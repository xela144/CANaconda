#include "Uart1.h"

#include "CircularBuffer.h"

#include <xc.h>
#include <uart.h>

static CircularBuffer uart1RxBuffer;
static uint8_t u1RxBuf[UART1_BUFFER_SIZE];
static CircularBuffer uart1TxBuffer;
static uint8_t u1TxBuf[UART1_BUFFER_SIZE];

/*
 * Private functions.
 */
void Uart1StartTransmission(void);

/**
 * Initialization function for the UART1 peripheral. Should be called in initialization code for the
 * model. This function configures the UART for whatever baud rate is specified. It also configures
 * two circular buffers for transmission and reception.
 *
 * This function can be called again to re-initialize the UART. This clears all relevant registers
 * and reinitializes values to 0.
 */
void Uart1Init(uint16_t brgRegister)
{
    // First initialize the necessary circular buffers.
    CB_Init(&uart1RxBuffer, u1RxBuf, sizeof(u1RxBuf));
    CB_Init(&uart1TxBuffer, u1TxBuf, sizeof(u1TxBuf));

    // If the UART was already opened, close it first. This should also clear the transmit/receive
    // buffers so we won't have left-over data around when we re-initialize, if we are.
    CloseUART1();

    // Configure and open the port.
    OpenUART1(UART_EN & UART_IDLE_CON & UART_IrDA_DISABLE & UART_MODE_FLOW & UART_UEN_00 &
        UART_EN_WAKE & UART_DIS_LOOPBACK & UART_DIS_ABAUD & UART_NO_PAR_8BIT & UART_UXRX_IDLE_ONE &
        UART_BRGH_SIXTEEN & UART_1STOPBIT,
        UART_INT_TX_LAST_CH & UART_IrDA_POL_INV_ZERO & UART_SYNC_BREAK_DISABLED & UART_TX_ENABLE &
        UART_INT_RX_CHAR & UART_ADR_DETECT_DIS & UART_RX_OVERRUN_CLEAR,
        brgRegister
    );

    // Setup interrupts for proper UART communication. Enable both TX and RX interrupts at
    // priority level 6 (arbitrary).
    ConfigIntUART1(UART_RX_INT_EN & UART_RX_INT_PR6 & UART_TX_INT_EN & UART_TX_INT_PR6);
}

void Uart1ChangeBaudRate(uint16_t brgRegister)
{
    uint8_t utxen = U1STAbits.UTXEN;

    // Disable the port;
    U1MODEbits.UARTEN = 0;

    // Change the BRG register to set the new baud rate
    U1BRG = brgRegister;

    // Enable the port restoring the previous transmission settings
    U1MODEbits.UARTEN = 1;
    U1STAbits.UTXEN = utxen;
}

/**
 * This function actually initiates transmission. It
 * attempts to start transmission with the first element
 * in the queue if transmission isn't already proceeding.
 * Once transmission starts the interrupt handler will
 * keep things moving from there. The buffer is checked
 * for new data and the transmission buffer is checked that
 * it has room for new data before attempting to transmit.
 */
void Uart1StartTransmission(void)
{
    while (uart1TxBuffer.dataSize > 0 && !U1STAbits.UTXBF) {
        // A temporary variable is used here because writing directly into U1TXREG causes some weird issues.
        uint8_t c;
        IEC0bits.U1TXIE = 0;
        CB_ReadByte(&uart1TxBuffer, &c);
        IEC0bits.U1TXIE = 1;

        // We process the char before we try to send it in case writing directly into U1TXREG has
        // weird side effects.
        U1TXREG = c;
    }
}

int Uart1ReadByte(uint8_t *datum)
{
    IEC0bits.U1RXIE = 0;
    int rv = CB_ReadByte(&uart1RxBuffer, datum);
    IEC0bits.U1RXIE = 1;
    return rv;
}

/**
 * This function supplements the Uart1WriteData() function by also
 * providing an interface that only enqueues a single byte.
 */
void Uart1WriteByte(uint8_t datum)
{
    IEC0bits.U1TXIE = 0;
    CB_WriteByte(&uart1TxBuffer, datum);
    IEC0bits.U1TXIE = 1;
    Uart1StartTransmission();
}

/**
 * This function enqueues all bytes in the passed data character array according to the passed
 * length.
 */
int Uart1WriteData(const void *data, size_t length)
{
    IEC0bits.U1TXIE = 0;
    int success = CB_WriteMany(&uart1TxBuffer, data, length, true);
    IEC0bits.U1TXIE = 1;
    if (success) {
        Uart1StartTransmission();
    }

    return success;
}

void _ISR _U1RXInterrupt(void)
{
    // Make sure if there's an overflow error, then we clear it. While this destroys 5 bytes of data,
    // it's like the whole message these bytes are a part of is missing more bytes, and irrecoverably
    // corrupt, so we don't worry about it.
    if (U1STAbits.OERR == 1) {
        U1STAbits.OERR = 0;
    }

    // Keep receiving new bytes while the buffer has data.
    char c;
    while (U1STAbits.URXDA == 1) {
        // If there's a framing or parity error for the current UART byte, read the data but ignore
        // it. Only if there isn't an error do we actually add the value to our circular buffer.
        if (U1STAbits.FERR == 1 && U1STAbits.PERR) {
            c = U1RXREG;
        } else {
            c = U1RXREG;
            CB_WriteByte(&uart1RxBuffer, (uint8_t)c);
        }
    }

    // Clear the interrupt flag
    IFS0bits.U1RXIF = 0;
}

/**
 * This is the interrupt handler for UART1 transmission.
 * It is called after at least one byte is transmitted (
 * depends on UTXISEL<1:0> as to specifics). This function
 * therefore keeps adding bytes to transmit if there're more
 * in the queue.
 */
void _ISR _U1TXInterrupt(void)
{
    // Due to a bug with the dsPIC33E, this interrupt can trigger prematurely. We sit and poll the
    // TRMT bit to stall until the character is properly transmit.
    while (!U1STAbits.TRMT);

    while (uart1TxBuffer.dataSize > 0 && !U1STAbits.UTXBF) {
        // A temporary variable is used here because writing directly into U1TXREG causes some weird issues.
        uint8_t c;
        CB_ReadByte(&uart1TxBuffer, &c);

        // We process the char before we try to send it in case writing directly into U1TXREG has
        // weird side effects.
        U1TXREG = c;
    }

    // Clear the interrupt flag
    IFS0bits.U1TXIF = 0;
}
