# 진단 도구용 Cloudflare Worker 배포

무료 공개 CORS 프록시(allorigins, corsproxy.io 등)는 불안정하고 보안 설정에 따라 자주 막힙니다.
이 Worker를 배포하면 우리가 직접 관리하는 안정적인 프록시를 갖게 됩니다.

## 배포 단계

1. https://dash.cloudflare.com 가입 (무료 플랜)
2. 좌측 메뉴 **Workers & Pages** → **Create** → **Create Worker**
3. 이름을 정한다 (예: `kuma-check-proxy`)
4. **Edit code** 화면에서 기존 코드를 모두 지우고 `proxy-worker.js` 내용을 붙여넣기
5. **Deploy** 클릭
6. 배포 후 나오는 URL을 복사 (예: `https://kuma-check-proxy.<계정이름>.workers.dev`)
7. 그 URL을 `check/check.js`의 `PROXIES` 배열 맨 앞에 추가:
   ```js
   (u) => "https://kuma-check-proxy.<계정이름>.workers.dev/?url=" + encodeURIComponent(u),
   ```

무료 플랜은 하루 100,000 요청까지 무료라 진단 도구 용도로는 충분합니다.
