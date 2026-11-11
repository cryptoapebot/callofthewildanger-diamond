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

def unpack_ewam_all(raw):
    out = bytearray()
    pos = 0
    while True:
        idx = raw.find(b"EWAM", pos)
        if idx == -1:
            break
        # EWAM header is 16 bytes or 4 bytes? Let's try decompressing at idx+4, idx+8, idx+12, idx+16
        for delta in (4, 8, 12, 16):
            try:
                dec = zlib.decompress(raw[idx + delta:], -15)
                if len(dec) > 16:
                    out.extend(dec)
                    break
            except Exception:
                pass
        pos = idx + 4
    return bytes(out) if out else raw

# 1. Inspect settings/fishsystem.bin (game12.arc, off=593985536, sc=92, su=92)
fs_bin = read_orig("game12.arc", 593985536, 92, 92)
print("=== 1. settings/fishsystem.bin (92 bytes) ===")
for o in range(0, len(fs_bin), 4):
    vi = struct.unpack_from("<i", fs_bin, o)[0]
    vu = struct.unpack_from("<I", fs_bin, o)[0]
    vf = struct.unpack_from("<f", fs_bin, o)[0]
    print(f"  0x{o:02x}: int={vi:11d} (0x{vu:08x}) | float={vf:12.5f}")

# 2. Inspect worlds/achelous/locations/global_trufish.bl (game16.arc, off=63422464, sc=4231, su=4231)
gt_bl = read_orig("game16.arc", 63422464, 4231, 4231)
print("\n=== 2. worlds/achelous/locations/global_trufish.bl (off=63422464, 4231 bytes) ===")
print("  First 32 bytes:", gt_bl[:32])
gt_unp = unpack_ewam_all(gt_bl)
print(f"  Unpacked len: {len(gt_unp)}")
strs_gt = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{4,}', gt_unp)]
print("  Strings in global_trufish.bl:", strs_gt[:40])

# 3. Inspect global/global_fish.bl (game0.arc, off=926879744, sc=609416, su=609416)
gf_bl = read_orig("game0.arc", 926879744, 609416, 609416)
print("\n=== 3. global/global_fish.bl (off=926879744, 609416 bytes) ===")
print("  First 32 bytes:", gf_bl[:32])
gf_unp = unpack_ewam_all(gf_bl)
print(f"  Unpacked len: {len(gf_unp)}")
strs_gf = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{4,}', gf_unp)]
# Filter for filenames or interesting strings
interesting = [s for s in strs_gf if any(k in s.lower() for k in [".", "fish", "rank", "score", "codex", "trufish", "diamond", "bronze", "tune", "csv"])]
print(f"  Interesting strings in global_fish.bl ({len(interesting)} total):", interesting[:80])
