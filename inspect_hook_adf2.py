import os
import struct
import zlib
import sqlite3
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
    fda_hits = [m.start() for m in re.finditer(b" FDA", sarc)]
    print(f"\n=== {vpath} (SARC len={len(sarc)}, ' FDA' hits={[hex(x) for x in fda_hits]}) ===")
    if "hook_" in vpath and fda_hits:
        last_fda = fda_hits[-1]
        chunk = sarc[last_fda:]
        for o in range(0, len(chunk), 4):
            vi = struct.unpack_from("<I", chunk, o)[0]
            vf = struct.unpack_from("<f", chunk, o)[0]
            raw4 = chunk[o:o+4]
            asc = "".join(chr(b) if 32 <= b < 127 else "." for b in raw4)
            print(f"  +0x{o:03x} (0x{last_fda+o:05x}): 0x{vi:08x} | float={vf:10.4f} | '{asc}'")
    elif "asp_01.ee" in vpath:
        for h in fda_hits:
            # Check strings inside each ADF inside asp_01.ee
            end_h = fda_hits[fda_hits.index(h)+1] if fda_hits.index(h)+1 < len(fda_hits) else len(sarc)
            sub = sarc[h:min(end_h, h+8192)]
            strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{4,}', sub)]
            print(f"  ADF at 0x{h:x} (len {end_h - h}): {strs[:25]}")

conn.close()
