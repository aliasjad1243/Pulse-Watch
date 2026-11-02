/* ppg_stream.c - 100 Hz PPG streaming for open-watch (STM32F030 + MAX30102 + HC-05)
 *
 * Why the changes from stock firmware:
 *  - stock config was 1000 sps with 8x averaging (125 Hz). I wanted an even
 *    100 Hz, so 400 sps with 4x averaging in the sensor.
 *  - stock code only buffered samples for the screen. Here every sample goes
 *    into a small ring buffer from the interrupt, and the main loop sends
 *    them out the Bluetooth UART as 10-byte frames.
 *  - each frame has a sequence number and CRC so the laptop side can tell
 *    when the radio dropped or mangled something.
 *
 * 100 frames/s * 10 bytes = 1000 B/s, which is more than the HC-05's default
 * 9600 baud can carry, so the module is set to 115200 (AT+UART=115200,0,0).
 */
#include "ppg_stream.h"

uint8_t ppg_crc8(const uint8_t *data, size_t len)
{
    uint8_t crc = 0;                       /* CRC-8, poly 0x07 */
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x07) : (uint8_t)(crc << 1);
    }
    return crc;
}

void ppg_encode(const ppg_sample_t *s, uint8_t out[PPG_FRAME_LEN])
{
    out[0] = 0xA5;
    out[1] = 0x5A;
    out[2] = s->seq;
    out[3] = (uint8_t)(s->red >> 16); out[4] = (uint8_t)(s->red >> 8); out[5] = (uint8_t)s->red;
    out[6] = (uint8_t)(s->ir  >> 16); out[7] = (uint8_t)(s->ir  >> 8); out[8] = (uint8_t)s->ir;
    out[9] = ppg_crc8(&out[2], 7);
}

#ifndef PPG_HOST_TEST

#define RING_SIZE 64   /* power of 2; ~640 ms of samples */

static ppg_sample_t ring[RING_SIZE];
static volatile uint16_t head, tail;
static uint8_t seq;
static uint8_t tx[PPG_FRAME_LEN * 4];

void ppg_start(max30102_t *dev, I2C_HandleTypeDef *hi2c)
{
    head = tail = 0;
    seq = 0;
    HAL_GPIO_WritePin(MAX_EN_GPIO_Port, MAX_EN_Pin, GPIO_PIN_SET);

    max30102_init(dev, hi2c);
    max30102_reset(dev);
    max30102_clear_fifo(dev);
    max30102_set_fifo_config(dev, max30102_smp_ave_4, 1, 15);   /* IRQ at 17 unread samples */
    max30102_set_sampling_rate(dev, max30102_sr_400);            /* 400 / 4 = 100 Hz out    */
    max30102_set_led_pulse_width(dev, max30102_pw_18_bit);
    max30102_set_adc_resolution(dev, max30102_adc_4096);
    max30102_set_led_current_1(dev, 6.2f);                       /* red */
    max30102_set_led_current_2(dev, 6.2f);                       /* IR  */
    max30102_set_mode(dev, max30102_spo2);
    max30102_set_a_full(dev, 1);
}

/* interrupt context (called by the driver for every FIFO sample) */
void ppg_on_sample(uint32_t red, uint32_t ir)
{
    if ((uint16_t)(head - tail) >= RING_SIZE)
        return;                            /* full: drop, the seq gap shows it on the PC */
    ring[head & (RING_SIZE - 1)] = (ppg_sample_t){ seq++, red, ir };
    head++;
}

void ppg_poll(UART_HandleTypeDef *huart)
{
    uint16_t n = 0;
    while (tail != head && n + PPG_FRAME_LEN <= (uint16_t)sizeof(tx)) {
        ppg_encode(&ring[tail & (RING_SIZE - 1)], &tx[n]);
        tail++;
        n += PPG_FRAME_LEN;
    }
    if (n)
        HAL_UART_Transmit(huart, tx, n, 20);   /* 40 B at 115200 baud is ~3.5 ms */
}

#endif
