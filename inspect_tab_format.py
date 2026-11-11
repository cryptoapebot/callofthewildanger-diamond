import sqlite3
import struct
import os

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. Find where 'doris' stores its CTruFishSystemObjectData or trufish files
print("=== Searching for doris TruFish files ===")
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE p.p_path LIKE '%game32.tab%' OR p.p_path LIKE '%game33.tab%' OR p.p_path LIKE '%game34.tab%' OR p.p_path LIKE '%game35.tab%'
""")
rows = cur.fetchall()
for r in rows:
    if r[3] and any(k in r[3].lower() for k in ["trufish", "fish", "global"]):
        print(" ", r)

# 2. Inspect game12.tab binary layout around fish_codex_achelous.csvc
tab12_path = r"C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler/archives_win64/initial/game12.tab"
with open(tab12_path, "rb") as f:
    tab12 = f.read()

print(f"\ngame12.tab size: {len(tab12):,} bytes")
print(f"game12.tab header (first 32 bytes): {tab12[:32].hex(' ')}")

# Search for fish_codex_achelous.csvc v_hash (5775195222236934712 = 0x50259ba7bc75de38) or offset (594051072 = 0x23688000) in game12.tab
vh_bytes = struct.pack("<q", 5775195222236934712)
off_bytes = struct.pack("<I", 594051072)

vh_pos = tab12.find(vh_bytes)
off_pos = tab12.find(off_bytes)
print(f"v_hash found in game12.tab at: 0x{vh_pos:x}")
print(f"offset found in game12.tab at: 0x{off_pos:x}")
if vh_pos != -1:
    print(f"32 bytes at v_hash (0x{vh_pos:x}): {tab12[vh_pos:vh_pos+32].hex(' ')}")
    vals = struct.unpack_from("<qIIIII", tab12, vh_pos)
    print(f"Unpacked <qIIIII at v_hash: hash={vals[0]}, u1={vals[1]}, u2={vals[2]}, u3={vals[3]}, u4={vals[4]}, u5={vals[5]}")

# 3. Also check if fish_codex_achelous.csvc has blocks in core_node_blocks
cur.execute("SELECT * FROM core_node_blocks WHERE node_id IN (66136, 65068, 66151, 67392, 67190, 31401, 51788, 48612, 69968)")
print("\nBlocks in core_node_blocks for our target nodes:", cur.fetchall())

# 4. Check the first 16 bytes of raw compressed data in game12.arc at offset 594051072
arc12_path = tab12_path.replace(".tab", ".arc")
with open(arc12_path, "rb") as f:
    f.seek(594051072)
    raw_chunk = f.read(32)
print(f"First 32 bytes in game12.arc at 594051072: {raw_chunk.hex(' ')}")

conn.close()