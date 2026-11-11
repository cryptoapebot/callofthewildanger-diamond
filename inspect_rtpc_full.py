import os
import struct
import sqlite3
import zlib

with open("extracted/achelous_global_trufish.blo", "rb") as f:
    blo = f.read()

print("=== Walking 9-byte RTPC properties 0x00dc .. 0x01ce ===")
start_off = 0x01ce - (27 * 9)
for i in range(28):
    off = start_off + (i * 9)
    if off < 0:
        continue
    h32, u32, t8 = struct.unpack_from("<IIB", blo, off)
    f32 = struct.unpack_from("<f", blo, off + 4)[0]
    i32 = struct.unpack_from("<i", blo, off + 4)[0]
    print(f"  0x{off:04x}: hash=0x{h32:08x} | int={i32:11d} (0x{u32:08x}) | float={f32:12.6f} | type={t8}")

# Check all 16 occurrences of hash 0x5cb62388 in achelous_global_trufish.blo
sig = struct.pack("<I", 0x5cb62388)
pos = 0
hits = []
while True:
    idx = blo.find(sig, pos)
    if idx == -1:
        break
    hits.append(idx)
    pos = idx + 1

print(f"\nFound {len(hits)} TruFish objects with hash 0x5cb62388 in achelous_global_trufish.blo:")
for idx in hits[:3]:
    print(f"\n--- Object around 0x{idx:04x} ---")
    for step in range(-15, 10):
        o = idx + (step * 9)
        h32, u32, t8 = struct.unpack_from("<IIB", blo, o)
        f32 = struct.unpack_from("<f", blo, o + 4)[0]
        i32 = struct.unpack_from("<i", blo, o + 4)[0]
        if h32 != 0:
            print(f"  {step:+3d} (0x{o:04x}): hash=0x{h32:08x} | int={i32:11d} | float={f32:12.6f} | type={t8}")
