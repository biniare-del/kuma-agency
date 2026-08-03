import csv, time, urllib.request, re, os

INPUT_CSV = "all_clinic_targets_scored.csv"
OUTPUT_CSV = "all_clinic_targets_final.csv"

SNS_DOMAINS = ["instagram.com", "blog.naver.com", "facebook.com", "youtube.com", "twitter.com", "tiktok.com", "smartplace.naver.com", "place.naver.com"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DreamAgencyBot/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
EXCLUDE_EMAIL = re.compile(r'(example|test|dummy|noreply|no-reply|webmaster|admin|@sentry|@example|\.png|\.jpg|\.gif)', re.I)


def is_sns(url):
    if not url:
        return False
    return any(d in url for d in SNS_DOMAINS)


def fetch(url, timeout=8):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, errors="replace")


def extract_email(url):
    if not url or is_sns(url):
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html = fetch(url)
        # mailto: 우선
        mailto = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html)
        for e in mailto:
            if not EXCLUDE_EMAIL.search(e):
                return e
        # 텍스트에서 이메일 패턴
        found = EMAIL_RE.findall(html)
        for e in found:
            if not EXCLUDE_EMAIL.search(e):
                return e
    except Exception:
        pass
    return ""


# --- main ---
with open(INPUT_CSV, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

if "이메일" not in fieldnames:
    fieldnames.append("이메일")
if "홈페이지유형" not in fieldnames:
    fieldnames.append("홈페이지유형")
if "영업등급" not in fieldnames:
    fieldnames.append("영업등급")

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
        memo = row.get("진단_메모", "")
        score = row.get("점수_종합", "")

        # 홈페이지 유형 분류
        if not url:
            row["홈페이지유형"] = "없음"
        elif is_sns(url):
            row["홈페이지유형"] = "SNS"
        elif "접근불가" in memo:
            row["홈페이지유형"] = "접근불가"
        else:
            row["홈페이지유형"] = "홈페이지"

        # 영업 등급
        유형 = row["홈페이지유형"]
        if 유형 in ("없음", "SNS"):
            row["영업등급"] = "A"
        elif 유형 == "접근불가":
            row["영업등급"] = "B"
        elif score == "" or (score.isdigit() and int(score) <= 50):
            row["영업등급"] = "C"
        else:
            row["영업등급"] = "D"

        # 이메일 추출 (홈페이지 있는 경우만)
        existing_email = row.get("이메일", "").strip()
        if not existing_email and 유형 == "홈페이지":
            row["이메일"] = extract_email(url)
            time.sleep(0.3)
        else:
            row["이메일"] = existing_email

        w.writerow(row)
        f.flush()

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(rows)} 완료...")

print("완료!")
