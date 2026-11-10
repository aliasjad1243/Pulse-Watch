# Example data (PulseWatch)

**⚠ Simulated data, not measurements.** Every file in this folder was generated from a simple model with random noise so you can try the analysis scripts and see what their output looks like. None of it was recorded from the device. Real results go in `data/` (outside this folder).

## Files

- `simulated_capture.csv`: 30 s of red/IR samples at 100 Hz (`seq,red,ir`), same format `tools/bt_logger.py` writes
- `simulated_trials.csv`: 20 watch-vs-reference rows, same format as `data/trials.csv`

## Try it

```
python analysis/hr_spo2.py data/example/simulated_capture.csv
```

Output:

```
HR 74.1 bpm   SpO2 96.3 %   R 0.548
```

```
python analysis/hr_spo2.py --compare data/example/simulated_trials.csv
```

Output:

```
HR: n=20  bias=+0.24  limits of agreement [-1.65, +2.14]  max error 2.1  within ±2: 19/20
SpO2: n=20  bias=-0.40  limits of agreement [-1.80, +1.00]  max error 1.9  within ±2: 20/20
```
