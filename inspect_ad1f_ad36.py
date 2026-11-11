import os

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

print("=== Hex dump of 0xad1f00..0xad3600 ===")
for o in range(0xad1f00, 0xad3600, 32):
    print(f"  0x{o:x}: {exe[o:o+32].hex()}")
