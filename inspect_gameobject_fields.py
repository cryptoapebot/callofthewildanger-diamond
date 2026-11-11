import os
import struct
import zlib
import sqlite3
import re

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

# 1. Print ALL strings in the string table of achelous_global_trufish.blo_adf (0x36d0 to end)
adf = read_orig("game16.arc", 63438848, 5908, 15980)
print("=== All Reflection Strings in achelous_global_trufish.blo_adf (0x36d0..end) ===")
for m in re.finditer(b'[A-Za-z0-9_]{2,}', adf[0x36d0:]):
    print(f"  0x{0x36d0 + m.start():04x}: {m.group(0).decode('latin1')}")

# 2. Check nodes around offset 66351104 in game32.tab (doris global_trufish.blo and .blo_adf!)
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
cur.execute("""
SELECT n.node_id, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE p.p_path LIKE '%game32.tab%'
  AND n.parent_offset BETWEEN 66330000 AND 66370000
ORDER BY n.parent_offset
""")
print("\n=== Doris (game32.tab) nodes around offset 66,351,104 ===")
for r in cur.fetchall():
    print(" ", r)
conn.close()
