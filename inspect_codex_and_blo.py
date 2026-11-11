import sqlite3
import struct

conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()

# 1. Print the first 15 lines of extracted/fish_codex_achelous.csvc as plain text!
print("=== Plain-Text Contents of extracted/fish_codex_achelous.csvc ===")
with open(r"extracted\fish_codex_achelous.csvc", "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
print(f"Total lines in fish_codex_achelous.csvc: {len(lines)}")
for i, line in enumerate(lines[:10]):
    print(f"Line {i}: {line.strip()}")

# 2. Check if the float values 0.025 (0x3ccccccd) and 0.15 (0x3e19999a) also appear in achelous_global_trufish.blo!
print("\n=== Searching achelous_global_trufish.blo for 0.025 / 0.15 / 0.34 ===")
with open(r"extracted\achelous_global_trufish.blo", "rb") as f:
    blo_data = f.read()

target_bytes = [
    ("0.025 (prob_diamond)", struct.pack("<f", 0.025)),
    ("0.150 (prob_gold)", struct.pack("<f", 0.15)),
    ("0.340 (dist_diamond)", struct.pack("<f", 0.34)),
    ("18.00 (dist_bronze)", struct.pack("<f", 18.0)),
]
for label, b_pat in target_bytes:
    off = 0
    matches = []
    while True:
        idx = blo_data.find(b_pat, off)
        if idx == -1:
            break
        matches.append(hex(idx))
        off = idx + 1
    print(f"  {label:25s} found in .blo at offsets: {matches}")

# 3. Check ALL 36 .tab archives for any duplicate v_hash of our target files!
# (Earlier we joined on core_strings, now let's query core_nodes directly by v_hash)
print("\n=== Checking All 36 Archives for Any Newer Overrides of v_hash ===")
target_hashes = [
    5775195222236934712,  # fish_codex_achelous.csvc
    1641961905539253042,  # fish_codex_alpheus.csvc
    5796824274819009528,  # fish_codex_belisama.csvc
    -7827499170503240933, # fish_codex_ceto.csvc
    -8597476204515797250, # fish_codex_doris.csvc
    4245202897118090955,  # achelous global_trufish.blo_adf
    -3466259965272263087, # achelous global_trufish.blo
    -588015160189099245,  # alpheus global_trufish.blo_adf
    -6486124725201906287, # alpheus global_trufish.blo
    5612303823963747841,  # belisama global_trufish.blo_adf
    -3651693968069125943, # belisama global_trufish.blo
    -8655686045783063754, # ceto global_trufish.blo_adf
    -3753177674570790551, # ceto global_trufish.blo
]
for vh in target_hashes:
    cur.execute("""
    SELECT n.node_id, p.p_path, n.v_path, n.parent_offset, n.size_c, n.size_u
    FROM core_nodes n
    JOIN core_nodes p ON n.parent_id = p.node_id
    WHERE n.v_hash = ?
    ORDER BY n.node_id
    """, (vh,))
    rows = cur.fetchall()
    for r in rows:
        print(" ", r)

# 4. Also check what reserve 'doris' (Japan Reserve) uses for global_trufish
print("\n=== Checking 'doris' (Japan Reserve) trufish files ===")
cur.execute("""
SELECT n.node_id, p.p_path, n.v_hash, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE '%doris%' AND (n.v_path LIKE '%fish%' OR n.v_path LIKE '%global%')
ORDER BY n.v_path
""")
for r in cur.fetchall():
    print(" ", r)

conn.close()