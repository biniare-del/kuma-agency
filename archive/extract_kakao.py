import csv, time, urllib.request, re, os

INPUT_CSV = "all_clinic_targets_final_v3.csv"
OUTPUT_CSV = "all_clinic_targets_final_v4.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DreamAgencyBot/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

KAKAO_RE = re.compile(r'https?://pf\.kakao\.com/[a-zA-Z0-9_\-]+')


def fetch(url, timeout=8):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, errors="replace")


def extract_kakao(url):
    if not url or not url.startswith("http"):
        url = "https://" + url if url else ""
    if not url:
        return ""
    try:
        html = fetch(url)
        found = KAKAO_RE.findall(html)
        if found:
            return found[0]
    except Exception:
        pass
    return ""


# --- main ---
with open(INPUT_CSV, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

if "카카오채널" not in fieldnames:
    fieldnames.append("카카오채널")

done = []
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, encoding="utf-8-sig") as f:
        done = list(csv.DictReader(f))
    print(f"{len(done)}개 이미 완료, 이어서 시작")

processed = {r["기관명"] for r in done}
print(f"총 {len(rows)}개 처리 시작...")

with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    if not done:
        w.writeheader()

    for i, row in enumerate(rows):
        if row["기관명"] in processed:
            continue

        url = row.get("홈페이지", "").strip()
        유형 = row.get("홈페이지유형", "")

        if 유형 == "홈페이지" and not row.get("카카오채널", "").strip():
            row["카카오채널"] = extract_kakao(url)
            time.sleep(0.3)
        else:
            row["카카오채널"] = row.get("카카오채널", "")

        w.writerow(row)
        f.flush()

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(rows)} 완료...")

print("완료!")
