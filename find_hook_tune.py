import sqlite3
import re
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

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. List ALL files under settings/ or tuning/ across all archives
print("=== All settings/ and tune files in core_nodes ===")
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE 'settings/%'
   OR n.v_path LIKE '%tune%'
   OR n.v_path LIKE '%hook%'
ORDER BY n.v_path
""")
for r in cur.fetchall():
    if not r[3].endswith(".ee") and not r[3].endswith(".ddsc") and not r[3].endswith(".modelc"):
        print(" ", os.path.basename(r[1]), r[3], f"off={r[4]} sc={r[5]} su={r[6]}")

# 2. Check all strings in core_strings that contain 'hook' or 'tune' or 'bite'
print("\n=== Strings in core_strings matching hook / tune / bite ===")
cur.execute("""
SELECT string, hash32, hash64 FROM core_strings
WHERE (string LIKE '%hook%' OR string LIKE '%tune%' OR string LIKE '%bite%' OR string LIKE '%truscore%')
  AND string NOT LIKE 'models/%'
  AND string NOT LIKE 'ui/%'
  AND string NOT LIKE 'animations/%'
LIMIT 60
""")
for r in cur.fetchall():
    print(" ", r)

conn.close()
