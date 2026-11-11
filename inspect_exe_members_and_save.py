import os
import struct
import zlib
import re

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

# 1. Dump the ADF member table inside CotWTheAngler_Steam.exe starting at 0x2902cf0
fda_base = 0x2902cf0
print("=== 1. CTruFishSystemObjectData ADF Member Definitions in CotWTheAngler_Steam.exe ===")
# Let's print every 32-byte (0x20) block from +0x1e0 to +0x540
for rel in range(0x1e0, 0x540, 0x20):
    off = fda_base + rel
    vals = struct.unpack_from("<IIIIIIII", exe, off)
    f6 = struct.unpack_from("<f", exe, off + 24)[0]
    f7 = struct.unpack_from("<f", exe, off + 28)[0]
    i6 = struct.unpack_from("<i", exe, off + 24)[0]
    print(f"  +0x{rel:03x} (0x{off:x}): u32={vals[:6]} | def_int={i6:11d} (0x{vals[6]:08x}) | def_float={f6:10.4f}")

# 2. Inspect player_save_data (233,507 bytes)
save_p = r"C:\Users\greg\Saved Games\Avalanche Studios\CotWTheAngler\Saves\76561197980145518\player_save_data"
with open(save_p, "rb") as sf:
    sdata = sf.read()

print(f"\n=== 2. Inspecting player_save_data ({len(sdata)} bytes) ===")
print("  First 32 bytes:", sdata[:32])
# Check if it's compressed (EWAM / zlib / SARC / ADF)
for sig in [b"FDA", b"RTPC", b"EWAM", b"SARC", b"AVALANCHE"]:
    print(f"  Sig {sig.decode()} at:", sdata.find(sig))

# Try zlib decompressing from various offsets in player_save_data
unp = sdata
for off in range(0, min(128, len(sdata))):
    for wbits in (15, -15):
        try:
            dec = zlib.decompress(sdata[off:], wbits)
            if len(dec) > 1000:
                print(f"  [DECOMPRESSED player_save_data at offset {off} (wbits={wbits}): {len(dec)} bytes!]")
                unp = dec
                break
        except Exception:
            pass
    if unp is not sdata:
        break

strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./:-]{4,}', unp)]
interesting = [s for s in strs if any(k in s.lower() for k in ["fish", "rank", "pop", "spawn", "achelous", "bass", "diamond", "bronze", "trufish", "overfish"])]
print(f"  Interesting strings in player_save_data ({len(interesting)} total):", interesting[:80])
