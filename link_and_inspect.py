import sqlite3
import pickle

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. Link core_strings.hash64 -> core_nodes.v_hash so v_path is populated!
print("=== Linking core_strings.hash64 to core_nodes.v_hash ===")
cur.execute("""
UPDATE core_nodes
SET v_path = (
    SELECT s.string 
    FROM core_strings s 
    WHERE s.hash64 = core_nodes.v_hash 
    LIMIT 1
)
WHERE v_hash IS NOT NULL AND EXISTS (
    SELECT 1 FROM core_strings s WHERE s.hash64 = core_nodes.v_hash
)
""")
conn.commit()

cur.execute("SELECT COUNT(*) FROM core_nodes WHERE v_path IS NOT NULL AND v_path NOT LIKE 'unknown/%'")
print(f"Nodes with real v_path mapped: {cur.fetchone()[0]}")

# 2. Now query the mapped fish / gdcc / tuning nodes along with their parent .arc file!
print("\n=== Mapped Fish / GDCC / Tuning Nodes in Archives ===")
cur.execute("""
SELECT n.node_id, n.parent_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
LEFT JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE '%gdcc%'
   OR n.v_path LIKE '%tru_fish%'
   OR n.v_path LIKE '%editor/entities/fish/%'
   OR n.v_path LIKE '%species%'
   OR n.v_path LIKE '%trophy%'
   OR n.v_path LIKE '%scoring%'
ORDER BY n.v_path
""")
nodes = cur.fetchall()
print(f"Found {len(nodes)} archive nodes!")
with open("mapped_fish_nodes.txt", "w", encoding="utf-8") as f:
    for row in nodes:
        f.write(f"{row}\n")

for row in nodes[:35]:
    print(" ", row)

# 3. Inspect core_adf_types by reading the raw pickle blobs for fish/weight/rank/diamond strings
print("\n=== Searching 2,965 ADF Struct Definitions in core_adf_types ===")
cur.execute("SELECT type_hash, pickle FROM core_adf_types")
adf_rows = cur.fetchall()

matched_types = []
for thash, pblob in adf_rows:
    # Search raw bytes of the pickle for ASCII strings inside the struct definition
    lower_blob = pblob.lower()
    if any(k in lower_blob for k in [b"fish", b"weight", b"rank", b"diamond", b"trophy", b"species", b"score", b"rating"]):
        # Extract readable ASCII strings from the pickle blob
        import re
        ascii_strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_]{3,}', pblob)]
        # Filter out standard pickle/deca module names
        clean_strs = [s for s in ascii_strs if s not in ("deca", "ff_adf", "TypeDef", "MemberDef", "EnumDef")]
        matched_types.append((thash & 0xFFFFFFFF, clean_strs))

print(f"Found {len(matched_types)} ADF struct/enum types related to fish/weight/rank/trophy:")
with open("adf_fish_types.txt", "w", encoding="utf-8") as f:
    for thash, strs in matched_types:
        line = f"Type 0x{thash:08x}: {strs}"
        f.write(line + "\n")

for thash, strs in matched_types[:30]:
    print(f"  Type 0x{thash:08x}: {strs[:15]}")

conn.close()
print("\nSaved full lists to mapped_fish_nodes.txt and adf_fish_types.txt!")