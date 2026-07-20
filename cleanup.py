import pandas as pd

df = pd.read_excel(r"C:\Users\binia\Desktop\영업대상_네이버.xlsx")

# 약국, 종합병원 제거
df = df[~df["카테고리"].str.contains("약국|종합병원", na=False)]

# 전남 광주 제거
df = df[~df["주소"].str.contains("전남|전라|광주광역시|광주통합", na=False)]

# A/B/C 등급 재분류
def remap(g):
    if g == "A등급 (홈페이지 없음)":
        return "A등급"
    if g == "A등급 (블로그만 있음)":
        return "A등급"
    return "B등급"  # 확인필요 → B등급 (URL 확인 후 C등급 제외)

df["등급"] = df["등급"].apply(remap)

# A등급은 경쟁 있는 과목만 타깃 (동네병원 제외)
A_TARGET = ["피부과", "성형외과", "산부인과", "안과"]
a_mask = df["등급"] == "A등급"
a_target_mask = df["카테고리"].str.contains("|".join(A_TARGET), na=False)
df = df[~a_mask | a_target_mask]

# 발송 템플릿 컬럼
df["발송템플릿"] = df["등급"].apply(lambda x: "버전A" if x == "A등급" else "버전C")

# 관리 컬럼 추가
for col in ["이메일", "발송여부", "발송일", "응답여부", "영업메모"]:
    df[col] = ""

# 정렬: A → B
order = {"A등급": 0, "B등급": 1}
df["_sort"] = df["등급"].map(order)
df = df.sort_values("_sort").drop(columns=["_sort"])
df = df.reset_index(drop=True)

output = r"C:\Users\binia\Desktop\영업대상_전체.xlsx"

# 시트 분리 저장
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df[df["등급"] == "A등급"].to_excel(writer, sheet_name="A등급", index=False)
    df[df["등급"] == "B등급"].to_excel(writer, sheet_name="B등급", index=False)
    df.to_excel(writer, sheet_name="전체", index=False)

a = len(df[df["등급"] == "A등급"])
b = len(df[df["등급"] == "B등급"])
print(f"완료! 총 {len(df)}개")
print(f"  A등급: {a}개 (버전A 이메일 즉시 발송)")
print(f"  B등급: {b}개 (URL 확인 후 버전C 이메일)")
print(f"저장: {output}")
