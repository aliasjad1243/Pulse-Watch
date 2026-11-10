"""Heart rate and SpO2 from a PulseWatch capture, and comparison against a reference monitor.

    python hr_spo2.py ../data/trial01.csv            # one capture
    python hr_spo2.py --compare ../data/trials.csv   # watch vs. store-bought monitor

Heart rate: remove the slow baseline, find IR pulse peaks at least 0.33 s apart
(caps at 180 bpm), HR = 60 / median beat-to-beat time.

SpO2: ratio of ratios R = (AC/DC)red / (AC/DC)ir per beat, median over the window,
then SpO2 = a - b*R. a, b are fitted from paired readings against the reference
oximeter (fit_cal below); 110 and 25 are the usual textbook starting values.
"""
import argparse
import csv

import numpy as np

FS = 100.0  # Hz, set in firmware


def smooth(x, n):
    n = max(1, int(n))
    return np.convolve(np.pad(x, (n // 2, n - 1 - n // 2), mode="edge"), np.ones(n) / n, mode="valid")


def find_peaks(x, min_gap):
    lo, hi = np.percentile(x, [5, 95])
    thresh = lo + 0.3 * (hi - lo)
    cand = np.where((x[1:-1] > x[:-2]) & (x[1:-1] >= x[2:]) & (x[1:-1] > thresh))[0] + 1
    peaks = []
    for i in cand[np.argsort(x[cand])[::-1]]:          # tallest first, skip anything too close
        if all(abs(i - p) > min_gap for p in peaks):
            peaks.append(i)
    return np.array(sorted(peaks))


def analyse(red, ir, a=110.0, b=25.0, fs=FS):
    red, ir = np.asarray(red, float), np.asarray(ir, float)
    dc_r, dc_i = smooth(red, fs), smooth(ir, fs)          # 1 s moving average = DC
    ac_r, ac_i = red - dc_r, ir - dc_i
    peaks = find_peaks(smooth(ac_i, 0.1 * fs), int(0.33 * fs))
    if len(peaks) < 3:
        return float("nan"), float("nan"), float("nan")
    hr = 60.0 / (np.median(np.diff(peaks)) / fs)
    ratios = []
    for p, q in zip(peaks[:-1], peaks[1:]):
        r = (np.ptp(ac_r[p:q + 1]) / dc_r[p:q + 1].mean()) / (np.ptp(ac_i[p:q + 1]) / dc_i[p:q + 1].mean())
        ratios.append(r)
    R = float(np.median(ratios))
    return hr, min(100.0, a - b * R), R


def fit_cal(R, ref_spo2):
    slope, intercept = np.polyfit(R, ref_spo2, 1)
    return intercept, -slope


def read_rows(path):
    """CSV rows as dicts; lines starting with '#' are comments and skipped."""
    with open(path) as fh:
        return list(csv.DictReader(l for l in fh if not l.startswith("#")))


def compare(path, band_hr=2.0, band_spo2=2.0):
    """trials.csv: trial,watch_hr,ref_hr,watch_spo2,ref_spo2"""
    rows = [r for r in read_rows(path) if r["watch_hr"]]
    for name, w, r, band in (("HR", "watch_hr", "ref_hr", band_hr), ("SpO2", "watch_spo2", "ref_spo2", band_spo2)):
        d = np.array([float(x[w]) - float(x[r]) for x in rows])
        sd = d.std(ddof=1)
        print(f"{name}: n={len(d)}  bias={d.mean():+.2f}  limits of agreement "
              f"[{d.mean() - 1.96 * sd:+.2f}, {d.mean() + 1.96 * sd:+.2f}]  "
              f"max error {np.abs(d).max():.1f}  within ±{band:g}: {(np.abs(d) <= band).sum()}/{len(d)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--cal", nargs=2, type=float, default=(110.0, 25.0), metavar=("A", "B"))
    args = ap.parse_args()
    if args.compare:
        compare(args.path)
        return
    rows = read_rows(args.path)
    hr, spo2, R = analyse([int(r["red"]) for r in rows], [int(r["ir"]) for r in rows], *args.cal)
    print(f"HR {hr:.1f} bpm   SpO2 {spo2:.1f} %   R {R:.3f}")


if __name__ == "__main__":
    main()
