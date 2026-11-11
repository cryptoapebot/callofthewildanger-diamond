import os
import struct
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

# 1. Inspect the 9-byte RTPC properties of "TruFishReserveSettings" in achelous_global_trufish.blo!
# Remember earlier: in achelous_global_trufish.blo, we saw 16 water bodies, and "TruFishReserveSettings" string is at 0x4e30!
# Let's find WHICH object in achelous_global_trufish.blo has 0.34 (0x3eae147b), 0.35 (0x3eb33333), 0.025 (0x3ccccccd), 18.0 (0x41900000)!
blo = read_orig("game16.arc", 63430656, 6916, 24240)
print(f"=== Scanning achelous_global_trufish.blo ({len(blo)} bytes) for CTruFishSystemObjectData floats ===")
for target_name, fval in [
    ("dist_bronze (18.0)", 18.0),
    ("dist_diamond (0.34)", 0.34),
    ("dist_gold (0.35)", 0.35),
    ("dist_silver (0.50)", 0.50),
    ("prob_diamond (0.025)", 0.025),
    ("prob_gold (0.15)", 0.15),
    ("prob_juvenile (0.20)", 0.20),
    ("prob_silver (0.45)", 0.45),
]:
    b_f = struct.pack("<f", fval)
    hits = [hex(i) for i in range(len(blo) - 4) if blo[i:i+4] == b_f]
    print(f"  {target_name:24s}: {hits}")

# 2. Dump the entire first object (0x0000 .. 0x0300) of achelous_global_trufish.blo and check where 0x4e30 ("TruFishReserveSettings") is referenced!
b_4e30 = struct.pack("<I", 0x4e30)
hits_4e30 = [hex(i) for i in range(len(blo) - 4) if blo[i:i+4] == b_4e30]
print(f"\nReferences to 0x4e30 ('TruFishReserveSettings') at any byte alignment in .blo: {hits_4e30}")

# 3. Dump 0x0500 .. 0x05d0 of achelous_global_trufish.blo_adf (where CTruFishSystemObjectData is!)
adf = read_orig("game16.arc", 63438848, 5908, 15980)
print("\n=== achelous_global_trufish.blo_adf (0x0500 .. 0x05c8) ===")
for o in range(0x0500, 0x05c8, 4):
    vi = struct.unpack_from("<i", adf, o)[0]
    vu = struct.unpack_from("<I", adf, o)[0]
    vf = struct.unpack_from("<f", adf, o)[0]
    print(f"  0x{o:04x}: int={vi:11d} (0x{vu:08x}) | float={vf:12.5f}")

# 4. Search core_nodes across ALL archives for any other file containing 'CTruFishSystemObjectData' or 'TruFishReserveSettings' (especially for doris!)
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE (p.p_path LIKE '%game32%' OR p.p_path LIKE '%game33%' OR p.p_path LIKE '%game34%')
  AND n.size_u BETWEEN 1000 AND 100000
""")
print("\n=== Scanning game32/33/34 for 'CTruFishSystemObject' or 'TruFishReserveSettings' ===")
for nid, ppath, vh, vp, off, sc, su in cur.fetchall():
    try:
        arc_n = os.path.basename(ppath).replace(".tab", ".arc")
        raw = read_orig(arc_n, off, sc, su)
        if b"TruFish" in raw or b"trufish" in raw:
            print(f"  [FOUND in {arc_n}] node={nid} v_hash={vh} v_path={vp} off={off} sc={sc} su={su}")
    except Exception:
        pass
conn.close()
