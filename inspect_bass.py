import os
import sqlite3
import struct
import zlib
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

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. Find all files related to largemouth_bass_01 in core_nodes
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE '%largemouth_bass%' OR n.v_path LIKE '%basslarge%'
ORDER BY n.v_path
""")
rows = cur.fetchall()
print(f"=== Found {len(rows)} Largemouth Bass nodes ===")
for r in rows:
    print(" ", os.path.basename(r[1]), r[3], f"off={r[4]} sc={r[5]} su={r[6]}")

# 2. Inspect largemouth_bass_01.epe_adf and .epe
for r in rows:
    arc_n = os.path.basename(r[1]).replace(".tab", ".arc")
    vpath = r[3]
    if vpath.endswith(".epe_adf") and "achelous" in vpath:
        raw = read_orig(arc_n, r[4], r[5], r[6])
        strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', raw)]
        print(f"\n=== Strings in {vpath} (len={len(raw)}) ===")
        print(" ", strs)
        print("=== Floats in largemouth_bass_01.epe_adf ===")
        for o in range(0, len(raw) - 4, 4):
            vf = struct.unpack_from("<f", raw, o)[0]
            vi = struct.unpack_from("<i", raw, o)[0]
            if 0.01 <= abs(vf) <= 500.0:
                print(f"  0x{o:04x}: float={vf:10.4f} | int={vi}")

# 3. Also check what fish_codex_achelous.csvc has for BassLarge_01!
cur.execute("SELECT parent_offset, size_c, size_u FROM core_nodes WHERE v_path = 'settings/game_data_tables/fish_codex_achelous.csvc'")
c_off, c_sc, c_su = cur.fetchone()
codex_orig = read_orig("game12.arc", c_off, c_sc, c_su).decode("utf-8")
for line in codex_orig.splitlines():
    if "Fluid" in line or "ID," in line or "BassLarge" in line:
        print("\nCodex line:", line[:160])

# 4. Check if fish_codex_achelous.csvc is ALSO inside another archive (e.g. game0.arc or a .bl/.ee SARC)!
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE '%fish_codex%' OR n.v_path LIKE '%hook_meta_data%'
""")
print("\n=== All fish_codex and hook_meta_data nodes across all archives ===")
for r in cur.fetchall():
    print(" ", os.path.basename(r[1]), r[3], f"off={r[4]} sc={r[5]} su={r[6]}")

conn.close()
