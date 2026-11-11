#  Data (PulseWatch)

## Files

- `capture.csv`: 30 s of red/IR samples at 100 Hz (`seq,red,ir`), same format `tools/bt_logger.py` writes
- `trials.csv`: 20 watch-vs-reference rows, same format as `data/trials.csv`

## Try it

```
python analysis/hr_spo2.py data/example/capture.csv
```

Output:

```
HR 74.1 bpm   SpO2 96.3 %   R 0.548
```

```
python analysis/hr_spo2.py --compare data/example/trials.csv
```

Output:

```
HR: n=20  bias=+0.24  limits of agreement [-1.65, +2.14]  max error 2.1  within ±2: 19/20
SpO2: n=20  bias=-0.40  limits of agreement [-1.80, +1.00]  max error 1.9  within ±2: 20/20
```
