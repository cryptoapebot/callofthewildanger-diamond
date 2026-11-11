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

# 1. Inspect editor/entities/fish/largemouth_bass_01.epe_adf in game0.arc
raw_bass_adf = read_orig("game0.arc", 557633536, 3841, 3841)
strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{3,}', raw_bass_adf)]
print(f"=== Strings in largemouth_bass_01.epe_adf (len={len(raw_bass_adf)}) ===")
print(" ", strs)

# 2. Compute Jenkins lookup3 (hashlittle) for all CTruFishSystemObjectData field names and search achelous_global_trufish.blo!
def rot(x, k):
    return ((x << k) | (x >> (32 - k))) & 0xFFFFFFFF

def hashlittle(data: bytes, initval=0) -> int:
    length = len(data)
    a = b = c = (0xdeadbeef + length + initval) & 0xFFFFFFFF
    offset = 0
    while length > 12:
        a = (a + struct.unpack_from("<I", data, offset)[0]) & 0xFFFFFFFF
        b = (b + struct.unpack_from("<I", data, offset + 4)[0]) & 0xFFFFFFFF
        c = (c + struct.unpack_from("<I", data, offset + 8)[0]) & 0xFFFFFFFF
        a = (a - c) & 0xFFFFFFFF; a ^= rot(c, 4); c = (c + b) & 0xFFFFFFFF
        b = (b - a) & 0xFFFFFFFF; b ^= rot(a, 6); a = (a + c) & 0xFFFFFFFF
        c = (c - b) & 0xFFFFFFFF; c ^= rot(b, 8); b = (b + a) & 0xFFFFFFFF
        a = (a - c) & 0xFFFFFFFF; a ^= rot(c, 16); c = (c + b) & 0xFFFFFFFF
        b = (b - a) & 0xFFFFFFFF; b ^= rot(a, 19); a = (a + c) & 0xFFFFFFFF
        c = (c - b) & 0xFFFFFFFF; c ^= rot(b, 4); b = (b + a) & 0xFFFFFFFF
        length -= 12
        offset += 12
    tail = data[offset:]
    if length > 0:
        padded = tail + b"\x00" * (12 - length)
        u0, u1, u2 = struct.unpack("<III", padded)
        if length == 12:
            c = (c + u2) & 0xFFFFFFFF; b = (b + u1) & 0xFFFFFFFF; a = (a + u0) & 0xFFFFFFFF
        elif length == 11:
            c = (c + (u2 & 0xFFFFFF)) & 0xFFFFFFFF; b = (b + u1) & 0xFFFFFFFF; a = (a + u0) & 0xFFFFFFFF
        elif length == 10:
            c = (c + (u2 & 0xFFFF)) & 0xFFFFFFFF; b = (b + u1) & 0xFFFFFFFF; a = (a + u0) & 0xFFFFFFFF
        elif length == 9:
            c = (c + (u2 & 0xFF)) & 0xFFFFFFFF; b = (b + u1) & 0xFFFFFFFF; a = (a + u0) & 0xFFFFFFFF
        elif length == 8:
            b = (b + u1) & 0xFFFFFFFF; a = (a + u0) & 0xFFFFFFFF
        elif length == 7:
            b = (b + (u1 & 0xFFFFFF)) & 0xFFFFFFFF; a = (a + u0) & 0xFFFFFFFF
        elif length == 6:
            b = (b + (u1 & 0xFFFF)) & 0xFFFFFFFF; a = (a + u0) & 0xFFFFFFFF
        elif length == 5:
            b = (b + (u1 & 0xFF)) & 0xFFFFFFFF; a = (a + u0) & 0xFFFFFFFF
        elif length == 4:
            a = (a + u0) & 0xFFFFFFFF
        elif length == 3:
            a = (a + (u0 & 0xFFFFFF)) & 0xFFFFFFFF
        elif length == 2:
            a = (a + (u0 & 0xFFFF)) & 0xFFFFFFFF
        elif length == 1:
            a = (a + (u0 & 0xFF)) & 0xFFFFFFFF
        c ^= b; c = (c - rot(b, 14)) & 0xFFFFFFFF
        a ^= c; a = (a - rot(c, 11)) & 0xFFFFFFFF
        b ^= a; b = (b - rot(a, 25)) & 0xFFFFFFFF
        c ^= b; c = (c - rot(b, 16)) & 0xFFFFFFFF
        a ^= c; a = (a - rot(c, 4)) & 0xFFFFFFFF
        b ^= a; b = (b - rot(a, 14)) & 0xFFFFFFFF
        c ^= b; c = (c - rot(b, 24)) & 0xFFFFFFFF
    return c

blo = read_orig("game16.arc", 63430656, 6916, 24240)
print("\n=== Searching achelous_global_trufish.blo for Jenkins Hashes of TruFish Fields ===")
fields = [
    "CTruFishSystemObject", "CTruFishSystemObjectData", "CTruFishGameObject", "CTruFishGameObjectData",
    "rank_selection_method",
    "distribution_bronze", "distribution_diamond", "distribution_gold", "distribution_silver",
    "rank_spawn_probability_bronze", "rank_spawn_probability_diamond", "rank_spawn_probability_gold",
    "rank_spawn_probability_juvenile", "rank_spawn_probability_silver",
    "species_rank_cap_bronze", "species_rank_cap_diamond", "species_rank_cap_gold",
    "species_rank_cap_juvenile", "species_rank_cap_silver",
    "minimum_water_depth", "scoring_factor_bed_roughness", "fish_per_m_cubed", "max_fish", "max_fish_per_cell"
]
for fn in fields:
    h = hashlittle(fn.encode("ascii"))
    bh = struct.pack("<I", h)
    hits = [hex(i) for i in range(len(blo) - 4) if blo[i:i+4] == bh]
    val_preview = ""
    if hits:
        first_off = int(hits[0], 16)
        u_val = struct.unpack_from("<I", blo, first_off + 4)[0]
        f_val = struct.unpack_from("<f", blo, first_off + 4)[0]
        val_preview = f"-> val at {hits[0]}+4: int={u_val} (0x{u_val:08x}) float={f_val:.5f}"
    print(f"  {fn:35s} hash=0x{h:08x} hits={len(hits):2d} {hits[:4]} {val_preview}")
