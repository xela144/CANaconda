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

#ifndef PACKING_H
#define PACKING_H

/**
 * @file
 * This file declares various functions for packing different datatypes into uint8 arrays. Functions
 * for unpacking them are also included.
 */

#include <stdint.h>

/**
 * Define a union used for converting between the floating point types and their integer representation.
 * This allows for 'proper' bitwise operations.
 */
typedef union {
	float r32;
	uint32_t u32;
} conv_union;

__attribute__((always_inline)) static inline void LEPackUint16(uint8_t container[2], uint16_t data)
{
	container[0] = (uint8_t)data;
	container[1] = (uint8_t)(data >> 8);
}

__attribute__((always_inline)) static inline void LEPackInt16(uint8_t container[2], int16_t data)
{
	container[0] = (uint8_t)data;
	container[1] = (uint8_t)(data >> 8);
}

__attribute__((always_inline)) static inline void LEPackUint32(uint8_t container[4], uint32_t data)
{
	container[0] = (uint8_t)data;
	container[1] = (uint8_t)(data >> 8);
	container[2] = (uint8_t)(data >> 16);
	container[3] = (uint8_t)(data >> 24);
}

__attribute__((always_inline)) static inline void LEPackInt32(uint8_t container[4], int32_t data)
{
	container[0] = (uint8_t)data;
	container[1] = (uint8_t)(data >> 8);
	container[2] = (uint8_t)(data >> 16);
	container[3] = (uint8_t)(data >> 24);
}

__attribute__((always_inline)) static inline void LEPackReal32(uint8_t container[4], float data)
{
	conv_union tmp;
	tmp.r32 = data;
	container[0] = (uint8_t)tmp.u32;
	container[1] = (uint8_t)(tmp.u32 >> 8);
	container[2] = (uint8_t)(tmp.u32 >> 16);
	container[3] = (uint8_t)(tmp.u32 >> 24);
}

__attribute__((always_inline)) static inline void LEUnpackUint16(uint16_t *data, const uint8_t container[2])
{
	*data = (uint16_t)container[0] | ((uint16_t)container[1] << 8);
}

__attribute__((always_inline)) static inline void LEUnpackInt16(int16_t *data, const uint8_t container[2])
{
	*data = (int16_t)container[0] | ((int16_t)container[1] << 8);
}

__attribute__((always_inline)) static inline void LEUnpackInt32(int32_t *data, const uint8_t container[4])
{
	*data = (int32_t)container[0] | ((int32_t)container[1] << 8) | ((int32_t)container[2] << 16) |
	        ((int32_t)container[3] << 24);
}

__attribute__((always_inline)) static inline void LEUnpackUint32(uint32_t *data, const uint8_t container[4])
{
	*data = (uint32_t)container[0] | ((uint32_t)container[1] << 8) | ((uint32_t)container[2] << 16) |
	        ((uint32_t)container[3] << 24);
}

__attribute__((always_inline)) static inline void LEUnpackReal32(float *data, const uint8_t container[4])
{
	conv_union tmp;
	tmp.u32 = (uint32_t)container[0] | ((uint32_t)container[1] << 8) |
	               ((uint32_t)container[2] << 16) | ((uint32_t)container[3] << 24);
	*data = tmp.r32;
}

__attribute__((always_inline)) static inline void BEPackUint16(uint8_t container[2], uint16_t data)
{
	container[0] = (uint8_t)(data >> 8);
	container[1] = (uint8_t)data;
}

__attribute__((always_inline)) static inline void BEPackInt16(uint8_t container[2], int16_t data)
{
	container[0] = (uint8_t)(data >> 8);
	container[1] = (uint8_t)data;
}

__attribute__((always_inline)) static inline void BEPackUint32(uint8_t container[4], uint32_t data)
{
	container[0] = (uint8_t)(data >> 24);
	container[1] = (uint8_t)(data >> 16);
	container[2] = (uint8_t)(data >> 8);
	container[3] = (uint8_t)data;
}

__attribute__((always_inline)) static inline void BEPackInt32(uint8_t container[4], int32_t data)
{
	container[0] = (uint8_t)(data >> 24);
	container[1] = (uint8_t)(data >> 16);
	container[2] = (uint8_t)(data >> 8);
	container[3] = (uint8_t)data;
}

__attribute__((always_inline)) static inline void BEPackReal32(uint8_t container[4], float data)
{
	conv_union tmp;
	tmp.r32 = data;
	container[3] = (uint8_t)tmp.u32;
	container[2] = (uint8_t)(tmp.u32 >> 8);
	container[1] = (uint8_t)(tmp.u32 >> 16);
	container[0] = (uint8_t)(tmp.u32 >> 24);
}

__attribute__((always_inline)) static inline void BEUnpackUint16(uint16_t *data, const uint8_t container[2])
{
	*data = (uint16_t)container[1] | ((uint16_t)container[0] << 8);
}

__attribute__((always_inline)) static inline void BEUnpackInt16(int16_t *data, const uint8_t container[2])
{
        *data = (int16_t)container[1] | ((int16_t)container[0] << 8);
}

__attribute__((always_inline)) static inline void BEUnpackInt32(int32_t *data, const uint8_t container[4])
{
	*data = (int32_t)container[3] | ((int32_t)container[2] << 8) | ((int32_t)container[1] << 16) |
	        ((int32_t)container[0] << 24);
}

__attribute__((always_inline)) static inline void BEUnpackUint32(uint32_t *data, const uint8_t container[4])
{
	*data = (uint32_t)container[3] | ((uint32_t)container[2] << 8) | ((uint32_t)container[1] << 16) |
	        ((uint32_t)container[0] << 24);
}

__attribute__((always_inline)) static inline void BEUnpackReal32(float *data, const uint8_t container[4])
{
	conv_union tmp;
	tmp.u32 = (uint32_t)container[3] | ((uint32_t)container[2] << 8) |
	               ((uint32_t)container[1] << 16) | ((uint32_t)container[0] << 24);
	*data = tmp.r32;
}

#endif // PACKING_H
