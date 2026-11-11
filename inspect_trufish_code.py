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

pdata_ro = sections[3][3]
pdata_rs = sections[3][4]
def find_func_bounds(target_rva):
    for o in range(pdata_ro, pdata_ro + pdata_rs, 12):
        b_rva, e_rva, u_rva = struct.unpack_from("<III", exe, o)
        if b_rva <= target_rva < e_rva:
            return (b_rva, e_rva, rva_to_file(b_rva), rva_to_file(e_rva))
    return None

# 1. Find the function containing RVA 0xad61b0 (file 0xad55b0)
b_rva, e_rva, b_foff, e_foff = find_func_bounds(0xad61b0)
print(f"=== 1. Function at 0xad61b0: RVA 0x{b_rva:x}..0x{e_rva:x} (file 0x{b_foff:x}..0x{e_foff:x}, len={e_foff-b_foff}) ===")

# Scan all RIP-relative references in file range 0xad2000 .. 0xada000
print("\n=== 2. All RIP-relative string/float references in file 0xad2000..0xada000 ===")
for pos in range(0xad2000, 0xada000):
    # Check for LEA r64, [rip+disp32] (48 8D / 4C 8D with modrm 05/0D/15/1D/25/2D/35/3D)
    if exe[pos] in (0x48, 0x4C) and exe[pos+1] == 0x8D and (exe[pos+2] & 0xC7) == 0x05:
        disp = struct.unpack_from("<i", exe, pos + 3)[0]
        next_rva = file_to_rva(pos + 7)
        target_rva = next_rva + disp
        t_foff = rva_to_file(target_rva)
        if t_foff and 0x1f42e00 <= t_foff < 0x2e20000:
            s_end = exe.find(b"\x00", t_foff, t_foff + 120)
            if s_end != -1 and s_end > t_foff:
                s_val = exe[t_foff:s_end]
                if all(32 <= b < 127 for b in s_val):
                    print(f"  0x{pos:x} (RVA 0x{file_to_rva(pos):x}): LEA -> '{s_val.decode()}'")

# 3. Also dump the exact bytes of the function containing 0xad55b0 (b_foff .. e_foff)
print(f"\n=== 3. Hex dump of function 0x{b_foff:x}..0x{e_foff:x} ===")
for o in range(b_foff, min(e_foff, b_foff + 1024), 32):
    print(f"  0x{o:x}: {exe[o:min(e_foff, o+32)].hex()}")
