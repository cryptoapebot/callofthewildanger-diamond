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
print("=== The 16 Root Properties of CTruFishSystemObject at 0x0014..0x00a4 in achelous .blo ===")
for i in range(16):
    off = 0x0014 + (i * 9)
    h32, u32, t8 = struct.unpack_from("<IIB", blo, off)
    f32 = struct.unpack_from("<f", blo, off + 4)[0]
    i32 = struct.unpack_from("<i", blo, off + 4)[0]
    extra = ""
    if t8 in (3, 5, 6, 8, 9, 13) and 0 < u32 < len(blo) - 16:
        vals = struct.unpack_from("<IIII", blo, u32)
        fvals = struct.unpack_from("<ffff", blo, u32)
        extra = f"-> @0x{u32:x}: ints={vals} floats=({fvals[0]:.4f},{fvals[1]:.4f},{fvals[2]:.4f},{fvals[3]:.4f})"
    print(f"  #{i:2d} (0x{off:04x}): hash=0x{h32:08x} | int={i32:11d} (0x{u32:08x}) | float={f32:12.5f} | type={t8:2d} {extra}")
