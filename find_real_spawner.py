import os
import glob
import struct
import zlib
import sqlite3

ARCHIVE_DIR = (
    "C:/Program Files (x86)/Steam/steamapps/common/"
    "Call of the Wild The Angler/archives_win64/initial"
)

# 1. Scan ALL .tab files in ARCHIVE_DIR for the v_hashes of fish_codex_*, hook_meta_data, and global_trufish!
target_hashes = {
    5775195222236934712:  "fish_codex_achelous.csvc",
    1641961905539253042:  "fish_codex_alpheus.csvc",
    5796824274819009528:  "fish_codex_belisama.csvc",
    -7827499170503240933: "fish_codex_ceto.csvc",
    -8597476204515797250: "fish_codex_doris.csvc",
    4245202897118090955:  "achelous global_trufish.blo_adf",
    -5714746364590497236: "achelous global_trufish.blo",
    -588015160189099245:  "alpheus global_trufish.blo_adf",
    5612303823963747841:  "belisama global_trufish.blo_adf",
    -8655686045783063754: "ceto global_trufish.blo_adf",
    -5172364055990370037: "doris global_trufish.blo_adf",
}

print("=== 1. Scanning ALL .tab files on disk for duplicate/override v_hashes ===")
for tab_path in sorted(glob.glob(os.path.join(ARCHIVE_DIR, "*.tab"))):
    tab_name = os.path.basename(tab_path)
    with open(tab_path, "rb") as f:
        data = f.read()
    for vh, label in target_hashes.items():
        b_vh = struct.pack("<q", vh)
        pos = 0
        while True:
            idx = data.find(b_vh, pos)
            if idx == -1:
                break
            _, off, sc, su, flg = struct.unpack_from("<qIIII", data, idx)
            print(f"  {tab_name:12s} has {label:32s} at tab_pos=0x{idx:x} -> arc_off=0x{off:x}, sc={sc}, su={su}")
            pos = idx + 8

# 2. Check if global_trufish.blo_adf is ALSO packed inside any .bl (EWAM/AAF SARC) in game16.arc!
print("\n=== 2. Scanning game16.arc .bl SARC containers for 'CTruFishSystemObjectData' ===")
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
cur.execute("""
SELECT n.node_id, n.v_path, n.parent_offset, n.size_c, n.size_u
FROM core_nodes n
JOIN core_nodes p ON n.parent_id = p.node_id
WHERE p.p_path LIKE '%game16.tab%'
""")
arc16_p = os.path.join(ARCHIVE_DIR, "game16.arc.bak")
if not os.path.exists(arc16_p):
    arc16_p = os.path.join(ARCHIVE_DIR, "game16.arc")

with open(arc16_p, "rb") as af:
    for nid, vp, off, sc, su in cur.fetchall():
        af.seek(off)
        chunk = af.read(sc)
        if sc != su:
            try:
                chunk = zlib.decompress(chunk)
            except Exception:
                pass
        # If it's an AAF/EWAM container, decompress its EWAM blocks too
        ewam = chunk.find(b"EWAM")
        if ewam != -1:
            try:
                chunk = zlib.decompress(chunk[ewam+4:], -15)
            except Exception:
                pass
        if b"CTruFishSystemObjectData" in chunk or b"rank_spawn_probability_diamond" in chunk:
            print(f"  [FOUND in game16.arc!] node={nid} v_path={vp} off={off} sc={sc} su={su} (unpacked len={len(chunk)})")

# 3. Inspect FishDataByRank inside largemouth_bass_01.ee (game0.arc, off=556679168, sc=946250)
print("\n=== 3. Inspecting largemouth_bass_01.frtune inside largemouth_bass_01.ee ===")
arc0_p = os.path.join(ARCHIVE_DIR, "game0.arc.bak")
if not os.path.exists(arc0_p):
    arc0_p = os.path.join(ARCHIVE_DIR, "game0.arc")
with open(arc0_p, "rb") as af:
    af.seek(556679168)
    bass_ee = af.read(946250)
ewam = bass_ee.find(b"EWAM")
bass_sarc = zlib.decompress(bass_ee[ewam+4:], -15)
pos_fd = bass_sarc.find(b"FishDataByRank")
if pos_fd != -1:
    # Find the ' FDA' header right before FishDataByRank
    fda_start = bass_sarc.rfind(b" FDA", 0, pos_fd)
    fda_end = bass_sarc.find(b" FDA", fda_start + 4)
    frtune = bass_sarc[fda_start:fda_end]
    print(f"  Found largemouth_bass_01.frtune at SARC offset 0x{fda_start:x} (len={len(frtune)})")
    # Dump the last 256 bytes of data before the string table in frtune
    for o in range(0x280, min(0x380, len(frtune)), 4):
        vi = struct.unpack_from("<i", frtune, o)[0]
        vf = struct.unpack_from("<f", frtune, o)[0]
        print(f"    +0x{o:03x}: int={vi:10d} (0x{vi&0xffffffff:08x}) | float={vf:10.4f}")

conn.close()
