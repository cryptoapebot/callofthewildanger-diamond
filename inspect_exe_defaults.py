import os
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

fda_base = 0x2902cf0
print("=== 1. Remaining CTruFishSystemObjectData ADF Members (+0x240 .. +0x600) in CotWTheAngler_Steam.exe ===")
for rel in range(0x240, 0x600, 0x20):
    off = fda_base + rel
    u0 = struct.unpack_from("<I", exe, off)[0]
    i0 = struct.unpack_from("<i", exe, off)[0]
    f0 = struct.unpack_from("<f", exe, off)[0]
    m_idx = struct.unpack_from("<I", exe, off + 8)[0]
    s_off = struct.unpack_from("<i", exe, off + 24)[0]
    print(f"  +0x{rel:03x} (0x{off:x}): member={m_idx:2d} | struct_off=0x{s_off:02x} ({s_off:3d}) | default_int={i0:11d} (0x{u0:08x}) | default_float={f0:10.5f}")

# 2. Check if there are any OTHER copies of 0x3eae147b (0.34f) + 0x3f000000 (0.50f) in CotWTheAngler_Steam.exe!
sig = struct.pack("<I", 0x3eae147b)
pos = 0
hits = []
while True:
    idx = exe.find(sig, pos)
    if idx == -1:
        break
    hits.append(hex(idx))
    pos = idx + 1
print("\n=== 2. All occurrences of 0.34f (0x3eae147b) in CotWTheAngler_Steam.exe ===", hits)
