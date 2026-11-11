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

# 1. Dump 0x0f80 to 0x1040 of original achelous_global_trufish.blo_adf
adf = read_orig("game16.arc", 63438848, 5908, 15980)
print("=== achelous_global_trufish.blo_adf (0x0f80 .. 0x1040) ===")
for off in range(0x0f80, min(0x1040, len(adf)), 4):
    vi = struct.unpack_from("<i", adf, off)[0]
    vu = struct.unpack_from("<I", adf, off)[0]
    vf = struct.unpack_from("<f", adf, off)[0]
    print(f"  0x{off:04x}: int={vi:11d} (0x{vu:08x}) | float={vf:12.5f}")

# 2. Dump 0x4f80 to 0x5080 of original achelous_global_trufish.blo
blo = read_orig("game16.arc", 63430656, 6916, 24240)
print("\n=== achelous_global_trufish.blo (0x4f80 .. 0x5080) ===")
for off in range(0x4f80, min(0x5080, len(blo)), 4):
    vi = struct.unpack_from("<i", blo, off)[0]
    vu = struct.unpack_from("<I", blo, off)[0]
    vf = struct.unpack_from("<f", blo, off)[0]
    print(f"  0x{off:04x}: int={vi:11d} (0x{vu:08x}) | float={vf:12.5f}")
