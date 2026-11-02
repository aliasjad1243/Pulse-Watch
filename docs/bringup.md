# Board bring-up notes

Order I checked the board in, and what each check should read. Part numbers and
sheet names refer to `Watch.pdf` in the open-watch repo.

## Power path

```
USB 5 V ──┬──────────────── SUP
          │        P-MOSFET + SS34 (load sharing: USB runs the watch while charging)
          └─ TP4056 ── BAT ─┴─ DW01A + FS8205A protection ── 3.7 V Li-Po, 400 mAh
SUP ── LD3985 3.3 V LDO ── MCU, MAX30102, OLED, MPU6050, HC-05
BAT ── 330 k ── BAT_LVL (ADC) ── 100 k ── GND
```

| # | Check | Expect |
|---|---|---|
| 1 | USB only, no battery, bench supply limited to 200 mA | VBUS ≈ 5.0 V, 3.3 V rail 3.23–3.37 V |
| 2 | Battery fitted, USB pulled | SUP switches to BAT without the MCU resetting |
| 3 | TP4056 PROG resistor | 10 kΩ → 1200 V / 10 kΩ = 120 mA (0.3 C for 400 mAh) |
| 4 | Charging, CHRG/STDBY LEDs | CHRG on while charging, STDBY on at full; stops at 4.2 V ± 1 % |
| 5 | BAT_LVL divider | ratio 100k / 430k = 0.2326 → 4.2 V reads 0.977 V = 1212 counts |
| 6 | I²C idle, MCU running | SDA and SCL sit at 3.3 V (4.7 kΩ pull-ups) |
| 7 | I²C scan | 0x57 MAX30102, 0x68 MPU6050, 0x3C OLED |

The divider always draws 4.2 V / 430 kΩ ≈ 9.8 µA, and its 76.7 kΩ source
resistance needs the slowest ADC sample time (239.5 cycles) to settle.

## Current measurements

Meter in series with the battery, after the protection board. Readings feed
`analysis/battery.py life <sleep_mA> <screen_mA> <stream_mA>`:

- screen off, sensors off (sleep)
- screen on, idle watch face
- PPG streaming over Bluetooth (the HC-05 is the biggest load)

Battery life = 400 mAh × 0.85 usable ÷ time-weighted average current
(90 % sleep, 7 % screen, 3 % streaming by default).

## HC-05 setup (once)

The module defaults to 9600 baud (~960 B/s), but 100 frames/s × 10 bytes needs
1000 B/s, so:

1. Hold KEY/EN high at power-up (PIO11 is not wired to the MCU on this board) → AT mode at 38400 baud.
2. `AT+UART=115200,0,0`, then `AT+NAME=PulseWatch`.
3. Pair from the laptop (PIN 1234) and note the COM port.

The open-watch notes say BT RX/TX are swapped on the PCB, so check MCU TX → HC-05 RX
for continuity before powering.
