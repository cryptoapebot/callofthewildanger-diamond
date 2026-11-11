import os
import sqlite3
import zlib
import struct
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

# 1. Print all hook paths in core_strings
cur.execute("""
SELECT string, hash32, hash64 FROM core_strings
WHERE (string LIKE '%hook%' AND string LIKE '%tune%')
   OR string LIKE '%tackle/hooks/%'
ORDER BY string
""")
print("=== All Hook Paths in core_strings ===")
for r in cur.fetchall():
    print(" ", r)

# 2. Extract hook_01.ee from game0.arc so we can see its SARC contents!
cur.execute("""
SELECT n.node_id, p.p_path, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE n.v_path LIKE 'editor/entities/equipment/tackle/hooks/hook_%.ee'
ORDER BY n.v_path
""")
hook_ees = cur.fetchall()
print(f"\nFound {len(hook_ees)} hook .ee archives in game0.tab:")
for r in hook_ees[:5]:
    print(" ", os.path.basename(r[1]), r[2], f"off={r[3]} sc={r[4]} su={r[5]}")

# Helper to decompress AAF / EWAM container
def unpack_aaf(raw_bytes, label):
    print(f"\n=== Unpacking AAF/EWAM: {label} ({len(raw_bytes):,} bytes) ===")
    pos = 0
    out_data = bytearray()
    while True:
        ewam = raw_bytes.find(b"EWAM", pos)
        if ewam == -1:
            break
        # Read header words around EWAM
        # Typically before EWAM: [size_c, size_u, ...] or after EWAM
        hdr_before = struct.unpack_from("<IIII", raw_bytes, ewam - 16)
        hdr_after = struct.unpack_from("<IIII", raw_bytes, ewam + 4)
        print(f"  EWAM at 0x{ewam:x}: before={hdr_before}, after={hdr_after}")
        # Try raw deflate (-15) at offsets ewam+4, ewam+8, ewam+12, ewam+16, ewam+20
        for try_off in range(ewam + 4, min(ewam + 64, len(raw_bytes))):
            try:
                d = zlib.decompress(raw_bytes[try_off:], -15)
                if len(d) > 100:
                    print(f"  -> Decompressed raw deflate at +0x{try_off - ewam:x}: {len(d):,} bytes!")
                    out_data.extend(d)
                    break
            except Exception:
                pass
        pos = ewam + 4
    if out_data:
        strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{4,}', out_data)]
        print(f"  Strings inside {label} ({len(strs)} total): {strs[:60]}")
    return bytes(out_data)

if hook_ees:
    r = hook_ees[0]
    h01_ee = read_orig("game0.arc", r[3], r[4], r[5])
    d_h01 = unpack_aaf(h01_ee, "hook_01.ee")
    if d_h01:
        with open("extracted/hook_01_ee_sarc.bin", "wb") as f:
            f.write(d_h01)

with open("extracted/global_fish.bl", "rb") as f:
    gf = f.read()
d_gf = unpack_aaf(gf, "global_fish.bl")
if d_gf:
    with open("extracted/global_fish_sarc.bin", "wb") as f:
        f.write(d_gf)

conn.close()
