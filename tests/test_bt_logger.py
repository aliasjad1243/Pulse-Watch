"""Tests for the laptop-side frame decoder (tools/bt_logger.py).

    pip install pytest
    pytest tests/

The reference frame was produced by firmware/ppg_stream.c's ppg_encode()
for seq 7, red 74565 (0x012345), ir 144470 (0x023456).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from bt_logger import crc8, decode, frames_missed  # noqa: E402

GOOD = bytes.fromhex("A55A07012345023456F3")


def test_crc_matches_firmware():
    assert crc8(GOOD[2:9]) == 0xF3


def test_good_frame_decodes():
    buf = bytearray(GOOD)
    samples, bad = decode(buf)
    assert samples == [(7, 74565, 144470)]
    assert bad == 0
    assert buf == bytearray()          # frame consumed


def test_two_frames_back_to_back():
    samples, bad = decode(bytearray(GOOD + GOOD))
    assert len(samples) == 2 and bad == 0


def test_corrupted_byte_is_rejected():
    frame = bytearray(GOOD)
    frame[4] ^= 0x01                   # one bit flipped in the red value
    samples, bad = decode(frame)
    assert samples == []
    assert bad == 1


def test_bad_frame_does_not_hide_the_next_good_one():
    frame = bytearray(GOOD)
    frame[9] ^= 0xFF                   # wrong CRC byte
    samples, bad = decode(frame + bytearray(GOOD))
    assert samples == [(7, 74565, 144470)]
    assert bad == 1


def test_junk_before_marker_is_skipped():
    samples, bad = decode(bytearray(b"\x00\x13\xFF" + GOOD))
    assert samples == [(7, 74565, 144470)]
    assert bad == 0


def test_half_frame_waits_for_rest():
    buf = bytearray(GOOD[:6])
    samples, bad = decode(buf)
    assert samples == [] and bad == 0
    buf.extend(GOOD[6:])               # rest arrives in the next read
    samples, bad = decode(buf)
    assert samples == [(7, 74565, 144470)]


def test_no_marker_keeps_last_byte():
    buf = bytearray(b"\x01\x02\xA5")   # 0xA5 could be the start of a marker
    decode(buf)
    assert buf == bytearray(b"\xA5")


def test_frames_missed():
    assert frames_missed(5, 6) == 0     # consecutive
    assert frames_missed(5, 8) == 2     # 6 and 7 lost
    assert frames_missed(255, 0) == 0   # counter wrap is not a drop
    assert frames_missed(254, 1) == 2   # 255 and 0 lost across the wrap
