#include <stdio.h>
#include <stdlib.h>

#include "Canaconda.h"
#include "Ecan1.h"

// Set constants for every state used in the command decoder
typedef enum {
    COMMAND_PARSER_STATE_WAITING,

    // States for the Open command
    COMMAND_PARSER_STATE_OPEN, // Captured the 'O', waiting for '\r'

    // States for the Close command
    COMMAND_PARSER_STATE_CLOSE, // Captured the 'C', waiting for '\r'

    // States for the Setup command
    COMMAND_PARSER_STATE_SETUP, // Captured the 'S', waiting for '%1d'
    COMMAND_PARSER_STATE_SETUP2, // Captured the '%1d', waiting for '\r'

    // States for the transmit standard message command.
    COMMAND_PARSER_STATE_TRANSMITSTD_ID,

    // States for the transmit extended message command.
    COMMAND_PARSER_STATE_TRANSMITEXT_ID,
            
    // States shared between the transmit commands
    COMMAND_PARSER_STATE_TRANSMIT_LEN,
    COMMAND_PARSER_STATE_TRANSMIT_PAYLOAD,
    COMMAND_PARSER_STATE_TRANSMIT_CR,

} CommandParserState;

void (*commandFunction[])(const void *) = {
    NULL, // Open
    NULL, // Close
    NULL, // Setup
    NULL // Transmit
};

/**
 * Store a mapping between the baud rate arguments to the Setup command and the
 * actual baud rate values in baud.
 */
const uint32_t buadRates[] = {
    10000,
    20000,
    50000,
    100000,
    125000,
    250000,
    500000,
    800000,
    1000000
};

/**
 * Converts the given CanMessage to a complete string following the format:
 * Standard messages: tiiildd...
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
int MessageToString(char *s, size_t n, const CanMessage *m)
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
        ByteTo2Hex(&s[charsWritten], m->payload[i]);
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
void ByteTo2Hex(char x[2], uint8_t d)
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
 * Convert 2 characters to their byte value.
 * @param x An array of 2 characters, x[0] is the high-nibble, x[1] is the low-nibble.
 * @return The converted value or 0 if either character is invalid.
 */
uint8_t HexToByte(const char x[2])
{
    uint8_t rv;
    // First convert the lower nibble.
    if (x[1] >= 'A' && x[1] <= 'F') {
        rv = 10 + (x[1] - 'A');
    } else if (x[1] >= '0' && x[1] <= '9') {
        rv = x[1] - '0';
    } else if (x[1] >= 'a' && x[1] <= 'f') {
        rv = 10 + (x[1] - 'a');
    } else {
        return 0;
    }

    // Then OR in the upper nibble.
    if (x[0] >= 'A' && x[0] <= 'F') {
        rv |= (10 + (x[0] - 'A')) << 4;
    } else if (x[0] >= '0' && x[0] <= '9') {
        rv |= (x[0] - '0') << 4;
    } else if (x[0] >= 'a' && x[0] <= 'f') {
        rv |= (10 + (x[0] - 'a')) << 4;
    } else {
        return 0;
    }

    return rv;
}

bool IsHexDigit(char c)
{
    return ((c >= '0' && c <= '9') || (c >= 'A' && c <= 'F') || (c >= 'a' && c <= 'f'));
}

/**
 * Process all UART input to this board, decoding any commands an executing them
 * as they're found.
 * @param c The input ASCII character.
 * @return 0 if the input character didn't cause an error, -1 if it was, 1 if
 *         the input corresponded to a command and it was successfully acted on.
 */
int ProcessIncomingCommandStream(uint8_t c)
{
    static CommandParserState state = COMMAND_PARSER_STATE_WAITING;
    static uint32_t baudRate = 0; // The baud rate in baud
    static uint8_t loopCounter = 0; // A loop counter for reading in characters
    static char tmpData[16]; // An array to store input characters until they're decoded. The index being written to corresponds to loopCounter.
    static CanMessage msg;

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
        } else if (c == 't') {
            loopCounter = 0;
            msg.frame_type = CAN_FRAME_STD;
            state = COMMAND_PARSER_STATE_TRANSMITSTD_ID;
            return 0;
        } else if (c == 'T') {
            loopCounter = 0;
            msg.frame_type = CAN_FRAME_EXT;
            state = COMMAND_PARSER_STATE_TRANSMITEXT_ID;
            return 0;
        } else if (c == '\r') { // If an invalid command was specified, return an error.
            return -1;
        } else { // Otherwise ignore the input.
            return 0;
        }
        break;
    case COMMAND_PARSER_STATE_OPEN:
        if (c == '\r') {
            if (commandFunction[COMMAND_FUNCTION_INDEX_OPEN]) {
                (commandFunction[COMMAND_FUNCTION_INDEX_OPEN])(NULL);
            }
            state = COMMAND_PARSER_STATE_WAITING;
            return 1;
        } else {
            state = COMMAND_PARSER_STATE_WAITING;
            return -1;
        }
        break;
    case COMMAND_PARSER_STATE_CLOSE:
        if (c == '\r') {
            if (commandFunction[COMMAND_FUNCTION_INDEX_CLOSE]) {
                (commandFunction[COMMAND_FUNCTION_INDEX_CLOSE])(NULL);
            }
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
        if (c >= '0' && c <= '8') {
            int setupArg = c - '0';
            baudRate = buadRates[setupArg];
            state = COMMAND_PARSER_STATE_SETUP2;
            return 0;
        } else {
            state = COMMAND_PARSER_STATE_WAITING;
            return -1;
        }
        break;
    case COMMAND_PARSER_STATE_SETUP2:
        if (c == '\r') {
            if (commandFunction[COMMAND_FUNCTION_INDEX_SETUP]) {
                (commandFunction[COMMAND_FUNCTION_INDEX_SETUP])(&baudRate);
            }
            state = COMMAND_PARSER_STATE_WAITING;
            return 1;
        } else {
            state = COMMAND_PARSER_STATE_WAITING;
            return -1;
        }
        break;
    case COMMAND_PARSER_STATE_TRANSMITSTD_ID:
        if (IsHexDigit(c)) {
            tmpData[loopCounter] = c;
            ++loopCounter;
            if (loopCounter >= 3) {
                tmpData[loopCounter] = '\0';
                msg.id = (uint32_t)strtol(tmpData, 0, 16);
                state = COMMAND_PARSER_STATE_TRANSMIT_LEN;
            }
            return 0;
        }
        return -1;
    case COMMAND_PARSER_STATE_TRANSMITEXT_ID:
        if (IsHexDigit(c)) {
            tmpData[loopCounter] = c;
            ++loopCounter;
            if (loopCounter >= 8) {
                tmpData[loopCounter] = '\0';
                msg.id = (uint32_t)strtol(tmpData, 0, 16);
                state = COMMAND_PARSER_STATE_TRANSMIT_LEN;
            }
            return 0;
        }
        return -1;
    case COMMAND_PARSER_STATE_TRANSMIT_LEN:
        if (c >= '1' && c <= '8') {
            msg.validBytes = c - '0';
            loopCounter = 0;
            state = COMMAND_PARSER_STATE_TRANSMIT_PAYLOAD;
            return 0;
        } else if (c == '0') {
            msg.validBytes = 0;
            state = COMMAND_PARSER_STATE_TRANSMIT_CR;
            return 0;
        }
        return -1;
    case COMMAND_PARSER_STATE_TRANSMIT_PAYLOAD:
        if (IsHexDigit(c)) {
            tmpData[loopCounter] = c;
            ++loopCounter;
            if (loopCounter >= msg.validBytes * 2) {
                int i;
                for (i = 0; i < msg.validBytes; ++i) {
                    msg.payload[i] = HexToByte(&tmpData[i << 1]);
                }
                state = COMMAND_PARSER_STATE_TRANSMIT_CR;
            }
            return 0;
        }
        return -1;
    case COMMAND_PARSER_STATE_TRANSMIT_CR:
        if (c == '\r') {
            if (commandFunction[COMMAND_FUNCTION_INDEX_TRANSMIT]) {
                (commandFunction[COMMAND_FUNCTION_INDEX_TRANSMIT])(&msg);
            }
            state = COMMAND_PARSER_STATE_WAITING;
            return 1;
        } else {
            state = COMMAND_PARSER_STATE_WAITING;
            return -1;
        }
    default:
        state = COMMAND_PARSER_STATE_WAITING;
        return 0;
    }
}
