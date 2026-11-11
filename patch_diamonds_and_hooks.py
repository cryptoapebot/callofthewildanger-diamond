import os
import shutil
import struct
import zlib
import sqlite3

ARCHIVE_DIR = (
    "C:/Program Files (x86)/Steam/steamapps/common/"
    "Call of the Wild The Angler/archives_win64/initial"
)

def backup_file(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        print("Creating backup:", os.path.basename(bak))
        shutil.copy2(path, bak)

def read_orig(arc_name, offset, size_c, size_u):
    arc_p = os.path.join(ARCHIVE_DIR, arc_name)
    src = arc_p + ".bak" if os.path.exists(arc_p + ".bak") else arc_p
    with open(src, "rb") as f:
        f.seek(offset)
        chunk = f.read(size_c)
    if size_c == size_u:
        return chunk
    return zlib.decompress(chunk)

def write_node(tab_n, arc_n, v_hash, orig_off, orig_sc, new_bytes):
    tab_p = os.path.join(ARCHIVE_DIR, tab_n)
    arc_p = os.path.join(ARCHIVE_DIR, arc_n)
    backup_file(tab_p)
    backup_file(arc_p)

    comp = zlib.compress(new_bytes, level=9)
    new_sc = len(comp)
    new_su = len(new_bytes)

    with open(tab_p, "rb") as f:
        tab_data = bytearray(f.read())

    vh_bytes = struct.pack("<q", v_hash)
    pos = tab_data.find(vh_bytes)
    if pos == -1:
        raise RuntimeError(f"v_hash {v_hash} not found in {tab_n}")

    vals = struct.unpack_from("<qIIII", tab_data, pos)
    cur_flags = vals[4]

    slot = ((orig_sc + 4095) // 4096) * 4096
    with open(arc_p, "r+b") as af:
        if new_sc <= slot:
            w_off = orig_off
            af.seek(w_off)
            af.write(comp)
            if new_sc < orig_sc:
                af.write(b"\x00" * (orig_sc - new_sc))
        else:
            af.seek(0, os.SEEK_END)
            end_p = af.tell()
            pad = (4096 - (end_p % 4096)) % 4096
            if pad:
                af.write(b"\x00" * pad)
            w_off = af.tell()
            af.write(comp)

    struct.pack_into(
        "<qIIII", tab_data, pos,
        v_hash, w_off, new_sc, new_su, cur_flags
    )
    with open(tab_p, "wb") as f:
        f.write(tab_data)

    print(f"  [OK] {tab_n} (off=0x{w_off:x}): size_c {orig_sc} -> {new_sc}, size_u={new_su}")

def fmt_num(val):
    s = f"{val:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"

def patch_csvc(raw_bytes, fname):
    text = raw_bytes.decode("utf-8")
    lines = text.splitlines(keepends=True)
    hdr = lines[0].strip().split(",")
    c_idx = {name: i for i, name in enumerate(hdr)}

    out = [lines[0], lines[1]]
    cnt = 0
    for line in lines[2:]:
        if not line.strip():
            out.append(line)
            continue
        end = "\r\n" if line.endswith("\r\n") else "\n"
        p = line.rstrip("\r\n").split(",")
        if len(p) < len(hdr):
            out.append(line)
            continue

        # Strictly increasing score brackets (1, 2, 3, 4, 100)
        p[c_idx["MAX_Score_Juvenile"]] = "1"
        p[c_idx["MAX_Score_Bronze"]]   = "2"
        p[c_idx["MAX_Score_Silver"]]   = "3"
        p[c_idx["MAX_Score_Gold"]]     = "4"
        p[c_idx["MAX_Score_Diamond"]]  = "100"

        # Strictly increasing Scale values right at the Diamond threshold
        g_scale = float(p[c_idx["MAX_Scale_Gold"]])
        d_scale = float(p[c_idx["MAX_Scale_Diamond"]])
        if g_scale >= d_scale:
            g_scale = max(0.1, d_scale * 0.9)
        p[c_idx["Scale_MIN"]]          = fmt_num(g_scale)
        p[c_idx["MAX_Scale_Juvenile"]] = fmt_num(g_scale + 0.001)
        p[c_idx["MAX_Scale_Bronze"]]   = fmt_num(g_scale + 0.002)
        p[c_idx["MAX_Scale_Silver"]]   = fmt_num(g_scale + 0.003)
        p[c_idx["MAX_Scale_Gold"]]     = fmt_num(g_scale + 0.004)

        # Strictly increasing KG values right at the Diamond threshold
        g_kg = float(p[c_idx["MAX_KG_Gold"]])
        d_kg = float(p[c_idx["MAX_KG_Diamond"]])
        if g_kg >= d_kg:
            g_kg = max(0.05, d_kg * 0.9)
        p[c_idx["KG_MIN"]]          = fmt_num(g_kg)
        p[c_idx["MAX_KG_Juvenile"]] = fmt_num(g_kg + 0.001)
        p[c_idx["MAX_KG_Bronze"]]   = fmt_num(g_kg + 0.002)
        p[c_idx["MAX_KG_Silver"]]   = fmt_num(g_kg + 0.003)
        p[c_idx["MAX_KG_Gold"]]     = fmt_num(g_kg + 0.004)

        out.append(",".join(p) + end)
        cnt += 1

    print(f"  Modified {cnt} species in {fname}")
    return "".join(out).encode("utf-8")

def patch_hook_meta_diamond_only(raw_bytes):
    text = raw_bytes.decode("utf-8")
    lines = text.splitlines(keepends=True)
    hdr = lines[0].rstrip("\r\n").split(",")
    num_cols = len(hdr)

    col_fish = {}
    for line in lines[2:]:
        if not line.strip():
            continue
        parts = line.rstrip("\r\n").split(",")
        for c_i in range(2, min(len(parts), num_cols)):
            cell = parts[c_i].strip()
            if cell and c_i not in col_fish:
                fish_id = cell.split("/")[0]
                is_leg = ("legendary" in cell.lower())
                col_fish[c_i] = (fish_id, is_leg)

    out = [lines[0], lines[1]]
    hook_cnt = 0
    for line in lines[2:]:
        if not line.strip():
            out.append(line)
            continue
        end = "\r\n" if line.endswith("\r\n") else "\n"
        parts = line.rstrip("\r\n").split(",")
        if len(parts) < num_cols:
            parts.extend([""] * (num_cols - len(parts)))

        for c_i in range(2, num_cols):
            if c_i in col_fish:
                fid, is_leg = col_fish[c_i]
                if is_leg:
                    parts[c_i] = f"{fid}/legendary"
                else:
                    # ONLY allow diamond rank to bite on every hook size!
                    parts[c_i] = f"{fid}/diamond"

        out.append(",".join(parts) + end)
        hook_cnt += 1

    print(f"  Set all {len(col_fish)} fish to /diamond ONLY across all {hook_cnt} hook sizes in hook_meta_data.csvc!")
    return "".join(out).encode("utf-8")

def patch_trufish_strict_diamond(raw_bytes, fname):
    data = bytearray(raw_bytes)
    found = 0
    for off in range(0, len(data) - 128, 4):
        db, dd, dg, ds = struct.unpack_from("<ffff", data, off)
        pb, pd, pg, pj, ps = struct.unpack_from("<fffff", data, off + 0x3C)
        cond1 = (10.0 <= db <= 30.0 and 0.01 <= dd <= 2.0)
        cond2 = (pb == 1.0 and 0.001 <= pd <= 0.5)
        if cond1 and cond2:
            print(f"  Found CTruFishSystemObjectData in {fname} at 0x{off:x}")
            # Distribution: Bronze=0.0, Diamond=100.0, Gold=0.0, Silver=0.0
            struct.pack_into("<ffff", data, off, 0.0, 100.0, 0.0, 0.0)
            # Spawn Probabilities: Bronze=0.0, Diamond=1.0, Gold=0.0, Juvenile=0.0, Silver=0.0
            struct.pack_into("<fffff", data, off + 0x3C, 0.0, 1.0, 0.0, 0.0, 0.0)
            # Keep all 5 species_rank_cap_* at -1 (unlimited)
            struct.pack_into("<iiiii", data, off + 0x58, -1, -1, -1, -1, -1)
            found += 1
    if found == 0:
        print("  [WARN] Pattern not found in", fname)
    return bytes(data)

print("=== 1. Restoring Clean game12.tab/.arc Before Re-Patching ===")
for fn in ["game12.tab", "game12.arc"]:
    p = os.path.join(ARCHIVE_DIR, fn)
    if os.path.exists(p + ".bak"):
        shutil.copy2(p + ".bak", p)

print("\n=== 2. Patching All 5 Fish Codex Tables in game12 ===")
codex_list = [
    ("fish_codex_achelous.csvc", 5775195222236934712, 594051072, 3746, 14691),
    ("fish_codex_alpheus.csvc", 1641961905539253042, 594055168, 2408, 9127),
    ("fish_codex_belisama.csvc", 5796824274819009528, 594063360, 2173, 7999),
    ("fish_codex_ceto.csvc", -7827499170503240933, 594067456, 2162, 8510),
    ("fish_codex_doris.csvc", -8597476204515797250, 594071552, 2703, 10171),
]

for name, vh, off, sc, su in codex_list:
    raw = read_orig("game12.arc", off, sc, su)
    patched = patch_csvc(raw, name)
    write_node("game12.tab", "game12.arc", vh, off, sc, patched)

print("\n=== 3. Patching hook_meta_data.csvc (All Hooks -> /diamond ONLY) ===")
conn = sqlite3.connect(r".\work\an\db\core.db")
cur = conn.cursor()
cur.execute("SELECT v_hash, parent_offset, size_c, size_u FROM core_nodes WHERE v_path = 'settings/game_data_tables/hook_meta_data.csvc'")
h_vh, h_off, h_sc, h_su = cur.fetchone()
conn.close()

raw_hooks = read_orig("game12.arc", h_off, h_sc, h_su)
patched_hooks = patch_hook_meta_diamond_only(raw_hooks)
write_node("game12.tab", "game12.arc", h_vh, h_off, h_sc, patched_hooks)

print("\n=== 4. Patching All 5 Reserves' global_trufish.blo_adf (Strict Diamond=1.0, Others=0.0, Caps=-1) ===")
tf_list = [
    ("game16.tab", "game16.arc", "achelous", 4245202897118090955, 63438848, 5908, 15980),
    ("game20.tab", "game20.arc", "alpheus", -588015160189099245, 226926592, 4885, 14028),
    ("game24.tab", "game24.arc", "belisama", 5612303823963747841, 132120576, 4800, 11332),
    ("game28.tab", "game28.arc", "ceto", -8655686045783063754, 486465536, 6882, 18596),
    ("game32.tab", "game32.arc", "doris", -5172364055990370037, 66351104, 6509, 17340),
]

for tab_n, arc_n, lbl, vh, off, sc, su in tf_list:
    raw = read_orig(arc_n, off, sc, su)
    patched = patch_trufish_strict_diamond(raw, lbl)
    write_node(tab_n, arc_n, vh, off, sc, patched)

print("\n[SUCCESS] Strict Diamond-only probabilities + /diamond hook table patched!")
