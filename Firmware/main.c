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
#define UART_BAUD 57600

// Set the operating frequency of the PIC
#define F_OSC 80000000l

// Hardware initialization routine.
static void Init(void);
void CommandOpen(const void *);
void CommandClose(const void *);
void CommandSetup(const void *);
void CommandTransmit(const void *d);

// Store the operating state
typedef enum {
    INACTIVE,
    CONFIGURED,
    ACTIVE
} RunState;
RunState opMode = INACTIVE; // True if the CAN hardware is enabled and receiving messages.

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

    CanMessage rxMsg;
    char outStr[30];
    while (1) {
        // If we're active, listen for CAN messages and spit them out when they're found.
        if (opMode == ACTIVE && Ecan1Receive(&rxMsg, NULL)) {
            // Turn on the yellow LED whenever a CAN message is received
            _LATA4 = 1;

            int bytesToSend;
            if ((bytesToSend = MessageToString(outStr, sizeof(outStr), &rxMsg))) {
                // We send 1 less than the output, because that last part is just
                // a NUL character.
                Uart1WriteData(outStr, bytesToSend - 1);
            }
            _LATA4 = 0;
        }

        // Regardless of run state, listen for incoming commands
        uint8_t u1RxData;
        if (Uart1ReadByte(&u1RxData)) {
            int commandResponse = ProcessIncomingCommandStream(u1RxData);

            // Output a CR if the command was successfully executed
            if (commandResponse > 0) {
                Uart1WriteByte('\r');
            }
            // Otherwise output a BEL if there was an error.
            else if (commandResponse < 0) {
                Uart1WriteByte('\b');
            }
            // The 0 value returned doesn't warrant an output as it's a command sequence in progress.
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
    // A4 (output): Amber LED, on by default.
    _TRISA4 = 0;
    _LATA4 = 1;

    _TRISB7 = 0; // Set ECAN1_TX pin to an output
    _TRISB4 = 1; // Set ECAN1_RX pin to an input;

    _TRISB11 = 0; // Set UART1_TX pin to an output
    _TRISB13 = 1; // Set UART1_RX pin to an input;

    // Set up UART1 for 57600 baud. There's no round() on the dsPICs, so we implement our own.
    double brg = (double) F_OSC / 2.0 / 16.0 / UART_BAUD - 1.0;
    if (brg - floor(brg) >= 0.5) {
        brg = ceil(brg);
    } else {
        brg = floor(brg);
    }
    Uart1Init((uint16_t)brg);

    // Initialize the Canaconda interface library callback functions
    commandFunction[COMMAND_FUNCTION_INDEX_OPEN] = CommandOpen;
    commandFunction[COMMAND_FUNCTION_INDEX_CLOSE] = CommandClose;
    commandFunction[COMMAND_FUNCTION_INDEX_SETUP] = CommandSetup;
    commandFunction[COMMAND_FUNCTION_INDEX_TRANSMIT] = CommandTransmit;
}

void CommandOpen(const void *d)
{
    if (opMode == CONFIGURED) {
        opMode = ACTIVE;
    }
}

void CommandClose(const void *d)
{
    if (opMode == ACTIVE) {
        opMode = CONFIGURED;
    }
}

void CommandSetup(const void *d)
{
    if (opMode != ACTIVE) {
        opMode = CONFIGURED;
        Ecan1Init(F_OSC);
    }
}

void CommandTransmit(const void *d)
{
    if (opMode == ACTIVE) {
        Ecan1Transmit((CanMessage*)d);
    }
}