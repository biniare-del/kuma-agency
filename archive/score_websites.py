import csv, time, urllib.request, urllib.error, json, os, re
from html.parser import HTMLParser

INPUT_CSV = "all_clinic_targets_with_url.csv"
OUTPUT_CSV = "all_clinic_targets_scored.csv"

SCORE_COLS = ["점수_메타데이터", "점수_구조화데이터", "점수_모바일", "점수_다국어", "점수_이미지alt", "점수_크롤링설정", "점수_종합", "진단_메모"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DreamAgencyBot/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def fetch(url, timeout=8):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        charset = "utf-8"
        ct = r.headers.get_content_charset()
        if ct:
            charset = ct
        return r.read().decode(charset, errors="replace")


class SimpleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.metas = {}       # name/property -> content
        self.links = []       # list of {rel, hreflang}
        self.scripts_ldjson = []
        self.imgs = []        # list of alt values (or None)
        self.lang = None
        self._in_script = False
        self._cur_script_type = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs.get("name", attrs.get("property", ""))
            content = attrs.get("content", "")
            if name:
                self.metas[name.lower()] = content
        elif tag == "link":
            self.links.append({"rel": attrs.get("rel", ""), "hreflang": attrs.get("hreflang", "")})
        elif tag == "script":
            t = attrs.get("type", "")
            self._cur_script_type = t
            self._in_script = True
            self._script_buf = ""
        elif tag == "img":
            self.imgs.append(attrs.get("alt", None))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            if self._cur_script_type == "application/ld+json":
                self.scripts_ldjson.append(self._script_buf)
            self._in_script = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_script:
            self._script_buf += data


def score_meta(p):
    score, notes = 0, []
    if len(p.title.strip()) >= 10:
        score += 35
    else:
        notes.append("title 태그 미흡")
    desc = p.metas.get("description", "")
    if len(desc.strip()) >= 20:
        score += 35
    else:
        notes.append("meta description 없음/짧음")
    if any(k.startswith("og:") for k in p.metas):
        score += 30
    else:
        notes.append("Open Graph 없음")
    return score, notes


def score_structured(p):
    if not p.scripts_ldjson:
        return 0, ["JSON-LD 없음"]
    valid = 0
    for s in p.scripts_ldjson:
        try:
            json.loads(s)
            valid += 1
        except Exception:
            pass
    if valid == 0:
        return 20, ["JSON-LD 형식 오류"]
    return 100, []


def score_mobile(p):
    vp = p.metas.get("viewport", "")
    if "width=device-width" in vp:
        return 100, []
    return 0, ["모바일 viewport 없음"]


def score_i18n(p):
    score, notes = 0, []
    hreflang = [l for l in p.links if l.get("hreflang")]
    if hreflang:
        score += 70
    else:
        notes.append("hreflang 없음")
    if p.lang:
        score += 30
    else:
        notes.append("html lang 속성 없음")
    return min(score, 100), notes


def score_images(p):
    imgs = p.imgs
    if not imgs:
        return 50, ["이미지 없음"]
    with_alt = sum(1 for a in imgs if a and a.strip())
    ratio = with_alt / len(imgs)
    score = round(ratio * 100)
    notes = [] if score >= 70 else [f"이미지 {len(imgs)}개 중 alt {with_alt}개"]
    return score, notes


def check_file(origin, path):
    try:
        fetch(origin + path, timeout=5)
        return True
    except Exception:
        return False


def score_crawl(origin):
    score, notes = 0, []
    if check_file(origin, "/robots.txt"):
        score += 50
    else:
        notes.append("robots.txt 없음")
    if check_file(origin, "/sitemap.xml"):
        score += 50
    else:
        notes.append("sitemap.xml 없음")
    return score, notes


def diagnose(url):
    if not url:
        return None
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html = fetch(url)
    except Exception as e:
        return {"error": str(e)[:80]}

    p = SimpleParser()
    try:
        p.feed(html)
    except Exception:
        pass

    origin = re.match(r"https?://[^/]+", url)
    origin = origin.group(0) if origin else url

    s_meta, n_meta = score_meta(p)
    s_struct, n_struct = score_structured(p)
    s_mob, n_mob = score_mobile(p)
    s_i18n, n_i18n = score_i18n(p)
    s_img, n_img = score_images(p)
    s_crawl, n_crawl = score_crawl(origin)

    total = round((s_meta + s_struct + s_mob + s_i18n + s_img + s_crawl) / 6)
    all_notes = n_meta + n_struct + n_mob + n_i18n + n_img + n_crawl

    return {
        "점수_메타데이터": s_meta,
        "점수_구조화데이터": s_struct,
        "점수_모바일": s_mob,
        "점수_다국어": s_i18n,
        "점수_이미지alt": s_img,
        "점수_크롤링설정": s_crawl,
        "점수_종합": total,
        "진단_메모": " / ".join(all_notes),
    }


# --- main ---
with open(INPUT_CSV, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print(f"총 {len(rows)}개 처리 시작...")

base_fields = list(rows[0].keys())
fieldnames = base_fields + [c for c in SCORE_COLS if c not in base_fields]

done = []
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, encoding="utf-8-sig") as f:
        done = list(csv.DictReader(f))
    print(f"{len(done)}개 이미 완료, 이어서 시작")

processed = {r["기관명"] for r in done}

with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    if not done:
        w.writeheader()

    for i, row in enumerate(rows):
        if row["기관명"] in processed:
            continue

        url = row.get("홈페이지", "").strip()
        result = diagnose(url) if url else None

        if result and "error" not in result:
            for col in SCORE_COLS:
                row[col] = result.get(col, "")
        elif result and "error" in result:
            for col in SCORE_COLS[:-1]:
                row[col] = ""
            row["점수_종합"] = ""
            row["진단_메모"] = "접근불가: " + result["error"]
        else:
            for col in SCORE_COLS:
                row[col] = ""
            row["진단_메모"] = "홈페이지 없음"

        w.writerow(row)
        f.flush()

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(rows)} 완료...")

        if url:
            time.sleep(0.3)

print("완료!")
