# 로코코 저널 — 병원 홈페이지 제작 레퍼런스 문서

> 이 문서는 로코코성형외과 저널 사이트 구축 경험을 바탕으로,
> 타 병원 홈페이지 제작 시 참고할 수 있도록 정리한 것입니다.

---

## 1. 전체 아키텍처

### 기술 스택
- **프론트엔드**: 순수 정적 HTML/CSS/JS (빌드 툴 없음)
- **호스팅**: GitHub Pages (main 브랜치 / root)
- **백엔드 API**: Vercel Functions (`api/*.js`, Node.js)
- **데이터베이스**: Supabase (PostgreSQL)
- **이메일**: Resend
- **분석**: Google Analytics 4 (GA4)
- **CDN 폰트**: NanumSquare (jsdelivr)

### 구조 원칙
- GitHub Pages는 서버사이드 코드 실행 불가 → 백엔드 로직은 반드시 Vercel Functions로 분리
- API 키, 비밀번호 등 민감 정보는 Vercel 환경변수로 관리
- *.sql 원본 DB 덤프는 .gitignore 처리 — 절대 커밋 금지

### 파일 구조

```
/
├── index.html                  ← 한국어 메인
├── css/style.css               ← 전체 공통 스타일
├── assets/                     ← 로컬 이미지
├── {카테고리}/                  ← 시술 카테고리
│   ├── index.html              ← 카테고리 목록
│   └── {서브카테고리}/
│       ├── index.html          ← 서브카테고리 목록
│       └── {id}/index.html     ← 아티클 상세
├── counsel/index.html          ← 온라인 상담 폼
├── reserve/index.html          ← 예약 신청 폼
├── cases/index.html            ← 전후사진 갤러리
├── about/                      ← 병원 소개
├── en/, ja/, zh/               ← 외국어 랜딩 페이지
├── admin/index.html            ← 관리자 페이지
├── api/                        ← Vercel Functions
│   ├── inquiries.js            ← 상담 문의 CRUD
│   ├── reserve.js              ← 예약 신청 (퍼블릭)
│   ├── reservations.js         ← 예약 관리 (어드민)
│   ├── schedule.js             ← 운영시간 설정
│   ├── publish.js              ← 글 발행
│   ├── stats.js                ← 대시보드 통계
│   └── track.js                ← 페이지뷰 추적
└── tools/build_pages.py        ← SQL → HTML 자동 생성 스크립트
```

---

## 2. 한국어 콘텐츠 사이트

### 네비게이션 구조
- 데스크탑: 가로 GNB, 카테고리에 서브메뉴 드롭다운
- 모바일: 햄버거 버튼 → 슬라이드인 사이드 패널 (640px 이하)
- **필수 요소 — 빠지면 모바일 메뉴 깨짐**:
  - `<div class="gnb-overlay" id="gnbOverlay"></div>` → `<header>` **바깥 앞**에 위치
  - `<div class="gnb-header">` + `<button class="gnb-close">` → `<nav>` 안 `<ul>` **앞**에 위치

### 아티클 페이지 구조
- hero → breadcrumb → article-layout (본문 + 사이드바)
- `<div class="translate-notice">`: 외국어 브라우저에만 표시 (JS 감지)
  - `navigator.language`가 `ko`이면 숨김
  - 영어/일본어/중국어 각각 해당 언어로 번역 안내
  - 기본값 `display:none` (CSS), JS로만 표시
- **아티클 원본 글 내용 절대 임의 요약/재작성 금지** — 원장 원문 그대로

### SEO 핵심 설정 (페이지당)

```html
<title>제목 — 병원명 원장명</title>
<meta name="description" content="...">
<meta property="og:title/description/image/url/type">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="...">
<script type="application/ld+json">
  <!-- MedicalWebPage + BreadcrumbList schema -->
</script>
```

- hreflang (ko/en/ja/zh/x-default) — 루트 및 외국어 페이지에 설정
- GA4 트래킹 코드 모든 페이지 삽입
- 페이지뷰 Supabase 저장 (api/track.js) → 관리자 대시보드 조회

---

## 3. 외국어 사이트 (en/ja/zh)

### 구조 원칙
- 외국어 페이지는 별도 랜딩 (`/en/`, `/ja/`, `/zh/`) 구성
- 한국어 아티클로 링크 → `translate-notice`로 브라우저 번역 안내

### 각 외국어 페이지 구성 순서
1. 언어 선택 바 (상단 검은 바)
2. 헤더 (로고 + 심플 nav)
3. 히어로 섹션 (CTA: 카카오톡 문의, 전화)
4. 시술 카테고리별 케이스 가로 스크롤 카드
5. 원장 소개
6. 상담 방법 (온라인 폼 + 카카오톡)
7. FAQ (국제 환자용)
8. 위치 & 진료시간
9. 푸터

### 외국어 페이지 필수 메타

```html
<html lang="en">  <!-- en / ja / zh-Hans -->
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" hreflang="ko" href="...">
<link rel="alternate" hreflang="en" href="...">
<link rel="alternate" hreflang="ja" href="...">
<link rel="alternate" hreflang="zh" href="...">
<link rel="alternate" hreflang="x-default" href="...">
```

### 외국어 푸터 구조

```html
<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-col">...</div>  <!-- 주소/연락처 -->
    <div class="footer-col">...</div>  <!-- 진료시간 -->
    <div class="footer-col">...</div>  <!-- 언어 선택 -->
  </div>
  <div class="footer-bottom" style="text-align:center;justify-content:center;...">
    <p>© {창립연도}–{현재연도} 병원명. All rights reserved.</p>
  </div>
</footer>
```

- `.footer-inner`: `max-width:1080px; margin:0 auto; display:flex; gap:2.5rem`
- `.footer-col` 글씨색: 밝은 배경 기준 `#555` / 타이틀 `#111`
- copyright: **창립 연도부터** 표기 (예: `© 2011–2025`)
- 히어로 클래스: `.lang-hero` 사용 (`.en-hero` 금지 — 언어 중립)

---

## 4. 예약 신청 시스템 (reserve/)

### 유저 페이지 — 4단계 폼
1. **진료정보**: 시술 카테고리 + 초진/재진
2. **날짜 선택**: 캘린더 UI (휴진일 비활성화)
3. **시간 선택**: 30분 단위 슬롯 (API → 가용 시간 조회)
4. **개인정보**: 이름, 연락처, 연락방법(전화/카카오톡), 동의

완료 후: "예약 신청 후 전화/카카오톡으로 연락 후 확정" 안내 표시

### API 구성
- `GET /api/reserve?date=YYYY-MM-DD` → 가용 슬롯 반환
- `POST /api/reserve` → 예약 생성 (중복 방지 검증 포함)
- `GET /api/schedule` → 운영시간 조회 (퍼블릭)
- `PATCH /api/schedule` → 운영시간 수정 (어드민 전용)

### Supabase 테이블

```sql
-- reservations
id, name, phone, contact_method, visit_type, category,
date, time, status DEFAULT 'new', note, created_at

-- settings (운영시간 JSON)
key PRIMARY KEY, value jsonb, updated_at
```

### 기본 운영시간 초기값 (settings INSERT)
- 월~금: 09:00–18:00
- 토: 09:00–16:00
- 일: 휴진
- 슬롯 단위: 30분

---

## 5. 관리자 페이지 (admin/)

### 인증
- 비밀번호 기반 (`ADMIN_PASSWORD` Vercel 환경변수)
- localStorage 저장 → 재방문 시 자동 로그인
- **비밀번호 전송: Authorization 헤더만 사용** (`Bearer {pw}`)
- URL 쿼리스트링 전송 절대 금지 (Vercel 로그/브라우저 히스토리에 노출됨)

### 레이아웃
- 사이드바(220px 고정) + 메인 콘텐츠
- 모바일(640px 이하):
  - `.mob-topbar`: 상단 고정 바 + 햄버거 버튼
  - `.sidebar-overlay`: 배경 딤 처리
  - 사이드바 `transform: translateX(-100%)` 숨김/표시

### 탭 구성
| 탭 | 기능 |
|---|---|
| 대시보드 | 일별 방문자 차트, 인기 페이지, 최근 문의 요약 |
| 온라인 상담 | 상담 문의 관리 |
| 예약 캘린더 | 예약 관리 + 운영시간 설정 |
| 새 글 작성 | 아티클 발행 |
| 글 관리 | 기존 글 수정/삭제 |

### 상담 관리 기능
- **3단계 상태**: 신규 → 상담중 → 완료
- 인라인 메모 저장
- 필터 탭: 전체 / 신규 / 상담중 / 완료
- 일괄 처리: 전체선택 삭제 / 완료 전체삭제
- CSV 다운로드

### 예약 관리 기능
- 월별 캘린더 뷰 (날짜별 예약 건수)
- 예약 목록 탭 (신규/확정/취소)
- **3단계 상태**: 신규 → 확정 → 취소
- 인라인 메모
- 운영시간 설정 UI (요일별 시간, 슬롯 단위, 휴진일 관리)

### 신규 알림 배지
- 사이드바 메뉴 옆 **NEW** 태그 (빨간 사각 pill)
- 로그인 시 자동 조회, 상태 변경 시 실시간 업데이트
- 건수 0이 되면 자동 숨김

### API 상수 구조 (중요)

```js
// 각각 독립 상수로 선언할 것
// API.replace()로 파생하면 const 중복 선언 위험
const API       = 'https://{프로젝트}.vercel.app/api/publish';
const STATS_API = 'https://{프로젝트}.vercel.app/api/stats';
const INQ_API   = 'https://{프로젝트}.vercel.app/api/inquiries';
const RESV_API  = 'https://{프로젝트}.vercel.app/api/reservations';
const SCHED_API = 'https://{프로젝트}.vercel.app/api/schedule';

function authHead(extra) {
  return Object.assign({'Authorization': 'Bearer ' + savedPw}, extra || {});
}
```

---

## 6. 보안 체크리스트

- [ ] *.sql 파일 .gitignore 처리
- [ ] 환경변수: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ADMIN_PASSWORD`, `RESEND_API_KEY`
- [ ] 관리자 비밀번호 → Authorization 헤더 전송 (URL 금지)
- [ ] admin API CORS → `Access-Control-Allow-Origin`을 해당 도메인으로 제한
- [ ] `Access-Control-Allow-Headers`에 `Authorization` 포함
- [ ] API 파일 auth 함수: `req.headers.authorization` 우선 확인

---

## 7. 타 병원 적용 시 커스터마이징 포인트

### 반드시 변경
- 병원명, 원장명, 전화번호, 주소
- GA4 측정 ID
- Vercel 프로젝트명 / API 엔드포인트 URL
- Supabase 프로젝트 (신규 생성 + 테이블 생성)
- 카카오톡 채널 링크
- copyright 연도 (창립 연도 기준)
- 진료시간 (settings 테이블 초기값)
- 시술 카테고리 구조

### 시술 카테고리
- 로코코 기준: 광대성형 / 코성형 / 콧구멍성형 / 이마성형 / 눈성형 / 동안성형
- 타 병원은 전문 분야에 맞게 재구성
- `build_pages.py`도 카테고리에 맞게 수정 필요

### 예약 시스템 진료항목 드롭다운
- `reserve/index.html` 내 카테고리 선택 옵션 → 병원 시술 항목으로 변경

---

## 8. 배포 프로세스

1. GitHub 저장소 생성 (병원별)
2. GitHub Pages 활성화 (main / root)
3. Vercel 프로젝트 생성 → GitHub 연동 → 환경변수 설정
4. Supabase 프로젝트 생성 → 테이블 생성 → settings 초기값 INSERT
5. Vercel 배포 → API URL 확인 → admin/index.html 상수 업데이트
6. 커스텀 도메인 연결 (GitHub Pages + Vercel 각각)

---

## 9. 알려진 주의사항 / 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 관리자 페이지 JS 전혀 안 돌아감 | `const` 중복 선언 | 선언 위치 확인, 중복 제거 |
| 모바일 메뉴 열리지 않음 | `gnb-overlay` 또는 `gnb-header` 누락 | 구조 확인 후 추가 |
| 예약 신청 nav 아래 검은 버튼 노출 | `<nav>` 안에 중복 `<a>` 태그 | 중복 제거 |
| 외국어 footer 글씨 안 보임 | 배경 밝은데 글씨 흰색 | `.footer-col` 색상 `#555`/`#111`으로 |
| copyright 왼쪽 정렬 | `.footer-bottom` flex 정렬 | `justify-content:center` 추가 |
| 상담 목록에 "undefined" 표시 | status 컬럼 추가 전 데이터 | `statusLabel()` fallback 함수로 처리 |
| 번역 안내 한국인에게도 표시 | JS 감지 누락 | `navigator.language` 체크 스크립트 삽입 |
