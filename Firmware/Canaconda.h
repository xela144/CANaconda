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

#ifndef CANACONDA_H
#define CANACONDA_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "EcanDefines.h"

// Specify the indices for each function pointer within the commandFunction[]
// array.
typedef enum {
    COMMAND_FUNCTION_INDEX_OPEN = 0,
    COMMAND_FUNCTION_INDEX_CLOSE,
    COMMAND_FUNCTION_INDEX_SETUP,
    COMMAND_FUNCTION_INDEX_TRANSMIT
} CommandFunctionIndices;

/**
 * Set this array with function pointers to be called when commands are executed.
 * The index of a functionc corresponds to the value of the CommandFunctionIndices
 * enum.
 */
extern void (*commandFunction[])(const void *);

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
int MessageToString(char *s, size_t n, const CanMessage *m);


/**
 * Converts the given integer to a 2-character ASCII hex (uppercase) value.
 * @param x The output character array.
 * @param d The input character.
 */
void ByteTo2Hex(char x[2], uint8_t d);

/**
 * Convert 2 characters to their byte value.
 * @param x An array of 2 characters, x[0] is the high-nibble, x[1] is the low-nibble.
 * @return The converted value or 0 if either character is invalid.
 */
uint8_t HexToByte(const char x[2]);

/**
 * Check if a given digit is a valid hexadecimal one.
 * @param c The character to convert
 * @return True if the input is a valid hexadecimal character.
 */
bool IsHexDigit(char c);

/**
 * Process all UART input to this board, decoding any commands an executing them
 * as they're found.
 * @param c The input ASCII character.
 * @return 0 if the input character didn't cause an error, -1 if it was, 1 if
 *         the input corresponded to a command and it was successfully acted on.
 */
int ProcessIncomingCommandStream(uint8_t c);

#endif // CANACONDA_H
