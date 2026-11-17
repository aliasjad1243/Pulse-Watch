# PulseWatch

My contributions to **[open-watch](https://github.com/SMotlaq/open-watch)**, an open-source
STM32 smartwatch by Salman AmiMotlaq that measures heart rate, SpO₂ and motion.

I built the watch from the open-watch hardware and firmware, changed the firmware so it streams
raw optical (PPG) data at 100 Hz over Bluetooth, and wrote the laptop-side code that turns that
data into heart rate and SpO₂. **This repo only holds the files I wrote or changed.** The
schematics, PCB, enclosure and the rest of the firmware live in the original project.

## The original project

| | |
|---|---|
| Repo | [SMotlaq/open-watch](https://github.com/SMotlaq/open-watch) (MIT) |
| MCU | STM32F030C8 (Cortex-M0), STM32 HAL, Keil |
| Sensors | MAX30102 pulse oximeter (I²C), MPU6050 |
| Other | 1.3" OLED, HC-05 Bluetooth, TP4056 charger, LD3985 3.3 V LDO, 400 mAh Li-Po |

## My contributions (what I did → where to look)

1. **Board bring-up** of the STM32 wearable (MAX30102, OLED, Li-Po charger, Bluetooth module):
   power path and I²C checks with a multimeter before loading firmware
   → [`docs/bringup.md`](docs/bringup.md)
2. **Firmware: 100 Hz PPG over I²C, streamed over Bluetooth**
   - fixed the MAX30102 driver, which read the first channel's low byte from the wrong FIFO
     byte and had red/IR swapped → [`firmware/max30102-fifo-fix.patch`](firmware/max30102-fifo-fix.patch)
   - 400 samples/s with 4× on-chip averaging = 100 Hz; samples sent to the HC-05 as small
     frames with a sequence number (to spot drops) and a CRC (to spot corruption)
     → [`firmware/ppg_stream.c`](firmware/ppg_stream.c)
3. **Heart rate and SpO₂ in Python:** logger for the Bluetooth stream
   → [`tools/bt_logger.py`](tools/bt_logger.py), with pytest tests for good, corrupted, partial
   and dropped frames → [`tests/test_bt_logger.py`](tests/test_bt_logger.py); peak detection for heart rate, ratio of
   ratios for SpO₂, and a script that compares the watch to a store-bought monitor
   → [`analysis/hr_spo2.py`](analysis/hr_spo2.py), trial sheet [`data/trials.csv`](data/trials.csv)

## Files

```
firmware/
  ppg_stream.c / .h           100 Hz sampling + framed Bluetooth streaming
  max30102-fifo-fix.patch     fix to the upstream MAX30102 driver
tools/bt_logger.py            laptop-side logger (pyserial)
tests/test_bt_logger.py       pytest tests for the frame decoder
analysis/hr_spo2.py           HR + SpO2 from a capture; watch vs. reference comparison
docs/bringup.md               power path, bring-up checks, HC-05 setup
data/trials.csv               trial sheet (watch vs. reference)
```

## Using it with open-watch

1. Clone open-watch and apply the driver fix from its root:
   `git apply max30102-fifo-fix.patch`
2. Copy `ppg_stream.c/.h` into `MyDrivers/` and add them to the Keil project.
3. In `Src/main.c`:
   ```c
   void max30102_plot(uint32_t ir_sample, uint32_t red_sample){
       ppg_on_sample(red_sample, ir_sample);
   }
   void max30102_turn_on(void){
       ppg_start(&max30102, &hi2c1);
   }
   // inside while(1):
   ppg_poll(&BLUETOOTH_UART);
   ```
4. Set the HC-05 to 115200 baud (see `docs/bringup.md`), pair it, then:
   ```
   python tools/bt_logger.py COM5 --seconds 30 --out data/trial01
   python analysis/hr_spo2.py data/trial01.csv
   python analysis/hr_spo2.py --compare data/trials.csv
   ```

Python needs `numpy` and `pyserial`. Tests (no hardware needed): `pip install pytest`, then `pytest tests/`.


## License

MIT, same as open-watch. The original copyright notice is kept in [`LICENSE`](LICENSE).
Not a medical device.
