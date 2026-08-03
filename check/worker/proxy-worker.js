// Cloudflare Worker: 진단 도구용 CORS 프록시
// 배포 방법은 check/worker/README.md 참고
//
// 2026-07-27 개선:
// - 봇 UA("KumaAgencyDiagnostic") → 실제 브라우저 UA로 변경. 일부 사이트가
//   봇에게 부실/차단 응답을 주던 오탐을 줄임.
// - ?mobile=1 파라미터 지원: 모바일 브라우저 UA로 요청. 기기별로 다른 페이지를
//   내려주는 사이트(예: allfit.kr)의 실제 모바일 대응 여부를 정확히 진단하기 위함.

const UA_DESKTOP =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";
const UA_MOBILE =
  "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1";

export default {
  async fetch(request) {
    const reqUrl = new URL(request.url);
    const target = reqUrl.searchParams.get("url");

    if (!target) {
      return new Response("Missing url parameter", { status: 400 });
    }

    let targetUrl;
    try {
      targetUrl = new URL(target);
      if (targetUrl.protocol !== "https:" && targetUrl.protocol !== "http:") {
        throw new Error("invalid protocol");
      }
    } catch {
      return new Response("Invalid url parameter", { status: 400 });
    }

    const isMobile = reqUrl.searchParams.get("mobile") === "1";

    try {
      const res = await fetch(targetUrl.toString(), {
        headers: {
          "User-Agent": isMobile ? UA_MOBILE : UA_DESKTOP,
          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        },
        redirect: "follow",
      });
      const body = await res.text();
      return new Response(body, {
        status: res.status,
        headers: {
          "Content-Type": res.headers.get("Content-Type") || "text/html; charset=utf-8",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } catch (err) {
      return new Response("Fetch failed: " + err.message, {
        status: 502,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }
  },
};
