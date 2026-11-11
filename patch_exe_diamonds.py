import os
import shutil
import struct

GAME_DIR = "C:/Program Files (x86)/Steam/steamapps/common/Call of the Wild The Angler"
ARCH_DIR = os.path.join(GAME_DIR, "archives_win64")
exe_p = os.path.join(GAME_DIR, "CotWTheAngler_Steam.exe")
bak_p = exe_p + ".bak"

# 1. Restore from clean backup of CotWTheAngler_Steam.exe
if not os.path.exists(bak_p):
    shutil.copy2(exe_p, bak_p)
    print(f"[BACKUP] Created clean backup: {bak_p}")
else:
    print(f"[BACKUP] Restoring from clean backup first: {bak_p}")
    shutil.copy2(bak_p, exe_p)

# 2. Restore any modified archive files (.bak) so hook_meta_data.csvc and codex files are clean vanilla
for fn in os.listdir(ARCH_DIR):
    if fn.endswith(".bak"):
        orig_fn = fn[:-4]
        src = os.path.join(ARCH_DIR, fn)
        dst = os.path.join(ARCH_DIR, orig_fn)
        shutil.copy2(src, dst)
        print(f"[ARCHIVE RESTORE] Restored clean vanilla {orig_fn}")

with open(exe_p, "rb") as f:
    exe = bytearray(f.read())

# Locate exact offsets inside the small windows to avoid 1-2 byte alignment shifts
def find_in_window(start, end, pat, name):
    idx = exe.find(pat, start, end)
    assert idx != -1, f"Could not find {name} ({pat.hex()}) in 0x{start:x}..0x{end:x}!"
    print(f"[FOUND] {name:45s} @ 0x{idx:x}: {pat.hex()}")
    return idx

off_rand_weighted = find_in_window(0xaca798, 0xaca7b0, bytes.fromhex("4c8bdc555641"), "RandomWeighted (0xaca7a0)")
off_fixed_dist    = find_in_window(0xacad98, 0xacadb0, bytes.fromhex("415441554883"), "FixedDistribution (0xacada0)")
off_get_rank      = find_in_window(0xad3c98, 0xad3cb0, bytes.fromhex("48895c240857"), "GetRankFromScore (0xad3ca0)")
off_cap_check     = find_in_window(0xacb258, 0xacb268, bytes.fromhex("83f9ff740e"),   "PickCandidateCellForRank cap check") + 3
off_prob_check    = find_in_window(0xacbf10, 0xacbf28, bytes.fromhex("0f87b8040000"), "SpawnFishInCell probability check")
off_loop1_start   = find_in_window(0xad3bf8, 0xad3c10, bytes.fromhex("0f2fcbf30f1000"), "EvalHabitatAndScore Rank Loop 1")
off_loop1_end     = find_in_window(0xad3c18, 0xad3c30, bytes.fromhex("33c94189532c"),   "EvalHabitatAndScore Loop 1 Target")
off_loop2_start   = find_in_window(0xad3c25, 0xad3c40, bytes.fromhex("0f2fe2f3410f1000"), "EvalHabitatAndScore Rank Loop 2")
off_loop2_end     = find_in_window(0xad3c48, 0xad3c60, bytes.fromhex("f3410f116b14"),   "EvalHabitatAndScore Loop 2 Target")

# Apply code patches:
# A. RandomWeighted -> mov eax, 4; ret (b8 04 00 00 00 c3)
exe[off_rand_weighted:off_rand_weighted+6] = bytes.fromhex("b804000000c3")

# B. FixedDistribution -> mov eax, 4; ret (b8 04 00 00 00 c3)
exe[off_fixed_dist:off_fixed_dist+6] = bytes.fromhex("b804000000c3")

# C. GetRankFromScore -> mov eax, 4; ret (b8 04 00 00 00 c3)
exe[off_get_rank:off_get_rank+6] = bytes.fromhex("b804000000c3")

# D. PickCandidateCellForRank cap check -> jmp +0x0e (eb 0e)
exe[off_cap_check:off_cap_check+2] = bytes.fromhex("eb0e")

# E. SpawnFishInCell probability check -> 6x NOP (90 90 90 90 90 90)
exe[off_prob_check:off_prob_check+6] = bytes.fromhex("909090909090")

# F. EvalHabitatAndScore Rank Loop 1 -> mov edx, 4; jmp off_loop1_end
rel1 = off_loop1_end - (off_loop1_start + 7)
assert 0 < rel1 < 127
exe[off_loop1_start:off_loop1_start+7] = b"\xba\x04\x00\x00\x00\xeb" + struct.pack("<B", rel1)

# G. EvalHabitatAndScore Rank Loop 2 -> mov ecx, 4; jmp off_loop2_end
rel2 = off_loop2_end - (off_loop2_start + 7)
assert 0 < rel2 < 127
exe[off_loop2_start:off_loop2_start+7] = b"\xb9\x04\x00\x00\x00\xeb" + struct.pack("<B", rel2)

# H. Update the embedded ADF default table in CotWTheAngler_Steam.exe (0x2902f70..0x2903250)
struct.pack_into("<f", exe, 0x2902f70, 0.0)    # distribution_bronze
struct.pack_into("<f", exe, 0x2902f90, 100.0)  # distribution_diamond
struct.pack_into("<f", exe, 0x2902fb0, 0.0)    # distribution_gold
struct.pack_into("<f", exe, 0x2902fd0, 0.0)    # distribution_silver
struct.pack_into("<f", exe, 0x2903150, 0.0)    # rank_spawn_probability_bronze
struct.pack_into("<f", exe, 0x2903170, 1.0)    # rank_spawn_probability_diamond
struct.pack_into("<f", exe, 0x2903190, 0.0)    # rank_spawn_probability_gold
struct.pack_into("<f", exe, 0x29031b0, 0.0)    # rank_spawn_probability_juvenile
struct.pack_into("<f", exe, 0x29031d0, 0.0)    # rank_spawn_probability_silver
struct.pack_into("<i", exe, 0x2903250, -1)     # species_rank_cap_diamond (-1 = unlimited)

with open(exe_p, "wb") as f:
    f.write(exe)

print(f"\n[SUCCESS] Patched CotWTheAngler_Steam.exe (rel1=0x{rel1:02x}, rel2=0x{rel2:02x}) and restored vanilla archives!")
