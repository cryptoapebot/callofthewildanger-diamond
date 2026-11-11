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

pdata_ro = sections[3][3]
pdata_rs = sections[3][4]

print("=== 1. Functions in .pdata between file 0xad1500 and 0xad4280 ===")
for o in range(pdata_ro, pdata_ro + pdata_rs, 12):
    b_rva, e_rva, u_rva = struct.unpack_from("<III", exe, o)
    b_foff = b_rva - 0x1000 + 0x400
    e_foff = e_rva - 0x1000 + 0x400
    if 0xad1500 <= b_foff <= 0xad4280:
        print(f"  Func RVA 0x{b_rva:x}..0x{e_rva:x} (file 0x{b_foff:x}..0x{e_foff:x}, len={e_foff-b_foff})")

print("\n=== 2. Search 0xad1000..0xad4280 for displacements +0xe8..+0x130 ===")
for pos in range(0xad1000, 0xad4280):
    val = struct.unpack_from("<I", exe, pos)[0]
    if 0xe8 <= val <= 0x134 and (val % 4 == 0):
        b1 = exe[pos-1]
        if (b1 & 0xC0) == 0x80:
            print(f"  0x{pos-2:x}: disp=+0x{val:x} bytes={exe[pos-4:pos+6].hex()}")

print("\n=== 3. Hex dump of 0xad3600..0xad4280 ===")
for o in range(0xad3600, 0xad4280, 32):
    print(f"  0x{o:x}: {exe[o:o+32].hex()}")
