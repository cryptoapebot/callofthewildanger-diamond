import os
import struct
import re
import sqlite3

# 1. Inspect the SARC header & file table of extracted/hook_01_ee_sarc.bin and extracted/global_fish_sarc.bin
for fname in ["extracted/hook_01_ee_sarc.bin", "extracted/global_fish_sarc.bin"]:
    with open(fname, "rb") as f:
        data = f.read()
    print(f"\n=== SARC Header of {fname} ({len(data):,} bytes) ===")
    print("First 64 bytes:", data[:64].hex(" "))
    # Find all printable path/type strings in the first 8192 bytes (the SARC directory table)
    hdr_strs = [(m.start(), m.group(0).decode('latin1')) for m in re.finditer(b'[A-Za-z0-9_./-]{4,}', data[:16384])]
    print("Directory strings:", hdr_strs[:40])
    # Also search entire SARC for 'FDA ' (ADF) or 'RTPC' or 'TruScore' or 'HookStats'
    for pat in [b"FDA ", b"RTPC", b"TruScore", b"HookStats", b"FishDefaults", b"FishStats", b"frtunec"]:
        hits = [hex(m.start()) for m in re.finditer(re.escape(pat), data)]
        if hits:
            print(f"  Pattern {pat} at: {hits[:20]} (total {len(hits)})")

# 2. Compare hook_01.epe_adf and hook_10.epe_adf from game0.arc to see what differs between hook sizes!
ARCHIVE_DIR = (
    "C:/Program Files (x86)/Steam/steamapps/common/"
    "Call of the Wild The Angler/archives_win64/initial"
)
with open(os.path.join(ARCHIVE_DIR, "game0.arc"), "rb") as af:
    af.seek(416845824)
    h01_adf = af.read(3136)
    af.seek(417177600)
    h10_adf = af.read(3136)

print(f"\n=== Comparing hook_01.epe_adf vs hook_10.epe_adf (len={len(h01_adf)}) ===")
for off in range(0, len(h01_adf), 4):
    if h01_adf[off:off+4] != h10_adf[off:off+4]:
        u1 = struct.unpack_from("<I", h01_adf, off)[0]
        u2 = struct.unpack_from("<I", h10_adf, off)[0]
        f1 = struct.unpack_from("<f", h01_adf, off)[0]
        f2 = struct.unpack_from("<f", h10_adf, off)[0]
        print(f"  Diff at 0x{off:04x}: hook_01=0x{u1:08x} ({f1:.4f}) | hook_10=0x{u2:08x} ({f2:.4f})")
