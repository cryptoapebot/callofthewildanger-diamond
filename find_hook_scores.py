import os
import struct
import sqlite3
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

# 1. Read the 64-bit hook_tune_file hash at 0x00b0 from hook_01.epe_adf .. hook_20.epe_adf
cur.execute("""
SELECT v_path, parent_offset, size_c, size_u
FROM core_nodes
WHERE v_path LIKE 'editor/entities/equipment/tackle/hooks/hook_%.epe_adf'
ORDER BY v_path
""")
for vpath, off, sc, su in cur.fetchall():
    raw_adf = read_orig("game0.arc", off, sc, su)
    h64_signed = struct.unpack_from("<q", raw_adf, 0x00b0)[0]
    h64_hex = f"0x{h64_signed & 0xFFFFFFFFFFFFFFFF:016x}"
    cur.execute("""
    SELECT n.node_id, p.p_path, n.v_path, n.parent_offset, n.size_c, n.size_u
    FROM core_nodes n
    JOIN core_nodes p ON n.parent_id = p.node_id
    WHERE n.v_hash = ?
    """, (h64_signed,))
    matches = cur.fetchall()
    print(f"{os.path.basename(vpath):16s} -> tune_hash={h64_hex} -> core_nodes={matches}")
    if matches:
        m = matches[0]
        arc_n = os.path.basename(m[1]).replace(".tab", ".arc")
        t_raw = read_orig(arc_n, m[3], m[4], m[5])
        # TruScoreModifier is at +0x0c4 in HookStats ADF!
        ts_mod = struct.unpack_from("<f", t_raw, 0x0c4)[0]
        print(f"   TruScoreModifier at +0x0c4 = {ts_mod:.4f} (len={len(t_raw)})")

# 2. Check why hook_01.ee SARC had 0.0 at 0x21900 - let's check the SARC TOC of hook_01.ee vs hook_10.ee!
with open(os.path.join(ARCHIVE_DIR, "game0.arc.bak") if os.path.exists(os.path.join(ARCHIVE_DIR, "game0.arc.bak")) else os.path.join(ARCHIVE_DIR, "game0.arc"), "rb") as af:
    af.seek(416813056) # hook_01.ee
    h01_ee = af.read(24924)
    af.seek(417144832 if False else 417173504 - 28672) # let's get hook_10.ee from core.db

cur.execute("SELECT v_path, parent_offset, size_c, size_u FROM core_nodes WHERE v_path LIKE 'editor/entities/equipment/tackle/hooks/hook_%.ee' ORDER BY v_path")
for vp, off, sc, su in cur.fetchall()[:10]:
    raw_ee = read_orig("game0.arc", off, sc, su)
    ewam = raw_ee.find(b"EWAM")
    sarc = zlib.decompress(raw_ee[ewam+4:], -15)
    ts_val = struct.unpack_from("<f", sarc, 0x21900)[0]
    print(f"Inside {os.path.basename(vp):12s} SARC at 0x21900: TruScoreModifier = {ts_val:.4f}")

conn.close()
