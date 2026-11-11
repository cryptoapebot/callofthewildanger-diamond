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
print("=== RTPC Header and Object Table (0x0000 .. 0x0190) of achelous_global_trufish.blo ===")
for off in range(0, 0x0190, 4):
    u32 = struct.unpack_from("<I", blo, off)[0]
    f32 = struct.unpack_from("<f", blo, off)[0]
    u16_0, u16_1 = struct.unpack_from("<HH", blo, off)
    print(f"  0x{off:04x}: 0x{u32:08x} (u16={u16_0:5d}, {u16_1:5d}) | float={f32:12.5f}")
