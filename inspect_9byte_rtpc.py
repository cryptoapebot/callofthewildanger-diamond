import struct

with open("extracted/achelous_global_trufish.blo", "rb") as f:
    blo = f.read()

# At 0x0270 we have 9-byte records: <II B (hash32, val32, type8)
# Let's walk backwards and forwards from 0x0270 in 9-byte steps!
print("=== Walking 9-byte RTPC properties around 0x0270 in achelous_global_trufish.blo ===")
start_off = 0x0270 - (18 * 9)
for i in range(30):
    off = start_off + (i * 9)
    h32, u32, t8 = struct.unpack_from("<IIB", blo, off)
    f32 = struct.unpack_from("<f", blo, off + 4)[0]
    i32 = struct.unpack_from("<i", blo, off + 4)[0]
    print(f"  0x{off:04x}: hash=0x{h32:08x} | int={i32:11d} (0x{u32:08x}) | float={f32:12.6f} | type={t8}")
