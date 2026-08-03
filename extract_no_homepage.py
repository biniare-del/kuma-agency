"""
'홈페이지 없음 / SNS만 있는' 병원을 따로 분류 → 버전A(홈페이지 없는 병원) 영업 리스트 생성
────────────────────────────────────────────────
score_targets.py가 '자체 홈페이지 있는 곳'만 채점한다면, 이 스크립트는 그 반대
(홈페이지가 아예 없거나 인스타·블로그 등 SNS만 있는 곳)를 모아 별도 파일로 만든다.
이들은 진단할 홈페이지가 없으므로 "검색에 아예 안 보인다"는 버전A 멘트로 접근.
- 입력: 영업대상_전체.xlsx
- 출력: 영업대상_홈페이지없음.xlsx  (네트워크 접속 없음, 즉시 생성)
실행:  python extract_no_homepage.py
"""
import pandas as pd
from urllib.parse import urlparse

INPUT = r"C:\Users\binia\Desktop\영업대상_전체.xlsx"
OUTPUT = r"C:\Users\binia\Desktop\영업대상_홈페이지없음.xlsx"

SNS_DOMAINS = ("instagram.com", "naver.com", "blog.", "kakao.com", "youtube.com", "youtu.be")


def classify(url):
    """'홈페이지없음' | 'SNS만' | '홈페이지있음'"""
    if not isinstance(url, str) or not url.strip():
        return "홈페이지없음"
    host = urlparse(url if "://" in url else "https://" + url).netloc.lower()
    if any(bad in host for bad in SNS_DOMAINS):
        return "SNS만"
    return "홈페이지있음"


def pitch(kind):
    if kind == "홈페이지없음":
        return ("자체 홈페이지 없음 → 네이버·구글·ChatGPT 어디에도 병원 정보가 거의 안 나옴. "
                "'검색 → 홈페이지 확인 → 예약' 경로 자체가 막힌 상태 (버전A 접근)")
    return ("인스타·블로그 등 SNS만 있음 → 증상·시술 검색과 AI 추천에 안 잡힘. "
            "SNS는 검색 색인이 약해 사실상 검색 노출 0에 가까움 (버전A 접근)")


def main():
    df = pd.read_excel(INPUT)
    df["분류"] = df["홈페이지"].apply(classify)

    target = df[df["분류"] != "홈페이지있음"].copy()
    target["영업멘트"] = target["분류"].apply(pitch)

    # 보기 편하게: SNS만(연락 채널 있음) 먼저, 그다음 홈페이지없음
    order = {"SNS만": 0, "홈페이지없음": 1}
    target = target.sort_values(by="분류", key=lambda s: s.map(order))

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        target.to_excel(writer, sheet_name="버전A_타겟(홈페이지없음)", index=False)
        target[target["분류"] == "SNS만"].to_excel(writer, sheet_name="SNS만", index=False)
        target[target["분류"] == "홈페이지없음"].to_excel(writer, sheet_name="홈페이지완전없음", index=False)

    n_sns = (target["분류"] == "SNS만").sum()
    n_none = (target["분류"] == "홈페이지없음").sum()
    print(f"전체 {len(df)}개 중 → SNS만 {n_sns}개 / 홈페이지완전없음 {n_none}개 (합 {len(target)}개)")
    print(f"저장: {OUTPUT}")


if __name__ == "__main__":
    main()
