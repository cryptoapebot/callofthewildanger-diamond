import struct
import re
import zlib

# 1. Inspect hook_01.epe_adf and hook_10.epe_adf to see how hook_tune_file or TruScoreModifier is stored
with open("extracted/hook_01.epe_adf", "rb") as f:
    h01 = f.read()

print("=== Floats & Hashes in hook_01.epe_adf ===")
for off in range(0, len(h01) - 4, 4):
    vf = struct.unpack_from("<f", h01, off)[0]
    vi = struct.unpack_from("<I", h01, off)[0]
    if 0.001 <= abs(vf) <= 1000.0:
        print(f"  0x{off:04x}: float={vf:10.4f} | int=0x{vi:08x}")

# 2. Parse the SARC header of extracted/global_fish.bl ('AVALANCHEARCHIVEFORMATISCOOLTA')
with open("extracted/global_fish.bl", "rb") as f:
    gf = f.read()

print(f"\n=== Parsing global_fish.bl ({len(gf):,} bytes) ===")
print("Header hex:", gf[:64].hex(" "))
# Find any 'FDA ' (ADF) or 'RTPC' headers inside global_fish.bl!
for sig in [b"FDA ", b"RTPC"]:
    pos = 0
    hits = []
    while True:
        idx = gf.find(sig, pos)
        if idx == -1:
            break
        hits.append(hex(idx))
        pos = idx + 1
    print(f"Signature {sig} found in global_fish.bl at: {hits[:30]} (total {len(hits)})")

# Check if global_fish.bl is zlib-compressed blocks after the header
for off in range(0, min(4096, len(gf) - 2)):
    if gf[off:off+2] in (b"\x78\x9c", b"\x78\x5e", b"\x78\xda", b"\x78\x01"):
        try:
            decomp = zlib.decompress(gf[off:])
            print(f"  Decompressed zlib stream at 0x{off:x} -> {len(decomp):,} bytes!")
            strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{4,}', decomp)]
            print(f"  Strings inside decompressed global_fish.bl ({len(strs)}): {strs[:60]}")
            with open("extracted/global_fish_decomp.bin", "wb") as out_f:
                out_f.write(decomp)
            break
        except Exception:
            pass
