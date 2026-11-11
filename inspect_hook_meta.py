import os
import zlib
import sqlite3

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

# 1. Inspect hook_meta_data.csvc, jighead_meta_data.csvc, lure_meta_data.csvc
for fname, off, sc, su in [
    ("hook_meta_data.csvc", 594124800, 4140, 40678),
    ("jighead_meta_data.csvc", 594186240, 2886, 2886),
    ("lure_meta_data.csvc", 594198528, 1537, 20223),
]:
    raw = read_orig("game12.arc", off, sc, su)
    with open("extracted/" + fname, "wb") as f:
        f.write(raw)
    lines = raw.decode("utf-8", errors="replace").splitlines()
    print(f"\n=== {fname} ({len(lines)} lines) ===")
    for i, l in enumerate(lines[:8]):
        print(f"  Line {i}: {l[:160]}")

# 2. Check all .frtunec files in core_nodes (hooks, lures, fish)
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
print("\n=== Searching core_nodes for .frtunec files ===")
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE '%.frtunec%'
ORDER BY n.v_path
""")
rows = cur.fetchall()
print(f"Found {len(rows)} .frtunec files in core_nodes!")
for r in rows[:40]:
    print(" ", os.path.basename(r[1]), r[3], f"off={r[4]} sc={r[5]} su={r[6]}")

# Extract one hook .frtunec and one fish .frtunec to inspect their fields!
for r in rows:
    if "hook" in r[3] or "largemouth" in r[3] or "rainbow" in r[3]:
        arc_n = os.path.basename(r[1]).replace(".tab", ".arc")
        raw = read_orig(arc_n, r[4], r[5], r[6])
        out_n = os.path.basename(r[3])
        with open("extracted/" + out_n, "wb") as f:
            f.write(raw)
        import re
        strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', raw)]
        print(f"\nStrings in {r[3]} ({len(raw)} bytes): {strs[:40]}")

conn.close()
