import pandas as pd

df = pd.read_excel(r"C:\Users\binia\Desktop\영업대상_네이버.xlsx")

# 타겟 의원급 카테고리만 남기기
TARGET_CATEGORIES = ["병원,의원>성형외과", "병원,의원>피부과", "병원,의원>안과", "병원,의원>치과", "미용>피부,체형관리"]
df = df[df["카테고리"].isin(TARGET_CATEGORIES)]

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
