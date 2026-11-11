import os
import struct
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

# 1. Inspect the CTruFishSystemObjectData instance in all 4 .blo_adf files
tf_adfs = [
    ("game16.arc", "achelous", 63438848, 5908, 15980),
    ("game20.arc", "alpheus", 226926592, 4885, 14028),
    ("game24.arc", "belisama", 132120576, 4800, 11332),
    ("game28.arc", "ceto", 486465536, 6882, 18596),
]

for arc_n, lbl, off, sc, su in tf_adfs:
    adf = read_orig(arc_n, off, sc, su)
    # Search for the 0.15f (0x3e19999a) float inside the instance data (after 0x0800)
    b_015 = struct.pack("<f", 0.15)
    pos = adf.find(b_015, 0x0800)
    print(f"\n=== {lbl} .blo_adf around 0.15f at 0x{pos:x} ===")
    if pos != -1:
        start = pos - 16
        for o in range(start, start + 96, 4):
            vi = struct.unpack_from("<i", adf, o)[0]
            vu = struct.unpack_from("<I", adf, o)[0]
            vf = struct.unpack_from("<f", adf, o)[0]
            print(f"  +0x{o-start:02x} (0x{o:04x}): int={vi:11d} (0x{vu:08x}) | float={vf:12.5f}")

# 2. Inspect 0x0170..0x02d0 in achelous_global_trufish.blo (where 0.000332, 0.002, 0.15 live!)
blo = read_orig("game16.arc", 63430656, 6916, 24240)
print("\n=== achelous .blo bytes around 0x0180..0x02b0 (finding all floats) ===")
for o in range(0x0180, 0x02b0):
    vf = struct.unpack_from("<f", blo, o)[0]
    if 0.0001 <= abs(vf) <= 500.0:
        # Check if it's a clean float
        if any(abs(vf - target) < 0.001 for target in [0.000332, 0.002, 0.15, 0.043, 0.871, 1.0, 3.0, 5.0, 10.0, 18.0, 20.0, 25.0, 30.0, 75.0, 100.0]):
            print(f"  0x{o:04x}: float={vf:12.6f} (hex={blo[o:o+4].hex(' ')}) prev4={blo[o-4:o].hex(' ')}")
