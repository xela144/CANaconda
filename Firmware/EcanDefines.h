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


// This file contains the constant definitions as well as the required
// data structures to work with on the ECAN module
#ifndef ECAN_DEFINES_H
#define ECAN_DEFINES_H

#include <stdint.h>

// Message Types either a data message or a remote transmit request
enum can_msg_type {
	CAN_MSG_DATA = 0,
	CAN_MSG_RTR
};

// CAN frame type: either extended (29-bit header) or standard (11-bit header)
enum can_frame_type {
	CAN_FRAME_EXT = 0,
	CAN_FRAME_STD
};

// Data structures
typedef struct {
	uint32_t id;           // The 11-bit or 29-bit message ID
	uint8_t  buffer;       // An internal-use variable referring to buffer this message was received into/sent from.
	uint8_t  message_type; // The message type. See can_msg_type.
	uint8_t  frame_type;   // The frame type. See can_frame_type.
	uint8_t  payload[8];   // The message payload. Stores between 0 and 8 bytes of data.
	uint8_t  validBytes;   // Indicates how many bytes are valid within payload.
} CanMessage;

typedef union {
	CanMessage message;
	uint8_t     bytes[sizeof(CanMessage)];
} CanUnion;

#endif /* ECAN_DEFINES_H */
