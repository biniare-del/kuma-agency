import pandas as pd

df = pd.read_excel(r"C:\Users\binia\Desktop\영업대상_네이버.xlsx")

# 약국, 종합병원 제거
df = df[~df["카테고리"].str.contains("약국|종합병원", na=False)]

# 전남 광주 제거
df = df[~df["주소"].str.contains("전남|전라|광주광역시|광주통합", na=False)]

# B등급만 타깃 (홈페이지 있는데 허접한 곳)
df = df[df["등급"] == "확인필요"]
df["등급"] = "B등급"

# 발송 템플릿 컬럼
df["발송템플릿"] = "버전C"

# 관리 컬럼 추가
for col in ["이메일", "발송여부", "발송일", "응답여부", "영업메모"]:
    df[col] = ""

df = df.reset_index(drop=True)

output = r"C:\Users\binia\Desktop\영업대상_전체.xlsx"

# 저장
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="B등급", index=False)

print(f"완료! B등급 총 {len(df)}개")
print(f"저장: {output}")
