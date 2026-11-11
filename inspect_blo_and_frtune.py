import os
import struct
import zlib
import re

# 1. Inspect the ADF at 0x1fd1c inside extracted/hook_01_ee_sarc.bin
with open("extracted/hook_01_ee_sarc.bin", "rb") as f:
    h01_sarc = f.read()

chunk_1fd1c = h01_sarc[0x1fd1c:0x2183c]
strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', chunk_1fd1c)]
print(f"=== Strings in hook_01_ee_sarc at 0x1fd1c (len={len(chunk_1fd1c)}) ===")
print(" ", strs)

# Also check if there is an RTPC inside hook_01_ee_sarc.bin!
rtpc_hits = [hex(m.start()) for m in re.finditer(b"RTPC", h01_sarc)]
print("RTPC hits in hook_01_ee_sarc.bin:", rtpc_hits)

# 2. Inspect asp_01.frtune at 0x1d2520 inside asp_01.ee
ARCHIVE_DIR = (
    "C:/Program Files (x86)/Steam/steamapps/common/"
    "Call of the Wild The Angler/archives_win64/initial"
)
with open(os.path.join(ARCHIVE_DIR, "game0.arc"), "rb") as af:
    af.seek(467034112)
    asp_ee = af.read(928797)
ewam = asp_ee.find(b"EWAM")
asp_sarc = zlib.decompress(asp_ee[ewam+4:], -15)
frtune = asp_sarc[0x1d2520:0x1d3a64]
f_strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', frtune)]
print(f"\n=== Strings in asp_01.frtune (len={len(frtune)}) ===")
print(" ", f_strs)

# Print all floats in asp_01.frtune between 0x40 and 0x350
print("\n=== Floats in asp_01.frtune ===")
for o in range(0x40, min(0x350, len(frtune)), 4):
    vf = struct.unpack_from("<f", frtune, o)[0]
    vi = struct.unpack_from("<I", frtune, o)[0]
    if 0.0001 <= abs(vf) <= 10000.0 or vi in (0, 1, 2, 3, 4, 5):
        print(f"  +0x{o:03x}: float={vf:10.4f} | int={vi} (0x{vi:08x})")

# 3. Inspect extracted/achelous_global_trufish.blo around 'TruFishReserveSettings'
with open("extracted/achelous_global_trufish.blo", "rb") as f:
    blo = f.read()
t_pos = blo.find(b"TruFishReserveSettings")
print(f"\n=== 'TruFishReserveSettings' in achelous_global_trufish.blo at 0x{t_pos:x} ===")
# Search for the 32-bit hashes of rank_spawn_probability_diamond, distribution_diamond, etc. in .blo!
import sqlite3
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
cur.execute("""
SELECT string, hash32 FROM core_strings
WHERE string IN (
    'rank_selection_method',
    'distribution_bronze', 'distribution_silver', 'distribution_gold', 'distribution_diamond',
    'rank_spawn_probability_juvenile', 'rank_spawn_probability_bronze', 'rank_spawn_probability_silver',
    'rank_spawn_probability_gold', 'rank_spawn_probability_diamond',
    'species_rank_cap_juvenile', 'species_rank_cap_bronze', 'species_rank_cap_silver',
    'species_rank_cap_gold', 'species_rank_cap_diamond'
)
""")
for s_name, h32 in cur.fetchall():
    b_h32 = struct.pack("<I", h32 & 0xFFFFFFFF)
    hits = [hex(m.start()) for m in re.finditer(re.escape(b_h32), blo)]
    vals_at_hits = []
    for h_hex in hits:
        h_off = int(h_hex, 16)
        # In RTPC, a property entry is (name_hash32, data_offset_or_val, type)
        u1, u2, u3 = struct.unpack_from("<III", blo, h_off)
        f2 = struct.unpack_from("<f", blo, h_off + 4)[0]
        vals_at_hits.append((h_hex, f"int={u2} (0x{u2:08x})", f"float={f2:.4f}", f"type={u3}"))
    print(f"  {s_name:35s} (0x{h32&0xFFFFFFFF:08x}): {vals_at_hits}")
conn.close()
