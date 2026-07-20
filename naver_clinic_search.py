import requests
import pandas as pd
import time
import re

CLIENT_ID = "r_1K9ZtkLbWZ3KLADEae"
CLIENT_SECRET = "U_rB637zWG"

LOCATIONS = [
    # 구 단위
    "강남구", "서초구", "마포구", "용산구", "양천구",
    # 동 단위 — 강남/부촌 권역
    "압구정", "청담", "대치", "역삼", "도곡", "개포", "논현", "신사", "학동",
    "방배", "반포", "잠원",
    "한남", "이태원",
    "홍대", "합정", "연남", "상수",
    "목동",
]

SPECIALTIES = [
    "성형외과", "피부과", "안과", "치과",
]

QUERIES = [f"{loc} {sp}" for loc in LOCATIONS for sp in SPECIALTIES]

def clean(text):
    return re.sub(r"<[^>]+>", "", text)

def grade(link):
    if not link:
        return "A등급 (홈페이지 없음)"
    if "blog.naver.com" in link or "blog.daum.net" in link:
        return "A등급 (블로그만 있음)"
    return "확인필요"

def search(query):
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {"query": query, "display": 100, "sort": "comment"}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    return res.json().get("items", [])

rows = []
total = len(QUERIES)
for i, q in enumerate(QUERIES, 1):
    print(f"[{i}/{total}] {q}")
    try:
        items = search(q)
        for item in items:
            link = item.get("link", "").strip()
            rows.append({
                "병원명": clean(item.get("title", "")),
                "카테고리": item.get("category", ""),
                "주소": item.get("roadAddress", "") or item.get("address", ""),
                "전화": item.get("telephone", ""),
                "홈페이지": link,
                "등급": grade(link),
                "검색어": q,
            })
        time.sleep(0.3)
    except Exception as e:
        print(f"  오류: {e}")

df = pd.DataFrame(rows)
df = df.drop_duplicates(subset=["병원명", "주소"])

order = {"A등급 (홈페이지 없음)": 0, "A등급 (블로그만 있음)": 1, "확인필요": 2}
df["_sort"] = df["등급"].map(order).fillna(3)
df = df.sort_values("_sort").drop(columns=["_sort"])

output = "영업대상_네이버.xlsx"
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="전체", index=False)
    for sp in SPECIALTIES:
        sheet = df[df["카테고리"].str.contains(sp.replace("과", "").replace("과", ""), na=False) |
                   df["검색어"].str.contains(sp, na=False)]
        sheet.to_excel(writer, sheet_name=sp, index=False)

b = len(df[df["등급"] == "확인필요"])
print(f"\n완료! 총 {len(df)}개 병원 (중복 제거 후)")
print(f"  확인필요 (홈페이지 있음): {b}개  ← URL 점수 확인 → B등급 후보")
print(f"  저장: {output}")
