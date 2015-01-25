/*
 * Copyright Bryant Mairs 2015
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses.
 */


// Standard C libraries
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// Microchip libraries
#include <xc.h>
#include <pps.h>

// User libraries
#include "Uart1.h"
#include "Ecan1.h"
#include "EcanDefines.h"
#include "Canaconda.h"

// Specify the output baud rate
#define UART_BAUD 115200

// Set the operating frequency of the PIC
#define F_OSC 80000000l

// Hardware initialization routine.
static void Init(void);
static int MessageToHumanReadableString(char *s, size_t n, const CanMessage *m);
uint32_t Iso11783Decode(uint32_t can_id, uint8_t *src, uint8_t *dest, uint8_t *pri);

// Set processor configuration settings
#ifdef __dsPIC33FJ128MC802__
// Use internal RC to start; we then switch to PLL'd iRC.
_FOSCSEL(FNOSC_FRC & IESO_OFF);
// Clock Pragmas
_FOSC(FCKSM_CSECMD & OSCIOFNC_ON & POSCMD_NONE);
// Disable watchdog timer
_FWDT(FWDTEN_OFF);
// Disable JTAG and specify port 3 for ICD pins.
_FICD(JTAGEN_OFF & ICS_PGD3);
#elif __dsPIC33EP256MC502__
// Use internal RC to start; we then switch to PLL'd iRC.
_FOSCSEL(FNOSC_FRC & IESO_OFF);
// Clock Pragmas
_FOSC(FCKSM_CSECMD & OSCIOFNC_ON & POSCMD_NONE);
// Disable watchdog timer
_FWDT(FWDTEN_OFF);
// Disable JTAG and specify port 2 for ICD pins.
_FICD(JTAGEN_OFF & ICS_PGD2);
#else
#error No valid processor found!
#endif

int main()
{
    /// First step is to move over to the FRC w/ PLL clock from the default FRC clock.
    // Set the clock to 79.84MHz.
    PLLFBD = 63; // M = 65
    CLKDIVbits.PLLPOST = 0; // N1 = 2
    CLKDIVbits.PLLPRE = 1; // N2 = 3

    // Initiate Clock Switch to FRM oscillator with PLL.
    __builtin_write_OSCCONH(0x01);
    __builtin_write_OSCCONL(OSCCON | 0x01);

    // Wait for Clock switch to occur.
    while (OSCCONbits.COSC != 1);

    // And finally wait for the PLL to lock.
    while (OSCCONbits.LOCK != 1);

    // Initialize the UART
    Init();
    char initStr[] = "Initialization complete.\n";
    Uart1WriteData(initStr, sizeof(initStr) - 1);

    CanMessage rxMsg;
    char outStr[255];
    while (1) {
        // If we're active, listen for CAN messages and spit them out when they're found.
        if (Ecan1Receive(&rxMsg, NULL)) {
            // Turn on the yellow LED whenever a CAN message is received
            _LATA4 = 1;

            int bytesToSend;
            if ((bytesToSend = MessageToHumanReadableString(outStr, sizeof(outStr), &rxMsg))) {
                // Convert the terminating NUL-character to a newline for readability.
                outStr[bytesToSend - 1] = '\n';
                Uart1WriteData(outStr, bytesToSend);
            }
            _LATA4 = 0;
        }
    }
}

/**
 * Initializes all PIC functionality beyond the clock.
 *  * Maps all ECAN/UART pins
 *  * Assigns pins as input/output
 *  * Initializes the UART
 */
void Init(void)
{
    // And configure the Peripheral Pin Select pins:
    PPSUnLock;

#ifdef __dsPIC33FJ128MC802__
    // To enable ECAN1 pins: TX on 7, RX on 4
    PPSOutput(OUT_FN_PPS_C1TX, OUT_PIN_PPS_RP7);
    PPSInput(IN_FN_PPS_C1RX, IN_PIN_PPS_RP4);

    // To enable UART1 pins: TX on B11/P11, RX on B13/P13
    PPSOutput(OUT_FN_PPS_U1TX, OUT_PIN_PPS_RP11);
    PPSInput(IN_FN_PPS_U1RX, IN_PIN_PPS_RP13);
#elif __dsPIC33EP256MC502__
    // To enable ECAN1 pins: TX on 39, RX on 36
    PPSOutput(OUT_FN_PPS_C1TX, OUT_PIN_PPS_RP39);
    PPSInput(IN_FN_PPS_C1RX, IN_PIN_PPS_RP36);

    // To enable UART1 pins: TX on B11/P43, RX on B13/P45
    PPSOutput(OUT_FN_PPS_U1TX, OUT_PIN_PPS_RP43);
    PPSInput(IN_FN_PPS_U1RX, IN_PIN_PPS_RPI45);
#else
#error Invalid processor selected.
#endif

    PPSLock;

    // Initialize status LEDs for use.
    // A3 (output): Red LED, off by default.
    _TRISA3 = 0;
    _LATA3 = 0;
    // A4 (output): Amber LED, off by default.
    ANSELAbits.ANSA4 = 0;
    _TRISA4 = 0;
    _LATA4 = 0;

    _TRISB7 = 0; // Set ECAN1_TX pin to an output
    _TRISB4 = 1; // Set ECAN1_RX pin to an input;

    _TRISB11 = 0; // Set UART1_TX pin to an output
    _TRISB13 = 1; // Set UART1_RX pin to an input;

    // Set up UART1. There's no round() on the dsPICs, so we implement our own.
    double brg = (double) F_OSC / 2.0 / 16.0 / UART_BAUD - 1.0;
    if (brg - floor(brg) >= 0.5) {
        brg = ceil(brg);
    } else {
        brg = floor(brg);
    }
    Uart1Init((uint16_t)brg);
    
    // And set up ECAN1
    Ecan1Init(F_OSC, 250000);
}

/**
 * Converts the given CanMessage object into a human-readable string
 * @param s[out] The character array to write into. Will contain the string with terminating NUL-character
 * @param n The size of the output character array
 * @param m The message to stringify.
 * @return The number of character written into s, including the terminating NUL-character.
 */
static int MessageToHumanReadableString(char *s, size_t n, const CanMessage *m)
{
    // Write the message type, erroring out if bad data here.
    int charsWritten = 1;
    s[0] = '{';
    if (m->frame_type == CAN_FRAME_STD) {
        s[1] = 's';
        s[2] = 't';
        s[3] = 'd';
        s[4] = ',';
        charsWritten = 5;
    } else if (m->frame_type == CAN_FRAME_EXT) {
        s[1] = 'e';
        s[2] = 'x';
        s[3] = 't';
        s[4] = ',';
        charsWritten = 5;
    } else {
        return 0;
    }

    // Write out the identifier
    if (m->frame_type == CAN_FRAME_STD) {
        charsWritten += sprintf(&s[charsWritten], "%03X", (uint16_t)m->id);
        if (charsWritten <= 5) {
            return 0;
        }
    } else if (m->frame_type == CAN_FRAME_EXT) {
        charsWritten += sprintf(&s[charsWritten], "%08lX", m->id);
        if (charsWritten <= 5) {
            return 0;
        }

        // Also write out the PGN of this ID
        s[charsWritten++] = '(';
        uint32_t pgn = Iso11783Decode(m->id, NULL, NULL, NULL);
        charsWritten += sprintf(&s[charsWritten], "%lu", pgn);
        s[charsWritten++] = ')';
    } else {
        return 0;
    }

    // Write out the message length.
    if (m->validBytes > 8) {
        return 0;
    } else {
        s[charsWritten++] = ',';
        s[charsWritten++] = '0' + m->validBytes;
        s[charsWritten++] = ',';
    }

    // Now output the body of the message as hex characters, with 2 ASCII hex chars
    // per byte of payload.
    int i;
    s[charsWritten++] = '[';
    for (i = 0; i < m->validBytes; ++i) {
        ByteTo2Hex(&s[charsWritten], m->payload[i]);
        charsWritten += 2;
        if (i < m->validBytes - 1) {
            s[charsWritten++] = ',';
        }
    }
    s[charsWritten++] = ']';

    // End the message packet.
    s[charsWritten++] = '}';
    s[charsWritten++] = '\0';

    return charsWritten;
}

/**
  * Converts the 29-bit CAN extended address into its components according to the ISO 11783 spec.
  * @param[in] can_id The 29-bit CAN identifier to decode.
  * @param[out] src The source of this message.
  * @param[out] dest The destination for this message. Set to 255 if the message was a broadcast.
  * @param[out] pri The priority, a 3-bit number with higher values indicating higher priority.
  */
uint32_t Iso11783Decode(uint32_t can_id, uint8_t *src, uint8_t *dest, uint8_t *pri)
{

	// The source address is the lowest 8 bits
	if (src) {
		*src = (uint8_t)can_id;
	}

	// The priority are the highest 3 bits
	if (pri) {
		*pri = (uint8_t)((can_id >> 26) & 7);
	}

	// Most significant byte
	uint32_t MS = (can_id >> 24) & 0x03;

	// PDU format byte
	uint32_t PF = (can_id >> 16) & 0xFF;

	// PDU specific byte
	uint32_t PS = (can_id >> 8) & 0xFF;

	uint32_t pgn;
	if (PF > 239) {
		// PDU2 format, the destination is implied global and the PGN is extended.
		if (dest) {
			*dest = 0xFF;
		}
		pgn = (MS << 16) | (PF << 8) | (PS);
	} else {
		// PDU1 format, the PDU Specific field contains the destination address.
		if (dest) {
			*dest = PS;
		}
		pgn = (MS << 16) | (PF << 8);
	}

	return pgn;
}
