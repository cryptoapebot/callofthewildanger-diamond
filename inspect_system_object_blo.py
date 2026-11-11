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

# 1. Check doris node 79898 (.blo_adf) for CTruFishSystemObjectData
doris_adf = read_orig("game32.arc", 66351104, 6509, 17340)
for off in range(0, len(doris_adf) - 128, 4):
    db, dd, dg, ds = struct.unpack_from("<ffff", doris_adf, off)
    pb, pd, pg, pj, ps = struct.unpack_from("<fffff", doris_adf, off + 0x3C)
    if 10.0 <= db <= 30.0 and pb == 1.0 and 0.001 <= pd <= 0.5:
        print(f"Found Doris CTruFishSystemObjectData in game32.arc at 0x{off:x}: dist=({db},{dd},{dg},{ds}) prob=({pb},{pd},{pg},{pj},{ps})")

# 2. Find where "CTruFishSystemObject" string is in achelous_global_trufish.blo and find all 9-byte RTPC properties in .blo!
blo = read_orig("game16.arc", 63430656, 6916, 24240)
s_pos = blo.find(b"CTruFishSystemObject")
print(f"\n'CTruFishSystemObject' string in achelous .blo at: 0x{s_pos:x}")
if s_pos != -1:
    b_spos = struct.pack("<I", s_pos)
    refs = [hex(i) for i in range(len(blo) - 4) if blo[i:i+4] == b_spos]
    print(f"References to 0x{s_pos:x} in .blo: {refs}")
    for r_hex in refs:
        r_off = int(r_hex, 16) - 4 # start of 9-byte property (hash32, val32, type8)
        print(f"\n--- Walking 9-byte RTPC properties around 0x{r_off:x} ---")
        for step in range(-25, 15):
            o = r_off + (step * 9)
            if 0 <= o <= len(blo) - 9:
                h32, u32, t8 = struct.unpack_from("<IIB", blo, o)
                f32 = struct.unpack_from("<f", blo, o + 4)[0]
                i32 = struct.unpack_from("<i", blo, o + 4)[0]
                if h32 != 0 or u32 != 0 or t8 != 0:
                    print(f"  {step:+3d} (0x{o:04x}): hash=0x{h32:08x} | int={i32:11d} (0x{u32:08x}) | float={f32:12.5f} | type={t8}")
