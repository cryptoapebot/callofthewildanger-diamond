import os
import re

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

def dump_context_strings(anchor_bytes, window=1500):
    pos = 0
    hits = 0
    while hits < 4:
        idx = exe.find(anchor_bytes, pos)
        if idx == -1:
            break
        chunk = exe[max(0, idx - window):min(len(exe), idx + window)]
        strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./:% -]{4,}', chunk)]
        print(f"\n=== Strings around {anchor_bytes.decode()} @ 0x{idx:x} ===")
        for s in strs:
            print(" ", s)
        pos = idx + len(anchor_bytes)
        hits += 1

dump_context_strings(b"new_diamond_spawns", 1200)
dump_context_strings(b"MAX_Score_%s", 1200)
dump_context_strings(b"rank_spawn_probability_diamond", 1000)

# Also check local save directories for Call of the Wild The Angler
print("\n=== Checking Save Game Directories ===")
for root_env in ["LOCALAPPDATA", "APPDATA", "USERPROFILE"]:
    base = os.environ.get(root_env, "")
    if not base:
        continue
    for sub in [
        "Avalanche Studios",
        "CallOfTheWildTheAngler",
        "Saved/SaveGames",
        "Documents/Avalanche Studios",
    ]:
        p = os.path.join(base, sub)
        if os.path.exists(p):
            print("Found dir:", p)
            for r, d, files in os.walk(p):
                for fn in files:
                    fp = os.path.join(r, fn)
                    print(f"  {fp} ({os.path.getsize(fp)} bytes)")
