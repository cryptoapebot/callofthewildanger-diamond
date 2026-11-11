import os
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

# 1. Inspect the embedded ADF block around 0x290371c in CotWTheAngler_Steam.exe!
fda_pos = exe.rfind(b" FDA", 0, 0x290371c)
print(f"=== 1. Embedded ADF in CotWTheAngler_Steam.exe at 0x{fda_pos:x} (around 0x290371c) ===")
for off in range(fda_pos, fda_pos + 0x400, 4):
    vi = struct.unpack_from("<i", exe, off)[0]
    vu = struct.unpack_from("<I", exe, off)[0]
    vf = struct.unpack_from("<f", exe, off)[0]
    if 0.001 <= abs(vf) <= 2000.0 or vi == -1:
        print(f"  0x{off:x} (+0x{off-fda_pos:03x}): int={vi:11d} (0x{vu:08x}) | float={vf:12.5f}")

# 2. Check the Cache files in Documents/Avalanche Studios/CotWTheAngler/Cache
cache_dir = r"C:\Users\greg\Documents\Avalanche Studios\CotWTheAngler\Cache"
if os.path.exists(cache_dir):
    print("\n=== 2. Inspecting Cache Files ===")
    for fn in os.listdir(cache_dir):
        fp = os.path.join(cache_dir, fn)
        with open(fp, "rb") as cf:
            cdata = cf.read(256)
        print(f"  {fn} ({os.path.getsize(fp)} bytes): header={cdata[:32]}")

# 3. Check where the actual SaveGame folder is in C:\Users\greg\Saved Games or AppData
for cand in [
    r"C:\Users\greg\Saved Games",
    r"C:\Users\greg\AppData\Local",
    r"C:\Users\greg\AppData\Roaming",
]:
    if os.path.exists(cand):
        for d in os.listdir(cand):
            if any(k in d.lower() for k in ["angler", "avalanche", "expansive", "cotw", "call"]):
                full_d = os.path.join(cand, d)
                print("\n=== Found Save/AppData folder:", full_d, "===")
                for r, dirs, files in os.walk(full_d):
                    for fn in files:
                        fp = os.path.join(r, fn)
                        print(f"  {fp} ({os.path.getsize(fp)} bytes)")
