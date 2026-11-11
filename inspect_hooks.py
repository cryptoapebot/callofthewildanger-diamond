import os
import zlib
import sqlite3
import struct

ARCHIVE_DIR = (
    "C:/Program Files (x86)/Steam/steamapps/common/"
    "Call of the Wild The Angler/archives_win64/initial"
)

def read_orig(arc_name, offset, size_c, size_u):
    arc_p = os.path.join(ARCHIVE_DIR, arc_name)
    src = arc_p + ".bak" if os.path.exists(arc_p + ".bak") else arc_p
    with open(src, "rb") as f:
        f.seek(offset)
        chunk = f.read(size_c)
    if size_c == size_u:
        return chunk
    return zlib.decompress(chunk)

# 1. Extract and inspect fish_codex_bait_compatibility.csvc from game12.arc
raw_compat = read_orig("game12.arc", 594059264, 4089, 26579)
with open("extracted/fish_codex_bait_compatibility.csvc", "wb") as f:
    f.write(raw_compat)

lines = raw_compat.decode("utf-8", errors="replace").splitlines()
print(f"=== fish_codex_bait_compatibility.csvc ({len(lines)} lines) ===")
for i, l in enumerate(lines[:15]):
    print(f"Line {i}: {l}")

# 2. Check all hook / lure / bait files in core.db
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
print("\n=== Hook & Tackle Files in core_nodes ===")
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE '%hook%'
   OR n.v_path LIKE '%tackle%'
   OR n.v_path LIKE '%bait%'
ORDER BY n.v_path
""")
rows = cur.fetchall()
for r in rows[:45]:
    if not r[3].endswith(".ee"):
        print(" ", r)

# 3. Extract one hook .epe and .epe_adf to see how HookStats / TruScoreModifier / hook size work
for r in rows:
    if r[3] and "hook_01.epe" in r[3]:
        arc_name = os.path.basename(r[1]).replace(".tab", ".arc")
        h_raw = read_orig(arc_name, r[4], r[5], r[6])
        fname = os.path.basename(r[3])
        with open("extracted/" + fname, "wb") as f:
            f.write(h_raw)
        import re
        strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', h_raw)]
        print(f"\nStrings in {fname} ({len(h_raw)} bytes): {strs}")

conn.close()
