import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse

INPUT = r"C:\Users\binia\Desktop\영업대상_전체.xlsx"
OUTPUT = r"C:\Users\binia\Desktop\영업대상_점검결과.xlsx"

EXCLUDE_DOMAINS = ("instagram.com", "naver.com", "blog.", "kakao.com", "youtube.com", "youtu.be")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

SCORE_THRESHOLD = 50


def is_real_homepage(url):
    if not isinstance(url, str) or not url.strip():
        return False
    host = urlparse(url if "://" in url else "https://" + url).netloc.lower()
    return not any(bad in host for bad in EXCLUDE_DOMAINS)


def fetch(url, timeout=8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None


def fetch_ok(url, timeout=6):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def score_meta(soup):
    score = 0
    title = soup.find("title")
    if title and len(title.get_text(strip=True)) >= 10:
        score += 35
    desc = soup.find("meta", attrs={"name": "description"})
    if desc and desc.get("content") and len(desc.get("content").strip()) >= 20:
        score += 35
    og = soup.find("meta", property=re.compile(r"^og:"))
    if og:
        score += 30
    return score


def score_structured_data(soup):
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    if not scripts:
        return 0
    import json
    valid = 0
    for s in scripts:
        try:
            json.loads(s.get_text())
            valid += 1
        except Exception:
            pass
    if valid == 0:
        return 20
    return 100


def score_mobile(soup):
    vp = soup.find("meta", attrs={"name": "viewport"})
    if vp and "width=device-width" in (vp.get("content") or ""):
        return 100
    return 0


def score_i18n(soup):
    score = 0
    if soup.find_all("link", attrs={"hreflang": True}):
        score += 70
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        score += 30
    return min(score, 100)


def score_images(soup):
    imgs = soup.find_all("img")
    if not imgs:
        return 50
    with_alt = sum(1 for img in imgs if (img.get("alt") or "").strip())
    return round(with_alt / len(imgs) * 100)


def score_crawl_setup(base_url):
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    score = 0
    if fetch_ok(origin + "/robots.txt"):
        score += 50
    if fetch_ok(origin + "/sitemap.xml"):
        score += 50
    return score


def score_site(url):
    if not url.startswith("http"):
        url = "https://" + url
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    parts = {
        "메타데이터": score_meta(soup),
        "구조화데이터": score_structured_data(soup),
        "모바일대응": score_mobile(soup),
        "다국어대응": score_i18n(soup),
        "이미지alt": score_images(soup),
        "크롤링설정": score_crawl_setup(url),
    }
    total = round(sum(parts.values()) / len(parts))
    return total, parts


def main():
    df = pd.read_excel(INPUT)

    before = len(df)
    df = df[df["홈페이지"].apply(is_real_homepage)].reset_index(drop=True)
    print(f"제외 필터 적용: {before}개 -> {len(df)}개 (인스타/네이버/블로그/카카오/유튜브 제외)")

    results = []
    total_n = len(df)
    for i, row in df.iterrows():
        url = row["홈페이지"]
        print(f"[{i+1}/{total_n}] {row['병원명']} - {url}", end=" ")
        try:
            res = score_site(url)
        except Exception as e:
            res = None
            print(f"오류: {e}")
        if res is None:
            print("-> 접속 실패")
            continue
        total, parts = res
        print(f"-> {total}점")
        row_data = row.to_dict()
        row_data["총점"] = total
        for k, v in parts.items():
            row_data[k] = v
        results.append(row_data)
        time.sleep(0.2)

    result_df = pd.DataFrame(results)
    low_df = result_df[result_df["총점"] <= SCORE_THRESHOLD].sort_values("총점")

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        low_df.to_excel(writer, sheet_name=f"{SCORE_THRESHOLD}점이하", index=False)
        result_df.sort_values("총점").to_excel(writer, sheet_name="전체채점결과", index=False)

    print(f"\n완료: 채점 성공 {len(result_df)}개 중 {SCORE_THRESHOLD}점 이하 {len(low_df)}개")
    print(f"저장: {OUTPUT}")


if __name__ == "__main__":
    main()
