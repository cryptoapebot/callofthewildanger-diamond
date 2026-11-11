import struct
import os
import zlib

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

blo = read_orig("game16.arc", 63430656, 6916, 24240)
# Look at the 18th child entry in the RTPC object table!
# Earlier we saw 0x00a0..0x016c had 17 entries (each 12 bytes: count, offset, u16_pair).
# Wait: where was the 1st entry? Let's print all 12-byte object headers from 0x0098 to 0x0178!
print("=== All 18 RTPC Child Object Headers (0x0098 .. 0x0178) ===")
for i in range(18):
    off = 0x0098 + (i * 12)
    idx, data_off, np, nc = struct.unpack_from("<IIHH", blo, off)
    print(f"  Obj #{i:2d} (hdr @ 0x{off:04x}): id=0x{idx:08x} | data_off=0x{data_off:04x} ({data_off:5d}) | props={np:2d} | children={nc:2d}")
