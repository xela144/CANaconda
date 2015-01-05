This folder contains code suitable for the CANode hardware for providing a canusb-compatible UART interface for interacting with the CAN bus. Only the C, O, and S commands are processed (with S not having any affect currently, but still being required). Only the t and T messages are output. This is no way to transmit CAN messages at this time.

There are 3 main() programs within this folder:
 * firmware.c - This implements a clone of the canusb (www.canusb.com) functionality, though transmission is not supported at this time.
 * tester.c - Used for unit testing. Designed to be run in debugging mode, as test failures result in infinite loops.
 * listener.c - An active CAN listener, so can be the only other node on a network. It decodes all CAN messages it receives and spits out human-readable text over UART.