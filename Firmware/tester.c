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
#include <string.h>
#include <stdint.h>

// Microchip libraries
#include <xc.h>

// User libraries
#include "Canaconda.h"

// Set the operating frequency of the PIC
#define F_OSC 80000000l

// Function prototypes
void CommandTransmit(const void *data);

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

    uint8_t outs[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
                      0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 0x90, 0xA0, 0xB0, 0xC0, 0xD0, 0xE0, 0xF0,
                      0x93, 0xFF, 0xC1};
    char *ins[] = {"00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "0A", "0B", "0C", "0D", "0E", "0F",
                   "00", "10", "20", "30", "40", "50", "60", "70", "80", "90", "A0", "B0", "C0", "D0", "E0", "F0",
                   "93", "FF", "C1"};

    /// Test Hex2Byte():
    int inputs = sizeof(outs);
    int i;
    for (i = 0; i < inputs; ++i) {
        uint8_t output = HexToByte(ins[i]);
        if (output != outs[i]) {
            while (1);
        }
    }

    commandFunction[COMMAND_FUNCTION_INDEX_TRANSMIT] = CommandTransmit;

    {
        char *cmdt1 = "t4560\r";
        for (i = 0; i < strlen(cmdt1); ++i) {
            ProcessIncomingCommandStream(cmdt1[i]);
        }
        char *cmdt2 = "t11120123\r";
        for (i = 0; i < strlen(cmdt2); ++i) {
            ProcessIncomingCommandStream(cmdt2[i]);
        }
        char *cmdt3 = "t09080123456789ABCDEF\r";
        for (i = 0; i < strlen(cmdt3); ++i) {
            ProcessIncomingCommandStream(cmdt3[i]);
        }
    }

    {
        char *cmdt1 = "T456789120\r";
        for (i = 0; i < strlen(cmdt1); ++i) {
            ProcessIncomingCommandStream(cmdt1[i]);
        }
        char *cmdt2 = "T1112223325665\r";
        for (i = 0; i < strlen(cmdt2); ++i) {
            ProcessIncomingCommandStream(cmdt2[i]);
        }
        char *cmdt3 = "T090909098ABCDEF0123456789\r";
        for (i = 0; i < strlen(cmdt3); ++i) {
            ProcessIncomingCommandStream(cmdt3[i]);
        }
    }

    while (1);
}

void CommandTransmit(const void *data)
{
    CanMessage *msg = (CanMessage*)data;
}
