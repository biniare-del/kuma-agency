"""티스토리 꿈담 블로그 RSS → blog.json (홈페이지 '꿈담 블로그' 칸용).

GitHub Actions(.github/workflows/blog-feed.yml)가 하루 2회 실행한다.
표준 라이브러리만 쓴다. 실패하면 기존 blog.json을 그대로 둔다(빈 목록으로 덮지 않음).
사용: python scripts/blog_feed.py [출력경로=blog.json]
"""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://dreamag.tistory.com/rss"
LIMIT = 5


def main(out_path: str) -> int:
    req = urllib.request.Request(FEED, headers={"User-Agent": "dream-ag-blog-feed/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            root = ET.fromstring(r.read())
    except Exception as e:  # 네트워크·파싱 실패: 기존 파일 유지
        print(f"feed fetch failed, keep existing file: {e}")
        return 0

    posts = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate") or ""
        if not title or not link.startswith("https://dreamag.tistory.com/"):
            continue
        try:
            date = parsedate_to_datetime(pub).strftime("%Y.%m.%d")
        except Exception:
            date = ""
        posts.append({"date": date, "title": title, "url": link})
        if len(posts) >= LIMIT:
            break

    if not posts:
        print("no posts parsed, keep existing file")
        return 0

    data = {"source": "티스토리", "posts": posts}
    try:
        with open(out_path, encoding="utf-8") as f:
            if json.load(f) == data:
                print("no change")
                return 0
    except (FileNotFoundError, ValueError):
        pass
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"wrote {len(posts)} posts to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "blog.json"))
