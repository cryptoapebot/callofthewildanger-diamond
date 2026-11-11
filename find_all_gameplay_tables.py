import sqlite3
import os
import zlib
import struct

ARCHIVE_DIR = (
    "C:/Program Files (x86)/Steam/steamapps/common/"
    "Call of the Wild The Angler/archives_win64/initial"
)

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. List ALL files under settings/ or with .csvc / .json / .xml / .tunec / .blo_adf across the entire database!
cur.execute("""
SELECT DISTINCT n.v_path, p.p_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE '%settings/%'
   OR n.v_path LIKE '%.csvc%'
   OR n.v_path LIKE '%rank%'
   OR n.v_path LIKE '%score%'
   OR n.v_path LIKE '%trufish%'
   OR n.v_path LIKE '%fish%'
ORDER BY n.v_path
""")
rows = cur.fetchall()
print(f"=== Found {len(rows)} matching paths in core.db (showing non-texture/non-audio/non-ui) ===")
for vp, pp, off, sc, su in rows:
    if any(skip in vp for skip in ["ui/", "sound/", "textures/", "animations/", "meshes/", "models/", "materials/", "effects/"]):
        continue
    print(f"  {os.path.basename(pp):12s} | {vp:65s} | off={off} sc={sc} su={su}")

# 2. Also check what is inside worlds/achelous/locations/global_trufish.bl (off=63426560, sc=2021, su=2021 in game16.arc)!
arc16 = os.path.join(ARCHIVE_DIR, "game16.arc.bak")
if not os.path.exists(arc16):
    arc16 = os.path.join(ARCHIVE_DIR, "game16.arc")
with open(arc16, "rb") as f:
    f.seek(63426560)
    bl_raw = f.read(2021)
ewam = bl_raw.find(b"EWAM")
if ewam != -1:
    sarc = zlib.decompress(bl_raw[ewam+4:], -15)
    print(f"\n=== Unpacked worlds/achelous/locations/global_trufish.bl (len={len(sarc)}) ===")
    import re
    print("  Strings:", [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{4,}', sarc)])
    # Print the SARC directory entries (v_hash64 + offset + length)
    for o in range(0, min(256, len(sarc)), 8):
        q = struct.unpack_from("<q", sarc, o)[0]
        i0, i1 = struct.unpack_from("<II", sarc, o)
        print(f"  0x{o:02x}: int64={q:20d} (0x{q&0xffffffffffffffff:016x}) | u32=({i0}, {i1})")

conn.close()
