import os
import shutil
import struct
import zlib

ARCHIVE_DIR = (
    "C:/Program Files (x86)/Steam/steamapps/common/"
    "Call of the Wild The Angler/archives_win64/initial"
)

log_lines = []
def log(msg):
    print(msg, flush=True)
    log_lines.append(str(msg))

def backup_file(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        log("Creating backup: " + os.path.basename(bak))
        shutil.copy2(path, bak)
    else:
        log("Backup exists: " + os.path.basename(bak))

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
        raise RuntimeError("v_hash not found in " + tab_n)

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

    log(f"  [OK] Patched {tab_n}: size_c {orig_sc} -> {new_sc}")

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

        p[c_idx["MAX_Score_Juvenile"]] = "0"
        p[c_idx["MAX_Score_Bronze"]] = "0"
        p[c_idx["MAX_Score_Silver"]] = "0"
        p[c_idx["MAX_Score_Gold"]] = "0"
        p[c_idx["MAX_Score_Diamond"]] = "100"

        g_scale = p[c_idx["MAX_Scale_Gold"]]
        p[c_idx["Scale_MIN"]] = g_scale
        p[c_idx["MAX_Scale_Juvenile"]] = g_scale
        p[c_idx["MAX_Scale_Bronze"]] = g_scale
        p[c_idx["MAX_Scale_Silver"]] = g_scale

        g_kg = p[c_idx["MAX_KG_Gold"]]
        p[c_idx["KG_MIN"]] = g_kg
        p[c_idx["MAX_KG_Juvenile"]] = g_kg
        p[c_idx["MAX_KG_Bronze"]] = g_kg
        p[c_idx["MAX_KG_Silver"]] = g_kg

        out.append(",".join(p) + end)
        cnt += 1

    log(f"  Modified {cnt} species in {fname}")
    return "".join(out).encode("utf-8")

def patch_trufish(raw_bytes, fname):
    data = bytearray(raw_bytes)
    found = 0
    for off in range(0, len(data) - 128, 4):
        db, dd, dg, ds = struct.unpack_from("<ffff", data, off)
        pb, pd, pg, pj, ps = struct.unpack_from(
            "<fffff", data, off + 0x3C
        )
        cond1 = (10.0 <= db <= 30.0 and 0.01 <= dd <= 2.0)
        cond2 = (pb == 1.0 and 0.001 <= pd <= 0.5)
        if cond1 and cond2:
            log(f"  Found TruFish struct in {fname} at {hex(off)}")
            struct.pack_into("<ffff", data, off, 0.0, 100.0, 0.0, 0.0)
            struct.pack_into(
                "<fffff", data, off + 0x3C, 0.0, 1.0, 0.0, 0.0, 0.0
            )
            struct.pack_into(
                "<iiiii", data, off + 0x58, 0, -1, 0, 0, 0
            )
            found += 1
    if found == 0:
        log(f"  [WARN] Pattern not found in {fname}")
    return bytes(data)

try:
    log("=== Step 1: Patching Fish Codex Tables in game12 ===")
    codex_list = [
        ("fish_codex_achelous.csvc", 5775195222236934712, 594051072, 3746, 14691),
        ("fish_codex_alpheus.csvc", 1641961905539253042, 594055168, 2408, 9127),
        ("fish_codex_belisama.csvc", 5796824274819009528, 594063360, 2173, 7999),
        ("fish_codex_ceto.csvc", -7827499170503240933, 594067456, 2162, 8510),
        ("fish_codex_doris.csvc", -8597476204515797250, 594071552, 2703, 10171),
    ]

    os.makedirs("extracted", exist_ok=True)
    for name, vh, off, sc, su in codex_list:
        raw = read_orig("game12.arc", off, sc, su)
        patched = patch_csvc(raw, name)
        out_p = os.path.join("extracted", "patched_" + name)
        with open(out_p, "wb") as f:
            f.write(patched)
        write_node("game12.tab", "game12.arc", vh, off, sc, patched)

    log("\n=== Step 2: Patching Reserve global_trufish.blo_adf ===")
    tf_list = [
        ("game16.tab", "game16.arc", "achelous", 4245202897118090955, 63438848, 5908, 15980),
        ("game20.tab", "game20.arc", "alpheus", -588015160189099245, 226926592, 4885, 14028),
        ("game24.tab", "game24.arc", "belisama", 5612303823963747841, 132120576, 4800, 11332),
        ("game28.tab", "game28.arc", "ceto", -8655686045783063754, 486465536, 6882, 18596),
    ]

    for tab_n, arc_n, lbl, vh, off, sc, su in tf_list:
        raw = read_orig(arc_n, off, sc, su)
        patched = patch_trufish(raw, lbl)
        write_node(tab_n, arc_n, vh, off, sc, patched)

    log("\nAll archives patched! Launch the game and test!")
except Exception as e:
    import traceback
    log("ERROR: " + traceback.format_exc())

with open("patch_log.txt", "w", encoding="utf-8") as lf:
    lf.write("\n".join(log_lines))
