import os
import sqlite3
import glob

# Adjust path if your folder is named 'work/am' or 'work/an'
work_dirs = glob.glob("work/*")
print("Found work directories:", work_dirs)

db_files = []
for d in work_dirs:
    for root, dirs, files in os.walk(d):
        for f in files:
            if f.endswith(".db") or f.endswith(".sqlite") or "vfs" in f.lower():
                db_files.append(os.path.join(root, f))

print("Found DB files:", db_files)

for db_path in db_files:
    if not os.path.isfile(db_path):
        continue
    print(f"\n--- Inspecting {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 1. List all tables in the database
        cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        for t_name, t_sql in tables:
            print(f"\nTable: {t_name}")
            print(f"Schema: {t_sql}")
            cur.execute(f"SELECT COUNT(*) FROM {t_name}")
            print(f"Row count: {cur.fetchone()[0]}")
            
            # 2. Search for fish / rank / diamond / weight strings in text/blob columns
            cur.execute(f"PRAGMA table_info({t_name})")
            cols = [c[1] for c in cur.fetchall()]
            for col in cols:
                try:
                    query = f"SELECT * FROM {t_name} WHERE CAST({col} AS TEXT) LIKE '%fish%' OR CAST({col} AS TEXT) LIKE '%diamond%' OR CAST({col} AS TEXT) LIKE '%rank%' OR CAST({col} AS TEXT) LIKE '%weight%' LIMIT 15"
                    cur.execute(query)
                    matches = cur.fetchall()
                    if matches:
                        print(f"  Matches in {t_name}.{col} (showing up to 15):")
                        for m in matches:
                            # Truncate long binary blobs for clean printing
                            clean_m = [str(x)[:120] if isinstance(x, (bytes, str)) else x for x in m]
                            print("   ", clean_m)
                except Exception:
                    pass
        conn.close()
    except Exception as e:
        print(f"Error reading {db_path}: {e}")