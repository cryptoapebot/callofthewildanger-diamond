import sqlite3
import json

# 1. Inspect an.json to see how DECA configures The Angler
with open(r".\_internal\resources\deca\gameinfo\an.json", "r", encoding="utf-8") as f:
    an_info = json.load(f)
print("=== an.json ===")
print(json.dumps(an_info, indent=2))

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 2. Find all fish, species, rank, trophy, and global.gdcc nodes in core_nodes
print("\n=== Searching core_nodes for Fish / Species / GDCC / Tuning files ===")
query = """
SELECT node_id, parent_id, v_hash, v_path, file_type, parent_offset, size_c, size_u
FROM core_nodes
WHERE v_path LIKE '%gdcc%'
   OR v_path LIKE '%species%'
   OR v_path LIKE '%tru_fish%'
   OR v_path LIKE '%editor/entities/fish/%'
   OR v_path LIKE '%trophy%'
   OR v_path LIKE '%rank%'
   OR v_path LIKE '%scoring%'
   OR v_path LIKE '%settings/%fish%'
ORDER BY v_path
"""
cur.execute(query)
rows = cur.fetchall()
print(f"Found {len(rows)} matching VFS nodes!")

with open("fish_nodes.txt", "w", encoding="utf-8") as out:
    for r in rows:
        out.write(f"{r}\n")

# Print first 40 matches to console
for r in rows[:40]:
    print(" ", r)

# 3. Search core_strings for any field names related to diamond, gold, weight, rank, score
print("\n=== Searching ADF Field Names in core_strings ===")
cur.execute("""
SELECT DISTINCT s.string, s.hash32
FROM core_strings s
JOIN core_string_references r ON s.rowid = r.string_rowid
WHERE r.is_adf_field_name = 1
  AND (s.string LIKE '%weight%' OR s.string LIKE '%rank%' OR s.string LIKE '%diamond%' 
       OR s.string LIKE '%trophy%' OR s.string LIKE '%score%' OR s.string LIKE '%rating%'
       OR s.string LIKE '%size%' OR s.string LIKE '%length%' OR s.string LIKE '%species%')
ORDER BY s.string
""")
fields = cur.fetchall()
print(f"Found {len(fields)} matching ADF field names:")
for fname, fhash in fields:
    print(f"  {fname} (0x{fhash & 0xFFFFFFFF:08x})")

# 4. Fix the DECA OverflowError crash in core.db!
# DECA crashes in process_file_type_find_no_name when v_path IS NULL and v_hash < 0.
# Giving unnamed negative-hash nodes a dummy v_path or file_type prevents process_file_type_find_no_name from crashing!
cur.execute("SELECT COUNT(*) FROM core_nodes WHERE file_type IS NULL AND v_hash < 0")
neg_count = cur.fetchone()[0]
print(f"\nNodes with NULL file_type and negative v_hash causing OverflowError: {neg_count}")

if neg_count > 0:
    print("Patching core_nodes so DECA skips negative uint64 hash crash...")
    cur.execute("""
    UPDATE core_nodes 
    SET v_path = printf('unknown/0x%016x', v_hash),
        file_type = 'unknown'
    WHERE file_type IS NULL AND v_hash < 0
    """)
    conn.commit()
    print("Patched! You can now open the project in deca_gui.exe without OverflowError!")

conn.close()