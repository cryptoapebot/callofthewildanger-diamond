import os
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

pe_off = struct.unpack_from("<I", exe, 0x3C)[0]
num_sec = struct.unpack_from("<H", exe, pe_off + 6)[0]
opt_size = struct.unpack_from("<H", exe, pe_off + 20)[0]
sec_table = pe_off + 24 + opt_size

sections = []
for i in range(num_sec):
    s = sec_table + i * 40
    name = exe[s:s+8].rstrip(b"\x00").decode('latin1')
    vsize, vaddr, rsize, roff = struct.unpack_from("<IIII", exe, s + 8)
    sections.append((name, vaddr, vsize, roff, rsize))

def file_to_rva(foff):
    for name, va, vs, ro, rs in sections:
        if ro <= foff < ro + rs:
            return va + (foff - ro)
    return None

def rva_to_file(rva):
    for name, va, vs, ro, rs in sections:
        if va <= rva < va + vs:
            return ro + (rva - va)
    return None

# 1. Find XREFs to the strings around 0x2793bb0 (rank_spawn_probability_diamond, distribution_diamond, species_rank_cap_diamond, FishDataByRank)
str_queries = [
    b"rank_spawn_probability_diamond\x00",
    b"distribution_diamond\x00",
    b"species_rank_cap_diamond\x00",
    b"FishDataByRank\x00",
    b"hook_meta_data\x00",
]

text_name, text_va, text_vs, text_ro, text_rs = sections[0]

for sq in str_queries:
    pos = 0
    while True:
        foff = exe.find(sq, pos)
        if foff == -1 or foff > 0x2850000:
            break
        rva = file_to_rva(foff)
        print(f"String {sq[:-1].decode():32s} @ file=0x{foff:x} (RVA=0x{rva:x}):")
        for tpos in range(text_ro, text_ro + text_rs - 4):
            disp = struct.unpack_from("<i", exe, tpos)[0]
            next_rva = text_va + (tpos - text_ro) + 4
            if next_rva + disp == rva:
                print(f"  -> XREF in .text @ file=0x{tpos:x} (RVA=0x{next_rva-4:x})")
        pos = foff + 1

# 2. Look up the functions in .pdata containing RVA 0xab57a2, 0xcd1817, and any XREFs found above!
pdata_ro = sections[3][3]
pdata_rs = sections[3][4]
def find_func_bounds(target_rva):
    for o in range(pdata_ro, pdata_ro + pdata_rs, 12):
        b_rva, e_rva, u_rva = struct.unpack_from("<III", exe, o)
        if b_rva <= target_rva < e_rva:
            return (b_rva, e_rva, rva_to_file(b_rva), rva_to_file(e_rva))
    return None

for lbl, trva in [("CodexLoader (0xab57a2)", 0xab57a2), ("TruFishSys (0xcd1817)", 0xcd1817)]:
    bounds = find_func_bounds(trva)
    print(f"\nFunction {lbl}: RVA 0x{bounds[0]:x}..0x{bounds[1]:x} (file 0x{bounds[2]:x}..0x{bounds[3]:x}, len={bounds[3]-bounds[2]})")
