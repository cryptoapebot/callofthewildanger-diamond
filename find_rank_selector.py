import os
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

print("=== 1. Hex dump of 0xad6120..0xad6810 ===")
for o in range(0xad6120, 0xad6810, 32):
    print(f"  0x{o:x}: {exe[o:o+32].hex()}")

print("\n=== 2. Searching .text (0xa00000..0xb50000) for references to offset +0x130 (rank_selection_method) or +0x118 (species_rank_cap) ===")
for pos in range(0xa00000, 0xb50000):
    val = struct.unpack_from("<I", exe, pos)[0]
    if val in (0x00000130, 0x00000118, 0x00000128):
        # check if preceded by common x86 opcode bytes (8b, 89, 83, 39, 3b, f3 0f 10, 48 8d, etc.)
        b1 = exe[pos-1]
        b2 = exe[pos-2]
        if (b1 & 0xC0) == 0x80 and b2 in (0x8b, 0x89, 0x83, 0x39, 0x3b, 0x8d, 0x10, 0x11, 0x58, 0x59, 0x5c, 0x5e, 0x2f, 0x63):
            print(f"  Hit +0x{val:x} @ file=0x{pos-2:x}: {exe[pos-4:pos+8].hex()}")
