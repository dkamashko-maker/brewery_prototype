"""Load the DataVest Brew v2 synthetic dataset into PostgreSQL.
Usage: pip install psycopg[binary]; python load_to_postgres.py "postgresql://user:pass@host/db" [--lite]
"""
import json, sys, os, psycopg
HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["site", "users", "vessels", "devices", "tags", "gateway", "tech_cards", "detergents", "raw_material_archive", "batches",
         "vessel_occupancy", "raw_material_lots", "events", "cip_records", "yeast_generations", "lab_results", "micro_tests",
         "tasting_panels", "packaging_releases", "quality_documents", "offset_records", "accuracy_checks", "alerts",
         "production_tasks", "excise_declarations", "forecasts", "assistant_answers"]
def main(dsn, lite):
    with psycopg.connect(dsn) as con, con.cursor() as cur:
        cur.execute(open(os.path.join(HERE, "schema.sql")).read())
        for name in ORDER:
            rows = json.load(open(os.path.join(HERE, "json", f"{name}.json")))
            rows = rows if isinstance(rows, list) else [rows]
            cols = list(rows[0].keys())
            sql = f'INSERT INTO {name} ({",".join(chr(34)+c+chr(34) for c in cols)}) VALUES ({",".join(["%s"]*len(cols))})'
            cur.executemany(sql, [[json.dumps(r[c]) if isinstance(r[c], (dict, list)) else r[c] for c in cols] for r in rows])
        f = "readings_demo_lite.csv" if lite else "readings_15min.csv"
        with open(os.path.join(HERE, "timeseries", f)) as fh, cur.copy("COPY readings FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')") as cp:
            for line in fh: cp.write(line)
        con.commit()
if __name__ == "__main__":
    main(sys.argv[1], "--lite" in sys.argv)
