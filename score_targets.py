"""
영업대상 홈페이지 일괄 진단 + 영업멘트 자동 생성
────────────────────────────────────────────────
- 입력: 영업대상_전체.xlsx  (컬럼에 '병원명', '홈페이지' 필요)
- 출력: 영업대상_점검결과_v2.xlsx  (연락처 수작업 파일은 건드리지 않음)
- 홈페이지 없는 곳 / SNS만 있는 곳은 자동 제외.
- 웹 진단도구(/check/)와 동일한 개선 로직 반영:
  meta refresh 추적, HTTP 폴백, HTTPS 점검, 모바일 UA 재요청, JS렌더링 감지,
  외국어 링크 감지, robots/sitemap 확인불가 구분.
- 각 병원마다 '영업멘트'(뭐가 부족/잘못됐는지 바로 쓸 문구) 컬럼 생성.
실행:  python score_targets.py
"""
import re
import io
import json
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

INPUT = r"C:\Users\binia\Desktop\영업대상_전체.xlsx"
OUTPUT = r"C:\Users\binia\Desktop\영업대상_점검결과_v2.xlsx"

EXCLUDE_DOMAINS = ("instagram.com", "naver.com", "blog.", "kakao.com", "youtube.com", "youtu.be")

UA_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
HEADERS = {"User-Agent": UA_DESKTOP, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}

SCORE_THRESHOLD = 50

# ── 연락처(이메일·카카오) 추출 ──────────────────────────────
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
JUNK_EMAIL_DOMAINS = (
    "sentry.io", "wixpress.com", "w3.org", "example.com", "example.org", "godaddy.com",
    "schema.org", "domain.com", "email.com", "mail.com", "google.com", "gstatic.com",
    "googleapis.com", "cloudflare.com", "jquery.com", "sentry-cdn.com",
    "test.com", "site.com", "yourdomain.com", "sample.com",
)
# 플레이스홀더 예시 이메일(가짜)의 흔한 아이디 부분 — 이런 건 실제 병원 이메일 아님
JUNK_EMAIL_LOCAL = (
    "email", "yourname", "your-email", "youremail", "name", "id", "user",
    "test", "sample", "example", "abc", "info@example", "admin",
)
# pf.kakao.com 직접 링크뿐 아니라, 클릭 시 SDK가 주소를 만드는 channelPublicId,
# 옛 plus.kakao, 오픈채팅까지 잡음 (버튼만 있고 링크가 HTML에 없던 케이스 대응)
KAKAO_PATTERNS = [
    re.compile(r"pf\.kakao\.com/(_?[a-zA-Z0-9]+)"),
    re.compile(r"channelPublicId\s*[:=]\s*['\"](_?[a-zA-Z0-9]+)['\"]"),
    re.compile(r"open\.kakao\.com/(?:o/)?([a-zA-Z0-9]+)"),
    re.compile(r"plus\.kakao\.com/(?:home/)?(@[^\"'\s<>/]+)"),
]


def find_email(html):
    for e in EMAIL_RE.findall(html):
        local, domain = e.split("@")[0].lower(), e.split("@")[-1].lower()
        if any(j in domain for j in JUNK_EMAIL_DOMAINS):
            continue
        if local in JUNK_EMAIL_LOCAL:
            continue
        return e
    return None


def find_kakao(html):
    for pat in KAKAO_PATTERNS:
        m = pat.search(html)
        if m:
            return m.group(1)
    return None


# ── 접속 유틸 ────────────────────────────────────────────────
def is_real_homepage(url):
    if not isinstance(url, str) or not url.strip():
        return False
    host = urlparse(url if "://" in url else "https://" + url).netloc.lower()
    return not any(bad in host for bad in EXCLUDE_DOMAINS)


def get(url, mobile=False, timeout=10):
    """(status_code, text) 반환. 실패 시 (None, None)."""
    try:
        h = dict(HEADERS)
        if mobile:
            h["User-Agent"] = UA_MOBILE
        r = requests.get(url, headers=h, timeout=timeout, allow_redirects=True)
        return r.status_code, r.text
    except Exception:
        return None, None


def status_of(url, timeout=8):
    """존재 확인: 'ok' | 'missing'(404) | 'unknown'(실패/차단)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return "ok"
        if r.status_code == 404:
            return "missing"
        return "unknown"
    except Exception:
        return "unknown"


META_REFRESH_RE = re.compile(r"url\s*=\s*['\"]?([^'\";]+)", re.I)


def follow_meta_refresh(soup, base_url, current_url):
    tag = soup.find("meta", attrs={"http-equiv": re.compile(r"^refresh$", re.I)})
    if not tag:
        return None
    m = META_REFRESH_RE.search(tag.get("content") or "")
    if not m:
        return None
    target = urljoin(current_url, m.group(1).strip())
    return target if target != current_url else None


def looks_js_rendered(soup):
    body = soup.find("body")
    text = re.sub(r"\s+", " ", body.get_text() if body else "").strip()
    if len(text) >= 300:
        return False
    spa = soup.select_one("#root, #app, #__next, #__nuxt, [data-reactroot], [ng-app], [data-server-rendered]")
    scripts = soup.find_all("script", src=True)
    return bool(spa) or len(scripts) >= 3


# ── 항목별 채점 ──────────────────────────────────────────────
def score_meta(soup):
    score = 0
    title = soup.find("title")
    tlen = len(title.get_text(strip=True)) if title else 0
    if tlen >= 10:
        score += 35
    desc = soup.find("meta", attrs={"name": "description"})
    dlen = len(desc.get("content").strip()) if desc and desc.get("content") else 0
    if dlen >= 20:
        score += 35
    og = soup.find("meta", property=re.compile(r"^og:"))
    if og:
        score += 30
    return score, {"title": tlen, "desc": dlen, "og": bool(og)}


def score_structured_data(soup):
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    if not scripts:
        return 0, 0
    valid = 0
    for s in scripts:
        try:
            json.loads(s.get_text())
            valid += 1
        except Exception:
            pass
    if valid == 0:
        return 20, 0
    return 100, valid


def has_device_width(text):
    return bool(re.search(r"name=[\"']?viewport", text, re.I) and re.search(r"width\s*=\s*device-width", text, re.I))


def score_mobile(soup, page_url, page_text):
    vp = soup.find("meta", attrs={"name": "viewport"})
    if vp and "width=device-width" in (vp.get("content") or ""):
        return 100, "정적 viewport"
    # 기기별로 다른 페이지를 주는 사이트: 모바일 UA로 재요청 (https/http 둘 다)
    variants = [page_url]
    if page_url.startswith("https://"):
        variants.append("http://" + page_url[8:])
    elif page_url.startswith("http://"):
        variants.append("https://" + page_url[7:])
    for u in variants:
        code, txt = get(u, mobile=True)
        if code == 200 and txt and has_device_width(txt):
            return 100, "모바일 전용 페이지"
    return 0, "없음"


def score_i18n(soup):
    hreflang = soup.find_all("link", attrs={"hreflang": True})
    html_tag = soup.find("html")
    lang = html_tag.get("lang") if html_tag else None
    foreign = False
    for a in soup.find_all("a", href=True):
        s = (a.get("href", "") + " " + a.get_text()).lower()
        if re.search(r"english|japanese|chinese|日本語|中文|/en/|/en\b|/jp|/jpn|/cn\b|/zh\b|lang=(en|ja|zh)", s):
            foreign = True
            break
    score = 0
    if hreflang:
        score += 70
    if lang:
        score += 30
    return min(score, 100), {"hreflang": len(hreflang), "lang": lang or "", "foreign": foreign}


def score_images(soup):
    imgs = soup.find_all("img")
    if not imgs:
        return 50, (0, 0)
    with_alt = sum(1 for img in imgs if (img.get("alt") or "").strip())
    return round(with_alt / len(imgs) * 100), (with_alt, len(imgs))


def score_crawl_setup(page_url):
    p = urlparse(page_url)
    origin = f"{p.scheme}://{p.netloc}"
    robots = status_of(origin + "/robots.txt")
    sitemap = status_of(origin + "/sitemap.xml")

    def sub(st):
        return 50 if st in ("ok", "unknown") else 0  # 확인불가는 감점 안 함

    return sub(robots) + sub(sitemap), {"robots": robots, "sitemap": sitemap}


def score_https(page_url):
    host = urlparse(page_url).netloc
    if status_of("https://" + host + "/") == "ok":
        return 100, "지원"
    if status_of("http://" + host + "/") == "ok":
        return 0, "미지원"
    return 50, "확인불가"


# ── 영업멘트 생성 ────────────────────────────────────────────
def build_pitch(parts, info):
    """뭐가 부족/잘못됐는지 영업에 바로 쓸 문구 (약한 항목 위주)."""
    msgs = []
    if parts["HTTPS"] == 0:
        msgs.append("보안 연결(HTTPS) 없음 → 크롬에 '주의 요함' 경고가 뜨고 검색 순위에도 불리")
    if parts["구조화데이터"] < 50:
        msgs.append("구조화 데이터(JSON-LD) 없음 → ChatGPT·네이버AI가 병원 정보를 못 읽음(AI검색 미노출)")
    if parts["모바일대응"] == 0:
        msgs.append("모바일 대응 안 됨 → 폰에서 화면이 깨지거나 축소됨")
    if parts["다국어대응"] < 70:
        if info["i18n"]["foreign"] and info["i18n"]["hreflang"] == 0:
            msgs.append("외국어 페이지는 있으나 hreflang 미설정 → 검색엔진이 언어판으로 인식 못 함")
        else:
            msgs.append("해외환자 대응 없음 → 다국어/hreflang 미설정")
    if parts["메타데이터"] < 70:
        d = info["meta"]
        lack = []
        if d["title"] < 10:
            lack.append("제목")
        if d["desc"] < 20:
            lack.append("설명")
        if not d["og"]:
            lack.append("공유(OG)")
        msgs.append(f"검색결과 노출 태그 부실({'/'.join(lack)} 없음) → 클릭 유도 약함")
    if parts["크롤링설정"] < 50 and info["crawl"]["sitemap"] == "missing":
        msgs.append("sitemap.xml 없음 → 검색엔진이 전체 페이지를 못 찾음")
    if parts["이미지alt"] < 70:
        wa, tot = info["img"]
        msgs.append(f"이미지 alt 텍스트 부족({wa}/{tot}) → 이미지 검색·접근성 손해")
    if not msgs:
        return "큰 약점 적음 — 이미 잘 되어있는 편, 영업 우선순위 낮음"
    return " / ".join(msgs)


# ── 한 사이트 종합 ───────────────────────────────────────────
def score_site(url):
    if not url.startswith("http"):
        url = "https://" + url
    code, html = get(url)
    if not html:  # https 실패 → http 재시도
        if url.startswith("https://"):
            url = "http://" + url[8:]
            code, html = get(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # meta refresh 스플래시 추적 (최대 2회)
    for _ in range(2):
        target = follow_meta_refresh(soup, url, url)
        if not target:
            break
        c2, h2 = get(target)
        if not h2:
            break
        url, html, soup = target, h2, BeautifulSoup(h2, "html.parser")

    email = find_email(html)
    kakao = find_kakao(html)

    if looks_js_rendered(soup):
        return {"총점": "", "상태": "수동확인(JS렌더링)", "영업멘트": "JS로 화면을 그리는 사이트 — 자동진단 부정확, 수동 확인 필요",
                "이메일": email or "", "카카오": kakao or "",
                "메타데이터": "", "구조화데이터": "", "모바일대응": "", "다국어대응": "", "이미지alt": "", "크롤링설정": "", "HTTPS": ""}

    m_score, m_info = score_meta(soup)
    sd_score, _ = score_structured_data(soup)
    mob_score, _ = score_mobile(soup, url, html)
    i18_score, i18_info = score_i18n(soup)
    img_score, img_info = score_images(soup)
    crawl_score, crawl_info = score_crawl_setup(url)
    https_score, _ = score_https(url)

    parts = {
        "메타데이터": m_score, "구조화데이터": sd_score, "모바일대응": mob_score,
        "다국어대응": i18_score, "이미지alt": img_score, "크롤링설정": crawl_score, "HTTPS": https_score,
    }
    info = {"meta": m_info, "i18n": i18_info, "img": img_info, "crawl": crawl_info}
    total = round(sum(parts.values()) / len(parts))
    pitch = build_pitch(parts, info)

    row = {"총점": total, "상태": "정상", "영업멘트": pitch, "이메일": email or "", "카카오": kakao or ""}
    row.update(parts)
    return row


def main():
    df = pd.read_excel(INPUT)
    before = len(df)
    df = df[df["홈페이지"].apply(is_real_homepage)].reset_index(drop=True)
    print(f"홈페이지 없음/SNS만 제외: {before} -> {len(df)}개")

    results, failed = [], 0
    total_n = len(df)
    for i, row in df.iterrows():
        url = row["홈페이지"]
        print(f"[{i+1}/{total_n}] {row.get('병원명','?')} - {url}", end=" ", flush=True)
        try:
            res = score_site(url)
        except Exception as e:
            res = None
            print(f"오류: {e}", end=" ")
        if res is None:
            failed += 1
            print("-> 접속 실패")
            continue
        print(f"-> {res['총점']}점 [{res['상태']}]")
        row_data = row.to_dict()
        row_data.update(res)
        results.append(row_data)

        # 30개마다 중간 저장 (중간에 끊겨도 유지)
        if len(results) % 30 == 0:
            pd.DataFrame(results).to_excel(OUTPUT, index=False)
        time.sleep(0.2)

    result_df = pd.DataFrame(results)
    # 정렬: 정상 항목을 총점 낮은 순(=영업 우선순위 높은 순)으로
    normal = result_df[result_df["상태"] == "정상"].copy()
    normal["_t"] = pd.to_numeric(normal["총점"], errors="coerce")
    manual = result_df[result_df["상태"] != "정상"]
    ordered = pd.concat([normal.sort_values("_t").drop(columns=["_t"]), manual], ignore_index=True)

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        ordered.to_excel(writer, sheet_name="채점결과", index=False)
        low = normal[normal["_t"] <= SCORE_THRESHOLD].sort_values("_t").drop(columns=["_t"])
        low.to_excel(writer, sheet_name=f"{SCORE_THRESHOLD}점이하(우선타겟)", index=False)

    print(f"\n완료: 채점 {len(result_df)}개 / 접속실패 {failed}개 / {SCORE_THRESHOLD}점이하 {len(low)}개")
    print(f"저장: {OUTPUT}")


if __name__ == "__main__":
    main()
