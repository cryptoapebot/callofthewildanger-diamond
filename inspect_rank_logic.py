import sqlite3
import zlib
import os
import re

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. Print full member details for the key Rank / TruFish / Hook / Fish ADF types
target_hashes = [
    0xfdbe7960, # CTruFishSystemObjectData
    0xacb12cb5, # CTruFishSystemObjectData_RankSelectionMethod
    0x13f63413, # CTruFishGameObjectData
    0x45baf583, # STruFishAreaAllowedFishData
    0xbcbe2473, # STruFishAreaAllowedFishData
    0xd884c1df, # STrufishSpawnOverrideData_RankOverride
    0x001d9711, # STrufishSpawnOverrideData_RankOverrideMin
    0x23413a36, # STrufishSpawnOverrideData
    0x346ab14a, # CTruFishOverrideAreaData
    0xc2620736, # FishDefaults
    0xbff95523, # FishDataByRank
    0x75cbf130, # FishStats
    0xbd6296ff, # HookStats
    0x94c0bb64, # RankScalingVariable
]

print("=== Detailed ADF Type Definitions ===")
for th in target_hashes:
    # SQLite might store type_hash as signed or unsigned
    cur.execute("SELECT type_hash, pickle FROM core_adf_types WHERE (type_hash & 0xFFFFFFFF) = ?", (th,))
    for row_th, pblob in cur.fetchall():
        strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_]{2,}', pblob)]
        clean = [s for s in strs if s not in ("META_position", "metatype", "size", "alignment", "type_hash", "flags", "element_type_hash", "element_length", "members", "name_utf8", "offset", "deca", "ff_adf", "TypeDef", "bit_offset", "default", "comment")]
        print(f"\nType 0x{th:08x}:")
        print(" ", clean)

# 2. Check ALL archive versions of global.gdcc, global_trufish, fishsystem.bin, and fish_codex
print("\n=== Checking All Archive Versions of Key Fish Configs ===")
cur.execute("""
SELECT n.node_id, p.p_path, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path IN (
    'gdc/global.gdcc',
    'global/global_fish.bl',
    'global/global_fish.blo',
    'settings/fishsystem.bin',
    'settings/game_data_tables/fish_codex_achelous.csvc',
    'settings/game_data_tables/fish_codex_alpheus.csvc',
    'worlds/achelous/locations/global_trufish.blo',
    'worlds/achelous/locations/global_trufish.blo_adf',
    'worlds/alpheus/locations/global_trufish.blo_adf',
    'worlds/belisama/locations/global_trufish.blo_adf',
    'worlds/ceto/global/global_trufish.blo_adf'
)
   OR n.v_path LIKE '%doris%trufish%'
   OR n.v_path LIKE '%trufish%tune%'
ORDER BY n.v_path, p.p_path
""")
for r in cur.fetchall():
    print(" ", r)

# 3. Helper to extract any node
def extract_node(node_id, out_filename):
    cur.execute("""
    SELECT n.parent_id, p.p_path, n.v_path, n.parent_offset, n.size_c, n.size_u
    FROM core_nodes n
    JOIN core_nodes p ON n.parent_id = p.node_id
    WHERE n.node_id = ?
    """, (node_id,))
    row = cur.fetchone()
    if not row:
        return None
    parent_id, p_path, v_path, offset, size_c, size_u = row
    arc_path = p_path.replace(".tab", ".arc")
    cur.execute("""
    SELECT block_index, block_offset, block_length_compressed, block_length_uncompressed
    FROM core_node_blocks WHERE node_id = ? ORDER BY block_index
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
    print(f"\nExtracted {v_path} from {os.path.basename(arc_path)} (node {node_id}, {len(data):,} bytes) -> {out_path}")
    return bytes(data)

# 4. Extract and inspect strings in global_trufish.blo_adf, fish_codex_achelous.csvc, fishsystem.bin
for vpath, fname in [
    ("worlds/achelous/locations/global_trufish.blo_adf", "achelous_global_trufish.blo_adf"),
    ("worlds/achelous/locations/global_trufish.blo", "achelous_global_trufish.blo"),
    ("settings/game_data_tables/fish_codex_achelous.csvc", "fish_codex_achelous.csvc"),
    ("settings/fishsystem.bin", "fishsystem.bin"),
]:
    cur.execute("SELECT node_id FROM core_nodes WHERE v_path = ? ORDER BY node_id DESC LIMIT 1", (vpath,))
    res = cur.fetchone()
    if res:
        raw = extract_node(res[0], fname)
        if raw:
            strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', raw)]
            print(f"  Strings in {fname} ({len(strs)} total): {strs[:80]}")

# 5. Search extracted/global.gdcc for fish, rank, diamond, weight, trufish strings!
if os.path.exists("extracted/global.gdcc"):
    with open("extracted/global.gdcc", "rb") as f:
        gdcc_raw = f.read()
    gdcc_strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', gdcc_raw)]
    fish_gdcc = [s for s in gdcc_strs if any(k in s.lower() for k in ["fish", "rank", "diamond", "weight", "score", "trophy", "hook", "species", "spawn"])]
    print(f"\n=== Fish/Rank/Weight Strings inside global.gdcc ({len(fish_gdcc)} matches) ===")
    print(" ", fish_gdcc[:120])

conn.close()