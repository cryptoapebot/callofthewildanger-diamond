import os
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

# 1. Find all CALLs (E8 disp32) to 0xad38c0, 0xad3ca0, 0xad3d60
targets = {
    0xad38c0: "EvalHabitatAndScore (0xad38c0)",
    0xad3ca0: "GetRankFromScore (0xad3ca0)",
    0xad3d60: "RollWeightAndScaleForRank (0xad3d60)",
}

print("=== 1. Direct CALLs to 0xad38c0, 0xad3ca0, 0xad3d60 ===")
for pos in range(0x1000, 0x1f40000):
    if exe[pos] == 0xE8:
        disp = struct.unpack_from("<i", exe, pos + 1)[0]
        dest = pos + 5 + disp
        if dest in targets:
            print(f"  CALL to {targets[dest]} from file=0x{pos:x} (RVA=0x{pos+0xc00:x})")

# 2. Search 0xac0000..0xaf0000 for SIB-indexed or direct accesses to +0xe8, +0x100, +0x118, +0x130
print("\n=== 2. Array base accesses (+0xe8, +0x100, +0x118, +0x130) in 0xac0000..0xaf0000 ===")
for pos in range(0xac0000, 0xaf0000):
    val = struct.unpack_from("<I", exe, pos)[0]
    if val in (0xe8, 0xec, 0x100, 0x110, 0x118, 0x128, 0x130):
        # Check if ModRM is at pos-1 (direct) or pos-2 (SIB with scale*4 = 0x80..0xbf)
        m1 = exe[pos-1]
        m2 = exe[pos-2]
        if ((m1 & 0xC0) == 0x80 and (m1 & 0x07) != 4) or ((m2 & 0xC0) == 0x80 and (m2 & 0x07) == 4):
            print(f"  0x{pos-3:x}: disp=+0x{val:x} bytes={exe[pos-4:pos+6].hex()}")
