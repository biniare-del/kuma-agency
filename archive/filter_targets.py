import csv

INPUT_CSV = "all_clinic_targets_with_url.csv"
OUT_NO_URL = "targets_no_website.csv"
OUT_HAS_URL = "targets_has_website.csv"

with open(INPUT_CSV, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

no_url = [r for r in rows if not r.get("홈페이지", "").strip()]
has_url = [r for r in rows if r.get("홈페이지", "").strip()]

def write(path, data):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(data)

write(OUT_NO_URL, no_url)
write(OUT_HAS_URL, has_url)

print(f"홈페이지 없음: {len(no_url)}개 → {OUT_NO_URL}")
print(f"홈페이지 있음: {len(has_url)}개 → {OUT_HAS_URL}")
