import os

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

print("=== 1. Hex dump of 0xad4280..0xad4ef0 ===")
for o in range(0xad4280, 0xad4ef0, 32):
    print(f"  0x{o:x}: {exe[o:o+32].hex()}")

print("\n=== 2. Hex dump of 0xad5690..0xad6120 ===")
for o in range(0xad5690, 0xad6120, 32):
    print(f"  0x{o:x}: {exe[o:o+32].hex()}")
