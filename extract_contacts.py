import re
import time
import requests
import pandas as pd

INPUT = r"C:\Users\binia\Desktop\영업대상_점검결과.xlsx"
INPUT_SHEET = "50점이하"
OUTPUT = r"C:\Users\binia\Desktop\영업대상_연락처.xlsx"

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
KAKAO_RE = re.compile(r"pf\.kakao\.com/(_?[a-zA-Z0-9]+)")

# 실제 병원 이메일이 아닌 트래킹/시스템 노이즈 도메인 제외
JUNK_DOMAINS = (
    "sentry.io", "sentry.wixpress.com", "sentry-next.wixpress.com",
    "wixpress.com", "w3.org", "example.com", "godaddy.com",
    "schema.org", "domain.com", "email.com", "google.com",
    "youremail.com", "yourname.com", "gstatic.com", "googleapis.com",
    "cloudflare.com", "jquery.com",
)

CONTACT_PATHS = ["", "contact", "about", "location", "oshineungil", "info"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}


def clean_emails(text):
    found = set()
    for e in EMAIL_RE.findall(text):
        domain = e.split("@")[-1].lower()
        if any(j in domain for j in JUNK_DOMAINS):
            continue
        found.add(e)
    return found


def fetch(url, timeout=8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None


def extract_contacts(homepage):
    if not isinstance(homepage, str) or not homepage.strip():
        return None, None

    base = homepage.strip().rstrip("/")
    if not base.startswith("http"):
        base = "https://" + base

    emails = set()
    kakao_id = None

    html = fetch(base)
    if html:
        emails |= clean_emails(html)
        m = KAKAO_RE.search(html)
        if m:
            kakao_id = m.group(1)

    if not emails and not kakao_id:
        for path in CONTACT_PATHS[1:]:
            html = fetch(f"{base}/{path}")
            if not html:
                continue
            emails |= clean_emails(html)
            if not kakao_id:
                m = KAKAO_RE.search(html)
                if m:
                    kakao_id = m.group(1)
            if emails or kakao_id:
                break

    email = sorted(emails)[0] if emails else None
    return email, kakao_id


def main():
    df = pd.read_excel(INPUT, sheet_name=INPUT_SHEET)
    df["이메일"] = ""
    df["카카오"] = ""

    total = len(df)
    got_email = 0
    got_kakao = 0
    got_neither = 0

    for i, row in df.iterrows():
        homepage = row.get("홈페이지")
        print(f"[{i+1}/{total}] {row.get('병원명')}", end=" ")
        email, kakao_id = extract_contacts(homepage)

        if email:
            df.at[i, "이메일"] = email
            got_email += 1
        if kakao_id:
            df.at[i, "카카오"] = kakao_id
            got_kakao += 1
        if not email and not kakao_id:
            got_neither += 1

        print(f"-> email={email} kakao={kakao_id}")
        time.sleep(0.2)

        if (i + 1) % 50 == 0:
            df.to_excel(OUTPUT, index=False)
            print(f"  중간 저장 ({i+1}/{total})")

    df.to_excel(OUTPUT, index=False)
    print(f"\n완료: 총 {total}개 중 이메일 {got_email}건 / 카카오 {got_kakao}건 확보, 둘 다 없음 {got_neither}건")
    print(f"저장: {OUTPUT}")


if __name__ == "__main__":
    main()
