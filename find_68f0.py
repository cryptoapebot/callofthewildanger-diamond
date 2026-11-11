import os
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

for target_disp in (0x68f0, 0x62f0):
    print(f"=== References to +0x{target_disp:x} in .text ===")
    for pos in range(0xa00000, 0xb50000):
        val = struct.unpack_from("<I", exe, pos)[0]
        if val == target_disp:
            print(f"  0x{pos-3:x}: bytes={exe[pos-4:pos+6].hex()}")
