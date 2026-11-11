import struct
import os
import zlib

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

adf = read_orig("game16.arc", 63438848, 5908, 15980)

# Dump the string table of achelous_global_trufish.blo_adf and find where CTruFishSystemObjectData is defined
import re
strs = [(m.start(), m.group(0).decode('latin1')) for m in re.finditer(b'[A-Za-z0-9_]{3,}', adf)]
print("=== Strings in achelous_global_trufish.blo_adf ===")
for off, s in strs:
    if any(k in s.lower() for k in ["trufish", "rank", "prob", "dist", "cap", "score", "fish", "spawn"]):
        print(f"  0x{off:04x}: {s}")

# Also check if doris (game32.arc) has ANY file with hash 0x5cb62388!
import sqlite3
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE p.p_path LIKE '%game32.tab%' AND n.v_path LIKE '%.blo'
""")
sig = struct.pack("<I", 0x5cb62388)
print("\n=== Scanning game32.arc (doris) .blo files for TruFish signature 0x5cb62388 ===")
for nid, ppath, vh, vpath, off, sc, su in cur.fetchall():
    try:
        raw = read_orig("game32.arc", off, sc, su)
        if sig in raw:
            print(f"  [FOUND!] {vpath} (node_id={nid}, v_hash={vh}, off={off}, sc={sc}, su={su})")
    except Exception:
        pass
conn.close()
