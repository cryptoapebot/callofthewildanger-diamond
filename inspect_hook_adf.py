import os
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

# 1. Inspect around 0x21800 to end of extracted/hook_01_ee_sarc.bin
with open("extracted/hook_01_ee_sarc.bin", "rb") as f:
    h01_sarc = f.read()

print(f"=== Tail of hook_01_ee_sarc.bin (total {len(h01_sarc)} bytes, 0x{len(h01_sarc):x}) ===")
start_dump = max(0, 0x21800)
tail = h01_sarc[start_dump:]
# Find 'FDA ' header in tail
fda_off = h01_sarc.rfind(b"FDA ")
print(f"Last 'FDA ' (ADF) header in hook_01_ee_sarc.bin is at: 0x{fda_off:x} (length {len(h01_sarc) - fda_off} bytes)")
if fda_off != -1:
    adf_chunk = h01_sarc[fda_off:]
    for off in range(0, len(adf_chunk), 4):
        vi = struct.unpack_from("<I", adf_chunk, off)[0]
        vf = struct.unpack_from("<f", adf_chunk, off)[0]
        raw4 = adf_chunk[off:off+4]
        ascii4 = "".join(chr(b) if 32 <= b < 127 else "." for b in raw4)
        print(f"  +0x{off:03x} (0x{fda_off+off:05x}): 0x{vi:08x} | float={vf:12.4f} | '{ascii4}'")

# 2. Also unpack hook_05.ee and hook_15.ee to compare their HookStats ADF chunk!
for h_name, h_off, h_sc in [
    ("hook_05.ee", 416960512, 24925),
    ("hook_15.ee", 417329152, 24925),
]:
    # Let's look up exact offset of hook_05.ee and hook_15.ee in core.db
    pass

import sqlite3
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
cur.execute("""
SELECT v_path, parent_offset, size_c, size_u
FROM core_nodes
WHERE v_path IN (
    'editor/entities/equipment/tackle/hooks/hook_01.ee',
    'editor/entities/equipment/tackle/hooks/hook_05.ee',
    'editor/entities/equipment/tackle/hooks/hook_10.ee',
    'editor/entities/equipment/tackle/hooks/hook_15.ee',
    'editor/entities/equipment/tackle/hooks/hook_20.ee',
    'editor/entities/fish/alpheus/asp_01.ee'
)
ORDER BY v_path
""")
for vpath, off, sc, su in cur.fetchall():
    raw_ee = read_orig("game0.arc", off, sc, su)
    ewam = raw_ee.find(b"EWAM")
    sarc = zlib.decompress(raw_ee[ewam+4:], -15)
    fda = sarc.rfind(b"FDA ")
    print(f"\n{vpath}: SARC size={len(sarc)}, last 'FDA ' at 0x{fda:x} (len={len(sarc)-fda})")
    if "hook_" in vpath and fda != -1:
        # Print the float at +0x40..+0x80 of the ADF chunk
        chunk = sarc[fda:]
        floats = [ (hex(o), struct.unpack_from("<f", chunk, o)[0]) for o in range(0x30, min(0x90, len(chunk)), 4) ]
        print("  Floats in ADF:", [(k, round(v, 4)) for k, v in floats if v != 0.0])
    elif "asp_01.ee" in vpath and fda != -1:
        chunk = sarc[fda:]
        strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', chunk)]
        print("  Strings in asp_01.ee last ADF:", strs[:40])

conn.close()
