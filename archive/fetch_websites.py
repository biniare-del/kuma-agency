import csv, time, urllib.request, urllib.parse, json, os

CLIENT_ID = "r_1K9ZtkLbWZ3KLADEae"
CLIENT_SECRET = "U_rB637zWG"

INPUT_CSV = "all_clinic_targets.csv"
OUTPUT_CSV = "all_clinic_targets_with_url.csv"

def search_naver(query):
    encoded = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/local.json?query={encoded}&display=1"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            items = data.get("items", [])
            if items:
                return items[0].get("link", "")
    except Exception as e:
        print(f"  오류: {e}")
    return ""

with open(INPUT_CSV, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print(f"총 {len(rows)}개 처리 시작...")

fieldnames = list(rows[0].keys())
done = []

# 이미 처리된 것 있으면 이어서
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, encoding="utf-8-sig") as f:
        done = list(csv.DictReader(f))
    print(f"{len(done)}개 이미 완료, 이어서 시작")

processed_names = {r["기관명"] for r in done}

with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    if not done:
        w.writeheader()

    for i, row in enumerate(rows):
        if row["기관명"] in processed_names:
            continue
        if row.get("홈페이지"):
            w.writerow(row)
            continue

        query = f"{row['기관명']} {row['구']}"
        url = search_naver(query)
        row["홈페이지"] = url

        w.writerow(row)
        f.flush()

        if (i+1) % 50 == 0:
            print(f"  {i+1}/{len(rows)} 완료...")

        time.sleep(0.12)  # 네이버 API 초당 10회 제한

print("완료!")
