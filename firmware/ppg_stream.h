/* ppg_stream.h
 * Streams raw MAX30102 red/IR samples at 100 Hz over the HC-05 (huart2).
 * Drop into open-watch's MyDrivers/ folder. See README for the 3 lines
 * that change in main.c.
 */
#ifndef PPG_STREAM_H
#define PPG_STREAM_H

#include <stdint.h>
#include <stddef.h>

#define PPG_FRAME_LEN 10   /* A5 5A seq red[3] ir[3] crc */

typedef struct {
    uint8_t  seq;
    uint32_t red;
    uint32_t ir;
} ppg_sample_t;

/* pure helpers (no HAL) so they can be checked on a PC */
uint8_t ppg_crc8(const uint8_t *data, size_t len);
void    ppg_encode(const ppg_sample_t *s, uint8_t out[PPG_FRAME_LEN]);

#ifndef PPG_HOST_TEST
#include "main.h"
#include "max30102_for_stm32_hal.h"

void ppg_start(max30102_t *dev, I2C_HandleTypeDef *hi2c);   /* replaces max30102_turn_on body */
void ppg_on_sample(uint32_t red, uint32_t ir);              /* call from max30102_plot()       */
void ppg_poll(UART_HandleTypeDef *huart);                   /* call once per main loop pass    */
#endif

#endif
