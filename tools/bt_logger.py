"""Record PPG frames from the watch over Bluetooth (HC-05 shows up as a COM port).

    python bt_logger.py COM5 --seconds 30 --out ../data/trial01

Writes trial01.csv (seq,red,ir). Frame format matches firmware/ppg_stream.c:
A5 5A | seq | red (3 bytes) | ir (3 bytes) | crc8
"""
import argparse
import csv
import time


def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def decode(buf):
    """Pull complete frames out of buf (a bytearray). Returns (samples, bad_crc)."""
    samples, bad = [], 0
    while True:
        i = buf.find(b"\xA5\x5A")
        if i < 0:
            del buf[:-1]
            return samples, bad
        del buf[:i]
        if len(buf) < 10:
            return samples, bad
        f = bytes(buf[:10])
        if crc8(f[2:9]) != f[9]:
            bad += 1
            del buf[:1]
            continue
        del buf[:10]
        samples.append((f[2], int.from_bytes(f[3:6], "big"), int.from_bytes(f[6:9], "big")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import serial  # pip install pyserial

    buf, rows, bad, dropped, last = bytearray(), 0, 0, 0, None
    with serial.Serial(args.port, args.baud, timeout=0.2) as port, open(args.out + ".csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["seq", "red", "ir"])
        end = time.time() + args.seconds
        while time.time() < end:
            buf.extend(port.read(512))
            samples, b = decode(buf)
            bad += b
            for seq, red, ir in samples:
                if last is not None:
                    dropped += (seq - last - 1) % 256
                last = seq
                w.writerow([seq, red, ir])
                rows += 1
    print(f"{rows} samples ({rows / args.seconds:.1f} Hz), dropped {dropped}, bad crc {bad}")


if __name__ == "__main__":
    main()
