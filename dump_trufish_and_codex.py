import sqlite3
import struct
import re

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. Find ALL nodes across all 36 .tab files that match fish_codex or global_trufish
print("=== All Archive Locations for fish_codex and global_trufish ===")
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE '%fish_codex%'
   OR n.v_path LIKE '%global_trufish%'
   OR n.v_path LIKE '%doris%fish%'
ORDER BY n.v_path, p.p_path
""")
for r in cur.fetchall():
    print(" ", r)

# 2. Check if there are multiple nodes sharing the same v_hash as fish_codex_achelous.csvc or global_trufish.blo_adf
# (In case only one node had v_path populated or multiple archives override the same v_hash!)
print("\n=== Checking All Overrides by v_hash ===")
cur.execute("""
SELECT s.string, n.node_id, p.p_path, n.v_hash, n.parent_offset, n.size_c, n.size_u
FROM core_strings s
JOIN core_nodes n ON n.v_hash = s.hash64
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE s.string LIKE 'settings/game_data_tables/fish_codex%'
   OR s.string LIKE '%global_trufish%'
ORDER BY s.string, p.p_path
""")
for r in cur.fetchall():
    print(" ", r)

# 3. Inspect the binary structure of extracted/achelous_global_trufish.blo_adf
print("\n=== Parsing extracted/achelous_global_trufish.blo_adf ===")
with open(r"extracted\achelous_global_trufish.blo_adf", "rb") as f:
    adf_data = f.read()

# Unpickle CTruFishSystemObjectData (0xfdbe7960) to get exact member offsets!
cur.execute("SELECT pickle FROM core_adf_types WHERE (type_hash & 0xFFFFFFFF) = ?", (0xfdbe7960,))
pblob = cur.fetchone()[0]

# Print raw hex/strings around member names in the pickle blob so we see exact byte offsets
print("Raw pickle bytes for CTruFishSystemObjectData (0xfdbe7960):")
for m in re.finditer(b'(rank_selection_method|distribution_[a-z]+|rank_spawn_probability_[a-z]+|species_rank_cap_[a-z]+)', pblob):
    start = m.start()
    snippet = pblob[start:start+60]
    print(f"  {m.group(0).decode('latin1'):35s} -> {snippet}")

# Search for TruFishReserveSettings in achelous_global_trufish.blo_adf and dump floats/ints around it
idx = adf_data.find(b"TruFishReserveSettings")
print(f"\n'TruFishReserveSettings' found at byte offset 0x{idx:x} in achelous_global_trufish.blo_adf")
# Dump the first 1024 bytes of the ADF instance data (offsets 0x00 to 0x400) as 32-bit floats and ints
print("\nScanning achelous_global_trufish.blo_adf for float probabilities (values between 0.001 and 100.0):")
for off in range(0, min(len(adf_data) - 4, 4096), 4):
    val_f = struct.unpack_from("<f", adf_data, off)[0]
    val_i = struct.unpack_from("<I", adf_data, off)[0]
    if 0.0001 <= val_f <= 1000.0 or val_i in (1, 2, 3, 4, 5, 10, 50, 100):
        # Print non-zero interesting rows
        print(f"  Offset 0x{off:04x}: float={val_f:12.5f} | int={val_i:10d} (0x{val_i:08x})")

# 4. Inspect extracted/fish_codex_achelous.csvc
print("\n=== Parsing extracted/fish_codex_achelous.csvc ===")
with open(r"extracted\fish_codex_achelous.csvc", "rb") as f:
    csvc_data = f.read()

print(f"fish_codex_achelous.csvc size: {len(csvc_data)} bytes, magic: {csvc_data[:16]}")
# Find where the string table starts in fish_codex_achelous.csvc
str_matches = list(re.finditer(b'[A-Za-z0-9_./ -]{4,}\x00', csvc_data))
print(f"First 30 null-terminated strings in fish_codex_achelous.csvc:")
for sm in str_matches[:30]:
    print(f"  0x{sm.start():04x}: {sm.group(0)[:-1].decode('latin1')}")

# Also dump the first 512 bytes of fish_codex_achelous.csvc in 4-byte chunks (ints/floats)
print("\nFirst 120 4-byte words of fish_codex_achelous.csvc:")
for off in range(0, min(480, len(csvc_data)), 4):
    vf = struct.unpack_from("<f", csvc_data, off)[0]
    vi = struct.unpack_from("<I", csvc_data, off)[0]
    f_str = f"{vf:10.4f}" if 0.0001 <= abs(vf) <= 100000.0 else "   -      "
    print(f"  0x{off:03x}: int={vi:10d} (0x{vi:08x}) | float={f_str}")

conn.close()