'''
This code is used to encode/decode PGN numbers from a CAN message
Translated from Bryant's Nmea2000.c file
'''

def Iso11783Decode(can_id):
    # Make sure we were passed an integer
    if type(can_id) != int:
        return (0, 0, 0, 0)

    # The source address is the lowest 8 bits
    src = can_id & 255

    # The priority are the highest 3 bits
    pri = (can_id >> 26) & 7

    # Most significant byte
    MS = (can_id >> 24) & 0x03

    # PDU format byte
    PF = (can_id >> 16) & 0xFF

    # PDU specific byte
    PS = (can_id >> 8) & 0xFF

    pgn = None
    if PF > 239:
        dest = 0xFF
        pgn = (MS << 16) | (PF << 8) | (PS)
    else:
        dest = PS
        pgn = (MS << 16) | (PF << 8)

    return (pgn, src, dest, pri)


def Iso11783Encode(pgn, src, dest, pri):
	can_id = 0

	# The source address is the lowest 8 bits
	can_id |= src

	# The priority is the highest 3 bits
	can_id |= (pri & 0x07) << 26;

	# Note that both the reserved bit and data page bit are left as 0 according to the protocol.

	# The following depends on if it's a PDU1 or PDU2 message. This can be determined
	# by the destination. 255 implies a global message with an extended PGN as PDU2, otherwise
	# it's PDU1.
	# For PDU2

	if pgn & 0xFF:
		can_id |= (pgn & 0x7FFFF) << 8

	# For PDU1
	else:
		can_id |= ((pgn & 0x7FF00) | dest) << 8

	return can_id


