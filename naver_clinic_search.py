import requests
import pandas as pd
import time
import re

CLIENT_ID = "r_1K9ZtkLbWZ3KLADEae"
CLIENT_SECRET = "U_rB637zWG"

QUERIES = [
    "노원구 내과", "노원구 정형외과", "노원구 이비인후과", "노원구 산부인과", "노원구 안과",
    "도봉구 내과", "도봉구 정형외과", "도봉구 이비인후과",
    "중랑구 내과", "중랑구 정형외과", "중랑구 이비인후과",
    "구로구 내과", "구로구 정형외과", "구로구 산부인과",
    "강동구 내과", "강동구 정형외과", "강동구 이비인후과",
    "금천구 내과", "금천구 정형외과",
]

def clean(text):
    return re.sub(r"<[^>]+>", "", text)

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
for q in QUERIES:
    print(f"검색 중: {q}")
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
                "등급": "A등급 (홈페이지 없음)" if not link else "확인필요",
                "검색어": q,
            })
        time.sleep(0.5)
    except Exception as e:
        print(f"  오류: {e}")

df = pd.DataFrame(rows)
df = df.drop_duplicates(subset=["병원명", "주소"])

# A등급 먼저, 그 다음 확인필요
df["_sort"] = df["등급"].apply(lambda x: 0 if "A등급" in x else 1)
df = df.sort_values("_sort").drop(columns=["_sort"])

output = "영업대상_네이버.xlsx"
df.to_excel(output, index=False)

a = len(df[df["등급"].str.contains("A등급")])
b = len(df[df["등급"].str.contains("확인필요")])
print(f"\n완료! 총 {len(df)}개 병원")
print(f"  A등급 (홈페이지 없음): {a}개")
print(f"  확인필요 (홈페이지 있음): {b}개")
print(f"  저장: {output}")
