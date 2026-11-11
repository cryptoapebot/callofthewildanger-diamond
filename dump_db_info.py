import os
import sqlite3

output_lines = []
def log(msg):
    print(msg)
    output_lines.append(str(msg))

log("=== Scanning C:/projects/deca/deca_gui-b636/ ===")
for root, dirs, files in os.walk("."):
    for f in files:
        fpath = os.path.join(root, f)
        fsize = os.path.getsize(fpath)
        # Log all non-cache files or potential SQLite files
        if "__CACHE__" not in fpath:
            log(f"File: {fpath} ({fsize:,} bytes)")
        
        # Check if file is an SQLite3 database by reading the first 16 bytes
        if fsize > 100 and "__CACHE__" not in fpath:
            try:
                with open(fpath, "rb") as bf:
                    header = bf.read(16)
                if header.startswith(b"SQLite format 3"):
                    log(f"\n>>> FOUND SQLITE DB: {fpath} <<<")
                    conn = sqlite3.connect(fpath)
                    cur = conn.cursor()
                    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
                    for t_name, t_sql in cur.fetchall():
                        cur.execute(f"SELECT COUNT(*) FROM {t_name}")
                        cnt = cur.fetchone()[0]
                        log(f"  Table: {t_name} ({cnt} rows) -> {t_sql}")
                        
                        # Sample first 5 rows
                        cur.execute(f"SELECT * FROM {t_name} LIMIT 5")
                        for r in cur.fetchall():
                            clean_r = [str(x)[:100] if isinstance(x, (bytes, str)) else x for x in r]
                            log(f"    Sample: {clean_r}")
                            
                        # Search for fish/rank/diamond/weight/score
                        cur.execute(f"PRAGMA table_info({t_name})")
                        cols = [c[1] for c in cur.fetchall()]
                        for col in cols:
                            for kw in ["fish", "rank", "diamond", "weight", "trophy", "species", "gdcc"]:
                                try:
                                    cur.execute(f"SELECT * FROM {t_name} WHERE CAST({col} AS TEXT) LIKE '%{kw}%' LIMIT 10")
                                    m = cur.fetchall()
                                    if m:
                                        log(f"    Matches for '{kw}' in {t_name}.{col}:")
                                        for row in m:
                                            clean_row = [str(x)[:120] if isinstance(x, (bytes, str)) else x for x in row]
                                            log(f"      {clean_row}")
                                except Exception:
                                    pass
                    conn.close()
            except Exception as e:
                log(f"Error checking {fpath}: {e}")

with open("deca_report.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(output_lines))
print("\nSaved full output to deca_report.txt!")