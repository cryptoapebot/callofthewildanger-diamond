import struct

with open("extracted/achelous_global_trufish.blo", "rb") as f:
    blo = f.read()

# In achelous_global_trufish.blo, we saw at 0x0300..0x0350:
# 0x0300: hash=0x02685abd, val_or_off=0x00000400 (1024), type=4
# Let's dump the RTPC property headers from 0x0300 to 0x0520!
print("=== RTPC Property Headers at 0x0300 .. 0x0520 in achelous_global_trufish.blo ===")
for off in range(0x0300, 0x0520, 12):
    h32, val_u, ptype = struct.unpack_from("<III", blo, off)
    val_f = struct.unpack_from("<f", blo, off + 4)[0]
    extra = ""
    if 0x100 <= val_u < len(blo) - 16:
        # Check what is at file offset val_u
        d1, d2, d3 = struct.unpack_from("<III", blo, val_u)
        f1, f2, f3 = struct.unpack_from("<fff", blo, val_u)
        extra = f"-> @0x{val_u:x}: ints=({d1},{d2},{d3}) floats=({f1:.5f}, {f2:.5f}, {f3:.5f})"
    print(f"  0x{off:04x}: hash=0x{h32:08x} | val=0x{val_u:08x} ({val_f:10.4f}) | type={ptype:2d} {extra}")

# Also dump the RTPC property headers around 0x4e30 ('TruFishReserveSettings')!
print("\n=== Searching for 'TruFishReserveSettings' string offset (0x4e30) in .blo ===")
off_bytes = struct.pack("<I", 0x4e30)
for m in range(0, len(blo) - 4, 4):
    if blo[m:m+4] == off_bytes:
        print(f"  Pointer to 0x4e30 found at 0x{m:04x}")
        start = max(0, m - 96)
        for o in range(start, min(len(blo) - 12, m + 180), 4):
            u1 = struct.unpack_from("<I", blo, o)[0]
            f1 = struct.unpack_from("<f", blo, o)[0]
            print(f"    0x{o:04x}: 0x{u1:08x} ({u1:10d}) | float={f1:12.5f}")
