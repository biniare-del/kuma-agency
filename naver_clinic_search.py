import os
import requests
import pandas as pd
import time
import re

CLIENT_ID = os.environ["NAVER_CLIENT_ID"]
CLIENT_SECRET = os.environ["NAVER_CLIENT_SECRET"]

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

KEYWORDS = [
    # 과목명
    "성형외과", "피부과", "안과", "치과",

    # 성형 시술
    "코성형", "눈성형", "쌍꺼풀", "가슴성형", "리프팅", "안면윤곽",
    "광대수술", "퀵광대", "사각턱", "턱끝수술", "이마거상", "목거상", "안면거상",
    "눈매교정", "트임성형", "눈썹거상", "눈밑지방재배치", "하안검", "상안검",
    "매부리코", "복코", "짧은코", "휜코", "자가늑연골", "코재수술",
    "지방흡입", "복부성형", "허벅지지방흡입", "팔뚝지방흡입",
    "귀성형", "실리프팅", "지방이식",

    # 피부 시술
    "울쎄라", "써마지", "인모드", "슈링크", "리쥬란", "스킨부스터",
    "물광주사", "보톡스", "필러", "레이저토닝", "피코토닝", "프락셀",
    "여드름", "기미", "주근깨", "점제거", "색소레이저", "모공",
    "홍조", "제모", "피부관리", "미백", "항노화", "콜라겐",
    "쁘띠성형", "윤곽주사",

    # 안과 시술
    "라식", "라섹", "스마일라식", "백내장", "노안라식", "노안교정",

    # 치과 시술
    "임플란트", "치아교정", "라미네이트", "투명교정", "크라운", "치아미백",
]

QUERIES = [f"{loc} {kw}" for loc in LOCATIONS for kw in KEYWORDS]

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

TABS = {
    "성형외과": ["성형외과", "코성형", "눈성형", "쌍꺼풀", "가슴성형", "리프팅", "안면윤곽",
               "광대수술", "퀵광대", "사각턱", "턱끝수술", "이마거상", "목거상", "안면거상",
               "눈매교정", "트임성형", "눈썹거상", "눈밑지방재배치", "하안검", "상안검",
               "매부리코", "복코", "짧은코", "휜코", "자가늑연골", "코재수술",
               "지방흡입", "복부성형", "허벅지지방흡입", "팔뚝지방흡입",
               "귀성형", "실리프팅", "지방이식"],
    "피부과":  ["피부과", "울쎄라", "써마지", "인모드", "슈링크", "리쥬란", "스킨부스터",
               "물광주사", "보톡스", "필러", "레이저토닝", "피코토닝", "프락셀",
               "여드름", "기미", "주근깨", "점제거", "색소레이저", "모공",
               "홍조", "제모", "피부관리", "미백", "항노화", "콜라겐",
               "쁘띠성형", "윤곽주사"],
    "안과":   ["안과", "라식", "라섹", "스마일라식", "백내장", "노안라식", "노안교정"],
    "치과":   ["치과", "임플란트", "치아교정", "라미네이트", "투명교정", "크라운", "치아미백"],
}

output = "영업대상_네이버.xlsx"
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="전체", index=False)
    for tab, kws in TABS.items():
        pattern = "|".join(kws)
        sheet = df[df["검색어"].str.contains(pattern, na=False)]
        sheet.to_excel(writer, sheet_name=tab, index=False)

b = len(df[df["등급"] == "확인필요"])
print(f"\n완료! 총 {len(df)}개 병원 (중복 제거 후)")
print(f"  확인필요 (홈페이지 있음): {b}개  ← URL 점수 확인 → B등급 후보")
print(f"  저장: {output}")
