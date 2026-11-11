import sqlite3
import zlib
import os
import re

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. Show all unique non-entity fish/gdcc/settings paths from our 277 mapped nodes
print("=== Non-.ee/.epe Fish, Settings, and GDCC Nodes ===")
cur.execute("""
SELECT n.node_id, n.parent_id, p.p_path, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
LEFT JOIN core_nodes p ON n.parent_id = p.node_id
WHERE (n.v_path LIKE '%gdcc%'
   OR n.v_path LIKE '%tru_fish%'
   OR n.v_path LIKE '%species%'
   OR n.v_path LIKE '%trophy%'
   OR n.v_path LIKE '%scoring%'
   OR n.v_path LIKE '%fish%')
  AND n.v_path NOT LIKE 'models/%'
  AND n.v_path NOT LIKE 'ui/%'
  AND n.v_path NOT LIKE 'animations/%'
  AND n.v_path NOT LIKE 'sounds/%'
ORDER BY n.v_path
""")
rows = cur.fetchall()
print(f"Found {len(rows)} gameplay/config nodes:")
for r in rows:
    if not r[3].endswith(".ee"): # Skip large .ee archives to keep output concise
        print(" ", r)

# 2. Dump all 218 ADF struct names and their member field names
print("\n=== All 218 Fish/Weight/Rank/Trophy ADF Structs ===")
with open("adf_fish_types.txt", "r", encoding="utf-8") as f:
    for line in f:
        # Only print structs that aren't statistics/save-game structs or material shaders
        if not any(skip in line for skip in ["StatisticsData", "Material", "TextureSlot", "VFX", "AnimationTrack"]):
            print(" ", line.strip()[:180])

# 3. Helper function to extract a node from its parent .arc file
def extract_node(node_id, out_filename):
    cur.execute("""
    SELECT n.parent_id, p.p_path, n.v_path, n.parent_offset, n.size_c, n.size_u
    FROM core_nodes n
    JOIN core_nodes p ON n.parent_id = p.node_id
    WHERE n.node_id = ?
    """, (node_id,))
    row = cur.fetchone()
    if not row:
        print(f"Node {node_id} not found!")
        return None
    parent_id, p_path, v_path, offset, size_c, size_u = row
    arc_path = p_path.replace(".tab", ".arc")
    
    # Check if blocks are in core_node_blocks
    cur.execute("""
    SELECT block_index, block_offset, block_length_compressed, block_length_uncompressed
    FROM core_node_blocks
    WHERE node_id = ?
    ORDER BY block_index
    """, (node_id,))
    blocks = cur.fetchall()
    
    data = bytearray()
    with open(arc_path, "rb") as af:
        if blocks:
            for b_idx, b_off, b_len_c, b_len_u in blocks:
                af.seek(b_off)
                chunk = af.read(b_len_c)
                if b_len_c == b_len_u:
                    data.extend(chunk)
                else:
                    try:
                        data.extend(zlib.decompress(chunk))
                    except Exception:
                        # Try raw deflate without header
                        data.extend(zlib.decompress(chunk, -15))
        else:
            af.seek(offset)
            chunk = af.read(size_c)
            if size_c == size_u:
                data.extend(chunk)
            else:
                try:
                    data.extend(zlib.decompress(chunk))
                except Exception:
                    data.extend(zlib.decompress(chunk, -15))
                    
    os.makedirs("extracted", exist_ok=True)
    out_path = os.path.join("extracted", out_filename)
    with open(out_path, "wb") as out_f:
        out_f.write(data)
    print(f"Extracted {v_path} ({len(data):,} bytes) -> {out_path}")
    return bytes(data)

# 4. Extract asp_01.epe_adf, asp_01.epe, global.gdcc, and a tru_fish tuning file
print("\n=== Extracting Sample Fish Configs ===")
for target_vpath, save_name in [
    ("editor/entities/fish/alpheus/asp_01.epe_adf", "asp_01.epe_adf"),
    ("editor/entities/fish/alpheus/asp_01.epe", "asp_01.epe"),
    ("gdc/global.gdcc", "global.gdcc"),
    ("settings/tru_fish/ceto/foodsources/trufish_ceto_foodsource_e.frtunec", "trufish_sample.frtunec")
]:
    cur.execute("SELECT node_id FROM core_nodes WHERE v_path = ? ORDER BY node_id DESC LIMIT 1", (target_vpath,))
    res = cur.fetchone()
    if res:
        raw = extract_node(res[0], save_name)
        if raw and len(raw) < 20000:
            # Print readable ASCII strings inside the extracted file!
            strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', raw)]
            print(f"  Strings inside {save_name} ({len(strs)}): {strs[:40]}")

conn.close()