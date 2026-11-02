# PulseWatch

My contributions to **[open-watch](https://github.com/SMotlaq/open-watch)**, an open-source
STM32 smartwatch by Salman AmiMotlaq that measures heart rate, SpO₂ and motion.

I built the watch from the open-watch hardware and firmware, then changed the parts I needed
so it streams raw optical (PPG) data at 100 Hz over Bluetooth, and wrote the laptop-side
code to turn that data into heart rate and SpO₂ and check it against a store-bought monitor.
**This repo only holds the files I wrote or changed.** The schematics, PCB, enclosure and
the rest of the firmware live in the original project.

## The original project

| | |
|---|---|
| Repo | [SMotlaq/open-watch](https://github.com/SMotlaq/open-watch) (MIT) |
| MCU | STM32F030C8 (Cortex-M0), STM32 HAL, Keil |
| Sensors | MAX30102 pulse oximeter (I²C), MPU6050 |
| Other | 1.3" OLED, HC-05 Bluetooth, TP4056 charger, LD3985 3.3 V LDO, 400 mAh Li-Po |

## What I did

- **Board bring-up:** checked the TP4056 charger, 3.3 V LDO, load switch, battery-sense
  divider and I²C pull-ups with a multimeter before loading firmware → [`docs/bringup.md`](docs/bringup.md)
- **Driver fix:** the MAX30102 driver built the first channel's low byte from the wrong FIFO
  byte (`sample[3]` instead of `sample[2]`) and had red/IR labelled the wrong way round
  → [`firmware/max30102-fifo-fix.patch`](firmware/max30102-fifo-fix.patch)
- **100 Hz streaming:** set the sensor to 400 sps with 4× on-chip averaging, buffered samples
  from the interrupt, and sent them out the HC-05 as 10-byte frames with a sequence number
  and CRC → [`firmware/ppg_stream.c`](firmware/ppg_stream.c)
- **Logging:** Python logger that reads the Bluetooth COM port, checks CRCs and counts dropped
  frames → [`tools/bt_logger.py`](tools/bt_logger.py)
- **Heart rate / SpO₂:** peak detection for HR, ratio of ratios for SpO₂, and a comparison
  script for the 20 trials against a store-bought monitor → [`analysis/hr_spo2.py`](analysis/hr_spo2.py)
- **Battery:** divider math, state of charge from voltage, battery-life estimate from the
  measured currents, and a check of the charge/discharge log against the 4.2 V cutoff
  → [`analysis/battery.py`](analysis/battery.py)

## Files

```
firmware/
  ppg_stream.c / .h           100 Hz sampling + framed Bluetooth streaming
  max30102-fifo-fix.patch     fix to the upstream MAX30102 driver
tools/bt_logger.py            laptop-side logger (pyserial)
analysis/hr_spo2.py           HR + SpO2 from a capture; watch vs. reference comparison
analysis/battery.py           ADC -> volts / % charge, battery life, charge log check
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

Python needs `numpy` and `pyserial`.

## License

MIT, same as open-watch. The original copyright notice is kept in [`LICENSE`](LICENSE).
Not a medical device.
