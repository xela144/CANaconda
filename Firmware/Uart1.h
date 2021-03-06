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

#ifndef UART1_H
#define UART1_H

// USAGE:
// Add Uart1Init() to an initialization sequence called once on startup.
// Use Uart1Write*Data() to push appropriately-sized data chunks into the queue and begin transmission.
// Use Uart1ReadByte() to read bytes out of the buffer

#include <stddef.h>
#include <stdint.h>

#define UART1_BUFFER_SIZE 1024

/**
 * Initializes the UART1 peripheral according to the BRG SFR value passed to it.
 * @param brgRegister The value to be placed in the BRG register.
 */
void Uart1Init(uint16_t brgRegister);

/**
 * Alters the baud rate of the UART1 peripheral to that dictated by brgRegister.
 * @param brgRegister The new baud rate.
 */
void Uart1ChangeBaudRate(uint16_t brgRegister);

/**
 * This function reads a byte out of the received data buffer for UART1.
 * @param datum The data received from the buffer. If no data was there it's unmodified.
 * @return A boolean value of whether valid data was returned.
 */
int Uart1ReadByte(uint8_t *datum);

/**
 * This function starts a transmission sequence after enqueuing a single byte into
 * the buffer.
 */
void Uart1WriteByte(uint8_t datum);

/**
 * This function augments the Uart1WriteByte() function by providing an interface
 * that enqueues multiple bytes.
 */
int Uart1WriteData(const void *data, size_t length);

#endif // UART1_H
