import struct

with open("extracted/achelous_global_trufish.blo", "rb") as f:
    blo = f.read()

print("=== Inspecting around 0x27d in achelous_global_trufish.blo ===")
for off in range(0x200, 0x350, 4):
    vi = struct.unpack_from("<I", blo, off)[0]
    vf = struct.unpack_from("<f", blo, off)[0]
    print(f"  0x{off:04x}: int=0x{vi:08x} ({vi:10d}) | float={vf:12.5f}")

# Also search for the exact float values from achelous_global_trufish.blo_adf (e.g. 75.0, 5.0, 100.0, 0.00033, 0.002, 0.15)
for label, val in [
    ("0.00033 (prob_diamond in achelous)", 0.0003321),
    ("0.00200 (prob_gold2 in achelous)", 0.002),
    ("75.0 (dist_bronze in achelous)", 75.0),
    ("0.043 (dist_diamond in achelous)", 0.043),
    ("0.871 (dist_gold in achelous)", 0.871),
]:
    b_val = struct.pack("<f", val)
    # Search for top 2 bytes of float (exponent + high mantissa)
    hits = []
    for o in range(0, len(blo) - 4):
        vf = struct.unpack_from("<f", blo, o)[0]
        if abs(vf - val) < 0.0001:
            hits.append((hex(o), vf))
    print(f"\nMatches for {label}: {hits[:20]}")
