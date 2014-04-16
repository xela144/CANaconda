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

// Function prototypes for private functions
void _Init(void);
int _MessageToString(char *s, size_t n, const CanMessage *m);
void _ByteTo2Hex(char x[2], uint8_t d);
int _ProcessIncomingCommandStream(uint8_t c);

// Specify the output baud rate
#define UART_BAUD 57600

// Set the operating frequency of the PIC
#define F_OSC 80000000l

// Set constants for every state used in the command decoder
typedef enum {
    COMMAND_PARSER_STATE_WAITING,

    // States for the Open command
    COMMAND_PARSER_STATE_OPEN, // Captured the 'O', waiting for '\r'

    // States for the Close command
    COMMAND_PARSER_STATE_CLOSE, // Captured the 'C', waiting for '\r'

    // States for the Setup command
    COMMAND_PARSER_STATE_SETUP, // Captured the 'S', waiting for '%1d'
    COMMAND_PARSER_STATE_SETUP2 // Captured the '%1d', waiting for '\r'

} CommandParserState;

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
    _Init();

    CanMessage rxMsg;
    char outStr[30];
    while (1) {
        // If we're active, listen for CAN messages and spit them out when they're found.
        if (opMode == ACTIVE && Ecan1Receive(&rxMsg, NULL)) {
            int bytesToSend;
            if ((bytesToSend = _MessageToString(outStr, sizeof(outStr), &rxMsg))) {
                // We send 1 less than the output, because that last part is just
                // a NUL character.
                Uart1WriteData(outStr, bytesToSend - 1);
            }
        }

        // Regardless of run state, listen for incoming commands
        uint8_t u1RxData;
        if (Uart1ReadByte(&u1RxData)) {
            int commandResponse = _ProcessIncomingCommandStream(u1RxData);

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
void _Init(void)
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
}

/**
 * Converts the given CanMessage to a complete string following the format:
 * Standard messages: tiiiildd...
 * Extended messages: Tiiiiiiiildd...
 * Where:
 *   * t/T - Their respective characters (ASCII)
 *   * i... - The CAN identifier in upper-case hex (ASCII)
 *   * l - The length of the message payload in bytes (ASCII)
 *   * dd... - The payload of the messages, starting with byte 0. In uppercase hex ASCII character pairs.
 * @param s The character array to store the output in.
 * @param n The size of the character array.
 * @param m The message to stringify
 * @return The number of bytes written into `s`
 */
int _MessageToString(char *s, size_t n, const CanMessage *m)
{
    // Write the message type, erroring out if bad data here.
    int charsWritten = 1;
    if (m->frame_type == CAN_FRAME_STD) {
        s[0] = 't';
    } else if (m->frame_type == CAN_FRAME_EXT) {
        s[0] = 'T';
    } else {
        return 0;
    }

    // Write out the identifier
    if (m->frame_type == CAN_FRAME_STD) {
        charsWritten += sprintf(&s[charsWritten], "%03X", (uint16_t)m->id);
        if (charsWritten <= 1) {
            return 0;
        }
    } else {
        charsWritten += sprintf(&s[charsWritten], "%08lX", m->id);
        if (charsWritten <= 1) {
            return 0;
        }
    }

    // Write out the message length.
    if (m->validBytes > 8) {
        return 0;
    } else {
        s[charsWritten] = '0' + m->validBytes;
        ++charsWritten;
    }

    // Check that there's enough space for the rest of the string, otherwise error
    // out. We check once here instead of doing it repeatedly for every new byte written.
    // At this point we need to make sure we have 2 characters for every byte in the payload
    // along with 2 characters for the '\r' and '\0' at the end.
    if (n - charsWritten < m->validBytes * 2 + 2) {
        return 0;
    }

    // Now output the body of the message as hex characters, with 2 ASCII hex chars
    // per byte of payload.
    int i;
    for (i = 0; i < m->validBytes; ++i) {
        _ByteTo2Hex(&s[charsWritten], m->payload[i]);
        charsWritten += 2;
    }

    // Append the final carriage return and NUL character
    s[charsWritten++] = '\r';
    s[charsWritten++] = '\0';

    return charsWritten;
}

/**
 * Converts the given integer to a 2-character ASCII hex (uppercase) value.
 * @param x The output character array.
 * @param d The input character.
 */
void _ByteTo2Hex(char x[2], uint8_t d)
{
    uint8_t nibble = d & 0x0F;
    if (nibble < 10) {
        x[1] = '0' + nibble;
    } else {
        x[1] = 'A' + nibble - 10;
    }
    nibble = (d >> 4) & 0x0F;
    if (nibble < 10) {
        x[0] = '0' + nibble;
    } else {
        x[0] = 'A' + nibble - 10;
    }
}

/**
 * Process all UART input to this board, decoding any commands an executing them
 * as they're found.
 * @param c The input ASCII character.
 * @return 0 if the input character didn't cause an error, -1 if it was, 1 if
 *         the input corresponded to a command and it was successfully acted on.
 */
int _ProcessIncomingCommandStream(uint8_t c)
{
    static CommandParserState state = COMMAND_PARSER_STATE_WAITING;
    static uint8_t baudRate = 0; // The baud rate setting as an integer [0,8].

    switch (state) {
    case COMMAND_PARSER_STATE_WAITING:
        if (c == 'O') { // Open command
            state = COMMAND_PARSER_STATE_OPEN;
            return 0;
        } else if (c == 'C') { // Close command
            state = COMMAND_PARSER_STATE_CLOSE;
            return 0;
        } else if (c == 'S') { // Setup command
            state = COMMAND_PARSER_STATE_SETUP;
            return 0;
        } else if (c == '\r') { // If an invalid command was specified, return an error.
            return -1;
        } else { // Otherwise ignore the input.
            return 0;
        }
        break;
    case COMMAND_PARSER_STATE_OPEN:
        if (c == '\r' && opMode == CONFIGURED) {
            // Enable CAN if the Open command was received 'O\r' and the CAN
            // settings have been configured.
            opMode = ACTIVE;
            state = COMMAND_PARSER_STATE_WAITING;
            return 1;
        } else {
            state = COMMAND_PARSER_STATE_WAITING;
            return -1;
        }
        break;
    case COMMAND_PARSER_STATE_CLOSE:
        if (c == '\r' && opMode == ACTIVE) {
            // Disable CAN if the Close command was received 'C\r'.
            opMode = CONFIGURED;
            state = COMMAND_PARSER_STATE_WAITING;
            return 1;
        } else {
            state = COMMAND_PARSER_STATE_WAITING;
            return -1;
        }
        break;
    case COMMAND_PARSER_STATE_SETUP:
        // Check the validity of the setup argument. Also check that we aren't
        // in the active state, otherwise this command is invalid.
        if (c >= '0' && c <= '8' && opMode != ACTIVE) {
            baudRate = c - '0';
            state = COMMAND_PARSER_STATE_SETUP2;
            return 0;
        } else {
            state = COMMAND_PARSER_STATE_WAITING;
            return -1;
        }
        break;
    case COMMAND_PARSER_STATE_SETUP2:
        if (c == '\r' && opMode != ACTIVE) {
            // Enable the ECAN1 peripheral for CAN reception if a setup command is received.
            opMode = CONFIGURED;
            Ecan1Init(F_OSC);
            state = COMMAND_PARSER_STATE_WAITING;
            return 1;
        } else {
            state = COMMAND_PARSER_STATE_WAITING;
            return -1;
        }
        break;
    default:
        state = COMMAND_PARSER_STATE_WAITING;
        return 0;
        break;
    }
}