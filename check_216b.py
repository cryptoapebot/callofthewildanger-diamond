import os
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

for base in (0x216bd60, 0x2902f50):
    print(f"\n=== Floats/Ints at 0x{base:x} in CotWTheAngler_Steam.exe ===")
    for o in range(base, base + 0x90, 4):
        vi = struct.unpack_from("<i", exe, o)[0]
        vu = struct.unpack_from("<I", exe, o)[0]
        vf = struct.unpack_from("<f", exe, o)[0]
        print(f"  0x{o:x}: int={vi:11d} (0x{vu:08x}) | float={vf:12.5f}")
