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
# 0x556c is where hash 0x1b368f6e (CTruFishSystemObject) is!
# In RTPC, the class hash is part of a 9-byte property: (prop_hash32, val32=0x1b368f6e, type=1)
# So the 9-byte alignment starts at 0x556c - 4 = 0x5568!
base = 0x5568
print("=== Walking 9-byte RTPC properties around CTruFishSystemObject (0x5568) in achelous .blo ===")
for step in range(-10, 45):
    off = base + (step * 9)
    if 0 <= off <= len(blo) - 9:
        h32, u32, t8 = struct.unpack_from("<IIB", blo, off)
        f32 = struct.unpack_from("<f", blo, off + 4)[0]
        i32 = struct.unpack_from("<i", blo, off + 4)[0]
        print(f"  {step:+3d} (0x{off:04x}): hash=0x{h32:08x} | int={i32:11d} (0x{u32:08x}) | float={f32:12.6f} | type={t8}")
