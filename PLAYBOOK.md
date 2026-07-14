# 꿈을담은에이전시 — 병원 세컨 홈페이지 제작 플레이북

> 실제 클라이언트 수주 시 처음부터 끝까지 참고하는 실무 가이드.  
> 로코코 저널(journal.rococops.com) 제작 경험 + 포트폴리오 6종 구축 경험 종합.  
> 마지막 업데이트: 2026-07-14

---

## 1. 이 사업의 핵심 포지셔닝

**"기존 홈페이지는 그대로 두고, AI·검색엔진이 읽을 수 있는 두 번째 홈페이지를 추가 구축한다"**

- 기존 사이트 = 브랜딩·예약전환용 (건드리지 않는다)
- 세컨 사이트 = 구글/네이버 검색 노출 + ChatGPT/Gemini/Claude 등 AI 검색 인용 + 해외환자 다국어 대응
- 클라이언트의 기존 호스팅 계정·비밀번호는 절대 받지 않는다 → DNS CNAME 1개 추가만 요청

---

## 2. 기술 스택 (확정)

| 항목 | 선택 | 이유 |
|------|------|------|
| 구조 | 정적 HTML/CSS/JS | 크롤러가 가장 잘 읽음, 빠름, 유지비 없음 |
| 호스팅 | Vercel 또는 Netlify | 한 계정에 클라이언트별 무제한 프로젝트+커스텀 도메인, 무료 티어로 수십 곳 운영 가능 |
| 도메인 구조 | 서브도메인 권장 (`journal.병원도메인.com`) | 루트 도메인 권위 일부 상속 → 인덱싱 빠름 |
| 문의 폼 백엔드 | Formspree | 클라이언트 이메일로 1회 등록하면 끝, 별도 서버 불필요 |
| 상담/예약 DB | Supabase + Vercel Functions | 관리자 목록 관리가 필요한 경우에만 |
| 이미지 | 자체 호스팅 (`/images/` 폴더) | 로코코는 핫링크 의존이 약점이었음 — 직접 보관 |
| 이미지 최적화 | WebP 변환 + lazy-load | Core Web Vitals 증거, hero-bg는 57KB 이하 목표 |

---

## 3. 필수 파일 구조 (모든 클라이언트 사이트 공통)

```
클라이언트사이트/
├── index.html          # 메인 랜딩 (한국어)
├── styles.css
├── en/
│   └── index.html      # 영어 랜딩 (해외환자 대응)
├── cases/
│   └── index.html      # 케이스·후기 통합페이지
├── reserve/
│   └── index.html      # 온라인 예약 (3단계 진행바)
├── admin/              # templates/admin/ 복사 후 색상·병원명 교체
│   ├── index.html      # 로그인 게이트
│   ├── dashboard.html
│   ├── consultations.html
│   ├── reservations.html
│   ├── reviews.html
│   └── content.html
├── images/             # 모든 이미지 자체 호스팅
├── robots.txt          # AI 크롤러 명시적 Allow 포함
├── sitemap.xml
└── llms.txt            # AI 학습·인용용 사이트 소개 텍스트
```

---

## 4. SEO / AI검색 최적화 체크리스트

클라이언트 사이트 납품 전 전부 확인.

### 4-1. HTML `<head>` 필수 태그

```html
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>시술명 | 병원명</title>
<meta name="description" content="150자 이내 핵심 요약">
<link rel="canonical" href="https://서브도메인.병원도메인.com/">

<!-- OG (카카오·SNS 공유) -->
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:url" content="https://...">
<meta property="og:image" content="https://.../og-image.jpg">

<!-- 다국어 hreflang -->
<link rel="alternate" hreflang="ko" href="https://.../">
<link rel="alternate" hreflang="en" href="https://.../en/">
```

### 4-2. JSON-LD 구조화 데이터 (필수)

메인 페이지에 최소 `MedicalClinic` + `Physician` + `FAQPage` 세 개 삽입.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "MedicalClinic",
  "name": "병원명",
  "description": "...",
  "url": "https://...",
  "telephone": "02-0000-0000",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "서울특별시",
    "addressRegion": "강남구",
    "streetAddress": "도로명주소"
  },
  "medicalSpecialty": "PlasticSurgery",  // 진료과별 변경
  "openingHours": ["Mo-Fr 09:00-18:00"],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.9",
    "reviewCount": "120"
  }
}
</script>
```

**진료과별 `medicalSpecialty` 값:**
- 성형외과: `PlasticSurgery`
- 피부과: `Dermatology`
- 치과: `Dentist` (타입도 `Dentist`로 변경)
- 정형외과: `Orthopedic`
- 한의원: `TraditionalChineseMedicine`
- 신경외과: `Neurosurgery`

### 4-3. robots.txt (AI 크롤러 명시적 허용)

```
User-agent: *
Allow: /
Disallow: /admin/

# AI 검색 크롤러 명시적 허용
User-agent: GPTBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: anthropic-ai
Allow: /

Sitemap: https://서브도메인.병원도메인.com/sitemap.xml
```

### 4-4. llms.txt (AI 인용 최적화 핵심)

루트에 `llms.txt` 파일 생성. AI 모델이 사이트 정보를 요약할 때 참고하는 파일.

```
# 병원명

병원명은 [지역]에 위치한 [진료과] 전문 의원입니다.

## 주요 시술
- 시술1: 설명
- 시술2: 설명

## 연락처
- 전화: 02-0000-0000
- 주소: 서울특별시 ...
- 진료시간: 월-금 09:00-18:00

## 온라인 채널
- 홈페이지: https://...
- 온라인 예약: https://.../reserve/
```

### 4-5. Speakable Schema (음성 검색·AI 답변 인용용)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".hero-sub", ".about-summary", ".faq-answer"]
  }
}
</script>
```

### 4-6. 시술 상세페이지 TL;DR 블록 (GEO 핵심)

AI가 답변을 생성할 때 맨 앞 단락을 발췌하는 경향이 있음. 각 시술 페이지 상단에:

```html
<div class="tldr">
  <strong>요약</strong>
  <p>[시술명]은 [한 줄 정의]. 주요 대상은 [대상], 회복기간은 [기간]입니다.</p>
</div>
```

---

## 5. 다국어 대응

### 5-1. 구조
- `/en/index.html` — 영어 랜딩 필수 (해외환자 구글 검색 대응)
- `/ja/`, `/zh/` — 선택 옵션 (일본어·중국어, 별도 견적)
- 헤더에 국기 스위처 UI (없는 언어는 깃발만 표시)

### 5-2. 헤더 언어 스위처 예시

```html
<div class="lang-switcher">
  <a href="../" class="lang-btn active" title="한국어">🇰🇷</a>
  <a href="../en/" class="lang-btn" title="English">🇺🇸</a>
  <span class="lang-btn disabled" title="日本語（준비중）">🇯🇵</span>
  <span class="lang-btn disabled" title="中文（준비중）">🇨🇳</span>
</div>
```

### 5-3. 브라우저 언어 감지 자동 리다이렉트

```html
<script>
(function(){
  const lang = navigator.language || navigator.userLanguage;
  if (lang.startsWith('en') && !location.pathname.includes('/en/')) {
    location.replace('/en/');
  }
})();
</script>
```

---

## 6. 상담 폼 / 문의 수신 설정

### Formspree 설정 순서 (클라이언트별)

1. formspree.io 에 클라이언트 이메일로 가입 (또는 내 계정에서 폼 추가 후 수신 이메일만 클라이언트로 설정)
2. 폼 ID 발급 받기 (예: `xkodndpg`)
3. HTML에 적용:

```html
<form action="https://formspree.io/f/[폼ID]" method="POST">
  <!-- 필드들 -->
  <input type="hidden" name="_next" value="https://사이트주소/thanks.html">
</form>
```

4. Formspree 대시보드에서 수신 확인

### 카카오채널 플로팅 버튼

```html
<a href="https://pf.kakao.com/_[채널ID]/chat" class="kakao-float" target="_blank" rel="noopener">
  <img src="/images/kakao-icon.png" alt="카카오 상담">
  <span>카카오 상담</span>
</a>
```

---

## 7. 도메인 / DNS 설정 (클라이언트에게 요청하는 작업)

클라이언트가 직접 해야 하는 작업은 **딱 한 가지**:

> DNS 관리 화면(카페24, 가비아, AWS Route53 등)에서 CNAME 레코드 1개 추가

```
타입: CNAME
호스트(서브도메인): journal  (또는 원하는 이름)
값(가리킬 주소): cname.vercel-dns.com  (Vercel 사용 시)
TTL: 3600 (또는 자동)
```

Vercel 대시보드 → Project → Settings → Domains 에서 `journal.병원도메인.com` 추가 후 CNAME 값 확인.

---

## 8. 관리자 패널 납품

### 기준 템플릿 위치
`templates/admin/` — 병원명·색상만 교체하면 바로 사용 가능.

### 파일별 역할

| 파일 | 설명 |
|------|------|
| `index.html` | 로그인 게이트 |
| `register.html` | 상담 회원가입 |
| `dashboard.html` | 노출수·클릭수·예약 현황 차트 (Chart.js) |
| `consultations.html` | 상담 목록, 미읽음 표시, 요일별·시술별 분포 |
| `reservations.html` | 예약 캘린더 + 시간대별 목록 + 오프라인 등록 |
| `reviews.html` | 후기 승인·게시·숨김 관리 |
| `content.html` | 시술·케이스 콘텐츠 CMS |
| `admin.css` | 공통 스타일 |

### 색상 교체 방법

`admin.css` 최상단 CSS 변수만 바꾸면 됨:

```css
:root {
  --accent: #3a5ddb;      /* 병원 브랜드 색으로 교체 */
  --accent-dark: #2944a8;
}
```

### 실제 납품 시 백엔드 연결

- **이메일 수신만 필요**: Formspree (빠름, 5분 설정)
- **상담·예약 목록 관리까지**: Supabase(DB) + Vercel Functions(API) 조합
  - `consultations.html`, `reservations.html`의 목업 데이터를 Supabase fetch로 교체
  - 로코코 어드민은 GitHub API 기반이라 수정 기능 없었음 — 이 구조가 훨씬 완성도 높음

---

## 9. 납품 전 최종 체크리스트

```
[ ] robots.txt — AI 크롤러 Allow 포함 확인
[ ] sitemap.xml — 모든 페이지 URL 포함 확인
[ ] llms.txt — 병원 정보 정확히 기재
[ ] JSON-LD — MedicalClinic + Physician + FAQPage 최소 3개
[ ] canonical 태그 — 실제 도메인으로 설정 (GitHub Pages URL 아님)
[ ] hreflang — 한국어/영어 상호 참조
[ ] OG 태그 — title/description/image/url 전부 채워짐
[ ] 이미지 alt 텍스트 — 모든 <img> 에 alt 속성
[ ] 이미지 lazy-load — <img loading="lazy">
[ ] hero 배경 이미지 — 100KB 이하 (WebP 또는 압축 JPG)
[ ] 모바일 반응형 — 320px~1440px 전 구간 확인
[ ] 폼 — Formspree 연결, 실제 이메일 수신 테스트
[ ] 카카오채널 — 링크 실제 연결 확인
[ ] Google Search Console — 사이트 등록 + sitemap 제출
[ ] 네이버서치어드바이저 — 사이트 등록 + sitemap 제출
[ ] DNS CNAME — 서브도메인 실제 접속 확인 (24~48시간 전파 대기)
[ ] 개인정보처리방침 페이지 — 상담폼 있으면 필수
```

---

## 10. Search Console 등록 절차 (클라이언트 대신 진행)

1. [search.google.com/search-console](https://search.google.com/search-console) → "속성 추가"
2. URL 접두사 방식 선택 → `https://journal.병원도메인.com/` 입력
3. HTML 파일 인증 또는 `<meta name="google-site-verification">` 태그 추가
4. `sitemap.xml` 제출
5. 네이버서치어드바이저(searchadvisor.naver.com)도 동일하게 진행

---

## 11. 로코코 저널 제작 당시 교훈 (하지 말 것)

| 로코코의 약점 | 이번에 개선한 방식 |
|--------------|----------------|
| 이미지 핫링크 의존 (외부 URL) | `/images/` 폴더에 직접 보관 |
| hreflang 누락 | 모든 다국어 페이지에 필수 삽입 |
| Resend 도메인 인증 미완 | 납품 전 이메일 수신 실제 테스트 |
| 어드민 수정 기능 미구현 | `content.html` CMS UI 완비 |
| 869개 페이지 = 콘텐츠가 차별점 | 구조화 데이터·AI 최적화가 차별점 (페이지 수 아님) |

---

## 12. 가격 안내 (영업 시 기준)

| 구성 | 금액 |
|------|------|
| 기본 구축 (메인+영어+케이스+SEO풀세트+어드민) | **정가 4,400,000원** |
| 레퍼런스 고객 한정 50% 할인 | **2,200,000원** |
| 시술 상세페이지 | 1페이지당 50,000원 |
| 추가 외국어 1개 (일어·중국어 등) | 400,000원 |
| 온라인 예약 페이지 | 300,000원 |
| 카카오채널 연동 | 300,000원 |
| 완전 신규 디자인 | 500,000원 |
| AI 이미지 세트 (10장) | 200,000원 |
| **월 유지보수 — 베이직** (모니터링+분기리포트) | 200,000원/월 |
| **월 유지보수 — 스탠다드** (베이직+월1회 콘텐츠) | 350,000원/월 |
| **월 유지보수 — 프리미엄** (스탠다드+월2회+우선대응) | 500,000원/월 |

**절대 하지 말 것**: "검색노출 보장" 약속. 등록(Search Console 제출)은 해주지만 순위 보장은 불가 — 계약서에 명시.

---

## 13. 포트폴리오 레퍼런스 (샘플 사이트)

| # | 진료과 | 디자인 컨셉 | URL |
|---|--------|------------|-----|
| 1 | 성형외과 | 미니멀 메디컬 (화이트+블루) | `/portfolio/01-minimal-medical/` |
| 2 | 피부과 | 프리미엄 비주얼 (다크+골드) | `/portfolio/02-premium-visual/` |
| 3 | 치과 | 클린 민트 (틸+화이트) | `/portfolio/03-dental-clinic/` |
| 4 | 정형외과 | 스포츠 메디컬 (네이비+스틸블루) | `/portfolio/04-orthopedic/` |
| 5 | 한의원 | 전통+현대 (베이지+인디고) | `/portfolio/05-korean-medicine/` |
| 6 | 신경외과 | 기술·정밀 (차콜+바이올렛) | `/portfolio/06-neurosurgery/` |
