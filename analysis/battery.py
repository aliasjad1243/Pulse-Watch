"""Battery numbers for the watch.

    python battery.py adc 1180                              # BAT_LVL reading -> volts, % charge
    python battery.py life 3.1 9.5 38                       # sleep, screen-on, streaming mA
    python battery.py log ../data/charge_discharge.csv      # columns: s,v_bat,i_ma

Divider on the Charger sheet: R8 330k (top) / R7 100k (bottom) into a 12-bit ADC at 3.3 V.
"""
import argparse
import csv

R_TOP, R_BOT, VREF, FULL = 330e3, 100e3, 3.3, 4095
CAPACITY_MAH = 400

# typical Li-Po resting voltage vs. state of charge
OCV = [(3.27, 0), (3.61, 5), (3.69, 10), (3.73, 20), (3.77, 30), (3.80, 40), (3.84, 50),
       (3.87, 60), (3.95, 70), (4.02, 80), (4.11, 90), (4.20, 100)]


def adc_to_volts(counts):
    return counts / FULL * VREF * (R_TOP + R_BOT) / R_BOT


def soc(v):
    if v <= OCV[0][0]:
        return 0.0
    if v >= OCV[-1][0]:
        return 100.0
    for (v0, s0), (v1, s1) in zip(OCV, OCV[1:]):
        if v0 <= v <= v1:
            return s0 + (s1 - s0) * (v - v0) / (v1 - v0)


def life_hours(sleep_ma, screen_ma, stream_ma, use=(0.90, 0.07, 0.03), usable=0.85):
    avg = sleep_ma * use[0] + screen_ma * use[1] + stream_ma * use[2]
    return avg, CAPACITY_MAH * usable / avg


def summarise_log(path):
    rows = list(csv.DictReader(open(path)))
    t = [float(r["s"]) for r in rows]
    v = [float(r["v_bat"]) for r in rows]
    i = [float(r["i_ma"]) for r in rows]
    mah = sum((i[k] + i[k - 1]) / 2 * (t[k] - t[k - 1]) / 3600 for k in range(1, len(t)))
    peak = max(range(len(v)), key=v.__getitem__)
    print(f"{len(rows)} points, {t[-1] / 3600:.2f} h, V {min(v):.3f}-{max(v):.3f} V "
          f"(peak at {t[peak] / 3600:.2f} h), net charge {mah:+.0f} mAh")
    # charger should stop at 4.2 V +/- 1 %: anything above 4.242 V is a problem
    print("charger cutoff OK" if max(v) <= 4.242 else "WARNING: battery went above 4.24 V")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("adc").add_argument("counts", type=float)
    lp = sub.add_parser("life")
    for name in ("sleep_ma", "screen_ma", "stream_ma"):
        lp.add_argument(name, type=float)
    sub.add_parser("log").add_argument("path")
    a = ap.parse_args()
    if a.cmd == "adc":
        v = adc_to_volts(a.counts)
        print(f"{v:.3f} V, about {soc(v):.0f} % (resting)")
    elif a.cmd == "life":
        avg, h = life_hours(a.sleep_ma, a.screen_ma, a.stream_ma)
        print(f"average {avg:.2f} mA -> {h:.0f} h ({h / 24:.1f} days)")
    else:
        summarise_log(a.path)


if __name__ == "__main__":
    main()
