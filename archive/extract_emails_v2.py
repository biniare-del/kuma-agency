"""
이메일 재수집 스크립트 (v2) — 로컬 클로드코드(또는 일반 파이썬 환경, 인터넷 제한 없는 곳)에서 실행

기존 extract_emails.py는 병원 홈페이지 첫 화면(루트 URL)만 훑어서 이메일 적중률이 낮았음(748/3,744, 약 20%).
이 버전은 첫 화면에서 이메일을 못 찾으면 "오시는길/문의/병원소개" 류 서브페이지까지 추가로 확인함.

대상: all_clinic_targets_final_v2.csv 중 홈페이지유형="홈페이지"이면서 이메일이 비어있는 행만.
(홈페이지유형="없음"/"SNS"는 애초에 이메일을 실을 소스가 없는 걸로 확인됐으므로 이 스크립트에서 건드리지 않음 — 그대로 통과)

사용법:
  python3 extract_emails_v2.py
  - 중간에 멈춰도 다시 실행하면 이어서 진행됨 (all_clinic_targets_final_v3.csv 존재 여부로 판단)
  - 완료 후 all_clinic_targets_final_v3.csv 가 최종 결과물
"""

import csv, time, os, re
import urllib.request
from urllib.parse import urljoin
from html.parser import HTMLParser

INPUT_CSV = "all_clinic_targets_final_v2.csv"
OUTPUT_CSV = "all_clinic_targets_final_v3.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DreamAgencyBot/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
EXCLUDE_EMAIL = re.compile(
    r'(example|test|dummy|noreply|no-reply|webmaster|admin|@sentry|@example|'
    r'\.png|\.jpg|\.jpeg|\.gif|\.svg|\.css|\.js|sentry\.io|wixpress|godaddy|@2x|@3x)',
    re.I,
)

# 서브페이지 후보 — 흔한 경로 패턴 + 링크 텍스트/href에 이 키워드가 있으면 우선 방문
COMMON_PATHS = ["/contact", "/about", "/info", "/company", "/location", "/notice", "/qna", "/board"]
CONTACT_KEYWORDS = [
    "오시는길", "오시는 길", "찾아오시는", "contact", "문의", "병원소개",
    "인사말", "진료안내", "이용안내", "고객센터", "qna", "고객문의", "about",
]


def fetch(url, timeout=8):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, errors="replace")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def find_email_in_html(html):
    mailto = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html)
    for e in mailto:
        if not EXCLUDE_EMAIL.search(e):
            return e
    for e in EMAIL_RE.findall(html):
        if not EXCLUDE_EMAIL.search(e):
            return e
    return None


def guess_subpages(base_url, html):
    candidates = []
    seen = set()

    for p in COMMON_PATHS:
        u = urljoin(base_url, p)
        if u not in seen:
            seen.add(u)
            candidates.append(u)

    parser = LinkParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    for href in parser.links:
        low = href.lower()
        if any(k.lower() in low for k in CONTACT_KEYWORDS):
            u = urljoin(base_url, href)
            if u not in seen and u.startswith(("http://", "https://")):
                seen.add(u)
                candidates.append(u)

    return candidates[:6]  # 사이트당 최대 6개 서브페이지만 시도 (과도한 요청 방지)


def extract_email_deep(url):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html = fetch(url)
    except Exception:
        return ""

    email = find_email_in_html(html)
    if email:
        return email

    for sub_url in guess_subpages(url, html):
        try:
            time.sleep(0.2)
            sub_html = fetch(sub_url, timeout=6)
        except Exception:
            continue
        email = find_email_in_html(sub_html)
        if email:
            return email

    return ""


# --- main ---
with open(INPUT_CSV, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

done = []
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, encoding="utf-8-sig") as f:
        done = list(csv.DictReader(f))
    print(f"{len(done)}개 이미 완료, 이어서 시작")

processed = {r["기관명"] for r in done}

targets = [
    r for r in rows
    if r.get("홈페이지유형") == "홈페이지" and not r.get("이메일", "").strip()
]
target_ids = {id(r) for r in targets}
print(f"재수집 대상(홈페이지 있음 + 이메일 없음): {len(targets)}개")

with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    if not done:
        w.writeheader()
        # 재수집 대상이 아닌 행(이미 이메일 있음/없음·SNS유형)은 그대로 먼저 다 써둠
        for r in rows:
            if id(r) not in target_ids:
                w.writerow(r)

    for i, row in enumerate(targets):
        if row["기관명"] in processed:
            continue

        url = row.get("홈페이지", "").strip()
        email = extract_email_deep(url) if url else ""
        if email:
            row["이메일"] = email

        w.writerow(row)
        f.flush()

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(targets)} 완료...")

        time.sleep(0.3)

print("완료! 결과: all_clinic_targets_final_v3.csv")
