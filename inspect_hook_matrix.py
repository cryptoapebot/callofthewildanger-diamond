import os
import re
import struct
import zlib

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

# 1. Inspect all columns and rows of extracted/hook_meta_data.csvc
with open("extracted/hook_meta_data.csvc", "r", encoding="utf-8") as f:
    h_lines = [l.strip() for l in f.readlines() if l.strip()]

print(f"=== hook_meta_data.csvc: {len(h_lines)} lines ===")
hdr = h_lines[0].split(",")
print(f"Total columns: {len(hdr)}")

# Find all unique FishIDs across all cells in hook_meta_data.csvc
col_fish = {}
for r_idx, line in enumerate(h_lines[2:], start=2):
    parts = line.split(",")
    print(f"Row {r_idx:2d} ({parts[0]:8s}, {parts[1]:16s}): non-empty cells = {sum(1 for x in parts[2:] if x)} / {len(parts)-2}")
    for c_idx, cell in enumerate(parts[2:], start=2):
        if cell:
            fish_id = cell.split("/")[0]
            col_fish[c_idx] = fish_id

print(f"\nMapped {len(col_fish)} / {len(hdr)-2} Compatibility columns to FishIDs:")
for c_idx in sorted(col_fish.keys())[:30]:
    print(f"  Col {c_idx:3d}: {col_fish[c_idx]}")

# Print all unique rank suffix patterns used in hook_meta_data.csvc
suffixes = set()
for line in h_lines[2:]:
    for cell in line.split(",")[2:]:
        if "/" in cell:
            suffixes.add(cell.split("/", 1)[1])
print("\nUnique rank suffixes in hook_meta_data.csvc:")
for s in sorted(suffixes):
    print(" ", s)

# 2. Check what strings/floats are inside hook_01.epe_adf and global/global_fish.bl
with open("extracted/hook_01.epe_adf", "rb") as f:
    h01 = f.read()
# Find all floats or hashes in hook_01.epe_adf
print("\nStrings in global/global_fish.bl:")
gf_raw = read_orig("game0.arc", 926879744, 609416, 609416)
with open("extracted/global_fish.bl", "wb") as f:
    f.write(gf_raw)
gf_strs = [s.decode('latin1') for s in re.findall(b'[A-Za-z0-9_./-]{4,}', gf_raw)]
print("  First 60 strings in global_fish.bl:", gf_strs[:60])
