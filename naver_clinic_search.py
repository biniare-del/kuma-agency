import requests
import pandas as pd
import time
import re

CLIENT_ID = "r_1K9ZtkLbWZ3KLADEae"
CLIENT_SECRET = "U_rB637zWG"

DISTRICTS = [
    # 서울 (경쟁 약한 구)
    "노원구", "도봉구", "중랑구", "강동구", "구로구", "금천구",
    "관악구", "동대문구", "성북구", "강북구", "은평구", "양천구",
    "영등포구", "동작구", "광진구",
    # 경기도
    "의정부시", "광명시", "시흥시", "평택시", "안산시", "부천시",
    "고양시", "수원시", "성남시", "용인시", "화성시", "남양주시",
    "파주시", "김포시", "안양시", "구리시", "하남시", "오산시",
    "양주시", "이천시", "광주시",
]

SPECIALTIES = [
    "정형외과", "이비인후과", "산부인과", "안과", "한의원",
    "재활의학과", "가정의학과", "외과", "신경과", "비뇨의학과",
]

QUERIES = [f"{d} {s}" for d in DISTRICTS for s in SPECIALTIES]

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
df.to_excel(output, index=False)

a1 = len(df[df["등급"] == "A등급 (홈페이지 없음)"])
a2 = len(df[df["등급"] == "A등급 (블로그만 있음)"])
b  = len(df[df["등급"] == "확인필요"])
print(f"\n완료! 총 {len(df)}개 병원")
print(f"  A등급 (홈페이지 없음):   {a1}개  ← 버전A 이메일 즉시 발송")
print(f"  A등급 (블로그만 있음):   {a2}개  ← 버전A 이메일 발송")
print(f"  확인필요 (홈페이지 있음): {b}개  ← URL 점수 확인 필요")
print(f"  저장: {output}")
