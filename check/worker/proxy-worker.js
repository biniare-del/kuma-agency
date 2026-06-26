// Cloudflare Worker: 진단 도구용 CORS 프록시
// 배포 방법은 check/worker/README.md 참고

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

    try {
      const res = await fetch(targetUrl.toString(), {
        headers: { "User-Agent": "Mozilla/5.0 (compatible; KumaAgencyDiagnostic/1.0)" },
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
