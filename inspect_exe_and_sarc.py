import os
import re
import struct
import zlib

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
ARCHIVE_DIR = os.path.join(GAME_DIR, "archives_win64/initial")

# 1. Inspect the unpacked 13,200 bytes of global_trufish.bl
arc16 = os.path.join(ARCHIVE_DIR, "game16.arc.bak")
if not os.path.exists(arc16):
    arc16 = os.path.join(ARCHIVE_DIR, "game16.arc")
with open(arc16, "rb") as f:
    f.seek(63422464)
    gt_bl = f.read(4231)

idx = gt_bl.find(b"EWAM")
for d in (4, 8, 12, 16):
    try:
        sarc = zlib.decompress(gt_bl[idx+d:], -15)
        if len(sarc) > 100:
            break
    except Exception:
        pass

print(f"=== 1. All strings in global_trufish.bl (len={len(sarc)}) ===")
print([s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./:-]{4,}', sarc)])

# 2. Find the game executable and search it for rank/diamond/codex/trufish strings!
exe_files = [os.path.join(GAME_DIR, f) for f in os.listdir(GAME_DIR) if f.lower().endswith(".exe")]
print("\n=== 2. Searching Game Executable:", exe_files, "===")
for exe_p in exe_files:
    with open(exe_p, "rb") as f:
        exe_bytes = f.read()
    for kw in [b"MAX_Score_", b"MAX_KG_", b"MAX_Scale_", b"fish_codex", b"hook_meta_data", b"rank_spawn_probability", b"distribution_diamond", b"species_rank_cap", b"FishDataByRank", b"RankSelectionMethod", b"juvenile", b"diamond"]:
        hits = []
        pos = 0
        while len(hits) < 10:
            i = exe_bytes.find(kw, pos)
            if i == -1:
                break
            # grab surrounding ascii string
            s_start = i
            while s_start > 0 and 32 <= exe_bytes[s_start-1] < 127:
                s_start -= 1
            s_end = i + len(kw)
            while s_end < len(exe_bytes) and 32 <= exe_bytes[s_end] < 127:
                s_end += 1
            hits.append(exe_bytes[s_start:s_end].decode('latin1', errors='ignore'))
            pos = s_end + 1
        print(f"  Keyword {kw.decode()}: {hits}")
