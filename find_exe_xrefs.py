import os
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")

with open(exe_p, "rb") as f:
    exe = f.read()

# Parse PE sections so we can convert file offsets <-> RVAs
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
    print(f"Section {name:8s}: RVA=0x{vaddr:08x} VSize=0x{vsize:08x} FileOff=0x{roff:08x}")

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

# Find targets in .rdata
targets = {
    "MAX_Score_%s": exe.find(b"MAX_Score_%s\x00"),
    "MAX_KG_%s": exe.find(b"MAX_KG_%s\x00"),
    "new_diamond_spawns": exe.find(b"new_diamond_spawns\x00"),
    "CTruFishSystemObjectData_ADF": 0x2902cf0,
}

for lbl, foff in targets.items():
    rva = file_to_rva(foff)
    print(f"\nTarget {lbl:28s}: file=0x{foff:x} -> RVA=0x{rva:x}")
    # Search .text section for RIP-relative LEA / MOV referencing this RVA!
    # In x86-64, RIP-relative addressing has disp32 = target_rva - (instr_rva + instr_len)
    # where disp32 is at offset pos in .text, and next_rip_rva = rva_of_disp32 + 4
    text_name, text_va, text_vs, text_ro, text_rs = sections[0]
    for pos in range(text_ro, text_ro + text_rs - 4):
        disp = struct.unpack_from("<i", exe, pos)[0]
        next_rva = text_va + (pos - text_ro) + 4
        if next_rva + disp == rva:
            print(f"  [XREF in .text] file=0x{pos:x} (RVA=0x{next_rva-4:x}) bytes={exe[pos-3:pos+8].hex()}")
