const PROXIES = [
  (u) => "https://dream-ag.biniare.workers.dev/?url=" + encodeURIComponent(u),
  (u) => "https://api.allorigins.win/raw?url=" + encodeURIComponent(u),
  (u) => "https://corsproxy.io/?url=" + encodeURIComponent(u),
  (u) => "https://api.codetabs.com/v1/proxy?quest=" + encodeURIComponent(u),
];

function colorFor(score) {
  if (score >= 70) return "var(--color-good)";
  if (score >= 40) return "var(--color-mid)";
  return "var(--color-bad)";
}

// 프록시가 응답을 안 하면 무한 대기하는 문제 방지 — 개별 요청에 타임아웃 부여
function timedFetch(u, ms = 9000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  return fetch(u, { signal: ctrl.signal }).finally(() => clearTimeout(timer));
}

async function fetchText(url) {
  let lastErr;
  for (const buildProxyUrl of PROXIES) {
    try {
      const res = await timedFetch(buildProxyUrl(url));
      if (!res.ok) throw new Error("HTTP " + res.status);
      const text = await res.text();
      if (text && text.length > 0) return text;
      throw new Error("empty response");
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error("fetch failed: " + url);
}

// robots.txt / sitemap.xml 존재 여부 확인.
// 반환: "ok"(있음) | "missing"(404로 명확히 없음) | "unknown"(프록시 실패·차단 등 확인 불가)
// "확인 불가"를 "없음"으로 단정하지 않는 것이 핵심 — 실제로 있는데 없다고 표시하면 신뢰를 잃음.
async function fetchStatus(url) {
  for (const buildProxyUrl of PROXIES) {
    try {
      const res = await timedFetch(buildProxyUrl(url));
      if (res.ok) return "ok";
      if (res.status === 404) return "missing";
    } catch {}
  }
  return "unknown";
}

function scoreMeta(doc) {
  let score = 0;
  const notes = [];
  const title = doc.querySelector("title");
  if (title && title.textContent.trim().length >= 10) { score += 35; }
  else notes.push("title 태그 미흡");
  const desc = doc.querySelector('meta[name="description"]');
  if (desc && desc.getAttribute("content") && desc.getAttribute("content").trim().length >= 20) { score += 35; }
  else notes.push("meta description 없음/짧음");
  const og = doc.querySelector('meta[property^="og:"]');
  if (og) { score += 30; }
  else notes.push("Open Graph 태그 없음");
  return { score, notes };
}

function scoreStructuredData(doc) {
  const scripts = doc.querySelectorAll('script[type="application/ld+json"]');
  if (scripts.length === 0) return { score: 0, notes: ["구조화 데이터(JSON-LD) 없음 — AI검색이 병원 정보를 이해하기 어려움"] };
  let valid = 0;
  scripts.forEach((s) => {
    try { JSON.parse(s.textContent); valid++; } catch {}
  });
  if (valid === 0) return { score: 20, notes: ["JSON-LD가 있지만 형식 오류로 읽히지 않을 수 있음"] };
  return { score: 100, notes: [] };
}

function scoreMobile(doc) {
  const vp = doc.querySelector('meta[name="viewport"]');
  if (vp && /width=device-width/.test(vp.getAttribute("content") || "")) {
    return { score: 100, notes: [] };
  }
  return { score: 0, notes: ["모바일 반응형 viewport 설정 없음"] };
}

function scoreI18n(doc) {
  const hreflang = doc.querySelectorAll('link[hreflang]');
  const langAttr = doc.documentElement.getAttribute("lang");
  let score = 0;
  const notes = [];
  if (hreflang.length > 0) score += 70;
  else notes.push("hreflang 다국어 태그 없음 — 해외환자 검색 노출 불리");
  if (langAttr) score += 30;
  else notes.push("html lang 속성 없음");
  return { score: Math.min(score, 100), notes };
}

function scoreImages(doc) {
  const imgs = Array.from(doc.querySelectorAll("img"));
  if (imgs.length === 0) return { score: 50, notes: ["이미지가 거의 없어 평가 어려움"] };
  const withAlt = imgs.filter((img) => (img.getAttribute("alt") || "").trim().length > 0).length;
  const ratio = withAlt / imgs.length;
  const score = Math.round(ratio * 100);
  const notes = score < 70 ? [`이미지 ${imgs.length}개 중 alt텍스트 있는 이미지 ${withAlt}개 — 검색엔진이 이미지 내용을 읽지 못함`] : [];
  return { score, notes };
}

async function scoreCrawlSetup(pageUrl) {
  let origin;
  try { origin = new URL(pageUrl).origin; }
  catch { return { score: 50, notes: ["주소 형식을 확인하지 못해 크롤링 설정은 평가에서 제외"] }; }

  const [robots, sitemap] = await Promise.all([
    fetchStatus(origin + "/robots.txt"),
    fetchStatus(origin + "/sitemap.xml"),
  ]);

  const notes = [];
  // 확인 불가(unknown)는 감점하지 않고 별도 표시 — "있는데 없다고 단정"하는 오류 방지
  const sub = (status, okNote, missingNote) => {
    if (status === "ok") return 50;
    if (status === "missing") { notes.push(missingNote); return 0; }
    notes.push(okNote + " 확인 불가 (사이트가 외부 접근을 차단했을 수 있음 — 감점 아님)");
    return 50;
  };

  const score =
    sub(robots, "robots.txt", "robots.txt 없음") +
    sub(sitemap, "sitemap.xml", "sitemap.xml 없음 — 검색엔진이 전체 페이지를 못 찾을 수 있음");

  return { score, notes };
}

function renderBar(container, label, result) {
  const row = document.createElement("div");
  row.className = "score-bar-row";
  const color = colorFor(result.score);
  row.innerHTML = `
    <div class="label-row"><span>${label}</span><span class="val" style="color:${color}">${result.score}점</span></div>
    <div class="score-bar-track"><div class="score-bar-fill" style="width:${result.score}%;background:${color}"></div></div>
    ${result.notes.length ? `<div class="detail">${result.notes.join(" · ")}</div>` : ""}
  `;
  container.appendChild(row);
}

// JS로 화면을 그리는 사이트(SPA) 감지.
// 우리 도구는 HTML 원본만 읽고 JS를 실행하지 않으므로, 이런 사이트는 실제 내용이 있어도
// 낮게 나온다. 이 경우 거짓 저점을 주는 대신 "수동 확인 필요"로 정직하게 표시한다.
function looksJsRendered(doc) {
  const bodyText = (doc.body ? doc.body.textContent : "").replace(/\s+/g, " ").trim();
  if (bodyText.length >= 300) return false; // 실제 텍스트가 충분하면 정상 페이지

  // 본문이 거의 비었는데 아래 신호가 있으면 JS 렌더링 앱 껍데기로 판단
  const spaRoot = doc.querySelector(
    '#root, #app, #__next, #__nuxt, [data-reactroot], [ng-app], [data-server-rendered]'
  );
  const scriptCount = doc.querySelectorAll("script[src]").length;
  return !!spaRoot || scriptCount >= 3;
}

// meta refresh(<meta http-equiv="refresh" content="0; URL=...">) 리다이렉트 대상 URL 추출.
// 카페24 등 옛 병원 사이트가 루트를 빈 스플래시로 두고 내부 페이지로 튕기는 패턴 대응.
function findMetaRefreshTarget(doc, baseUrl) {
  const metas = doc.querySelectorAll('meta[http-equiv]');
  for (const m of metas) {
    if ((m.getAttribute("http-equiv") || "").toLowerCase() !== "refresh") continue;
    const content = m.getAttribute("content") || "";
    const match = content.match(/url\s*=\s*['"]?([^'";]+)/i);
    if (match) {
      try { return new URL(match[1].trim(), baseUrl).href; } catch { return null; }
    }
  }
  return null;
}

async function runCheck(url) {
  let html = await fetchText(url);
  let doc = new DOMParser().parseFromString(html, "text/html");

  // 루트가 meta refresh 스플래시면 실제 콘텐츠 페이지로 한 번 따라가서 재채점
  // (최대 2회 추적하여 무한 루프 방지)
  for (let hops = 0; hops < 2; hops++) {
    const target = findMetaRefreshTarget(doc, url);
    if (!target || target === url) break;
    try {
      const nextHtml = await fetchText(target);
      html = nextHtml;
      doc = new DOMParser().parseFromString(html, "text/html");
      url = target;
    } catch {
      break;
    }
  }

  const categories = [
    { label: "메타데이터 (제목/설명)", result: scoreMeta(doc) },
    { label: "구조화 데이터 (AI검색용 JSON-LD)", result: scoreStructuredData(doc) },
    { label: "모바일 대응", result: scoreMobile(doc) },
    { label: "해외환자 대응 (다국어)", result: scoreI18n(doc) },
    { label: "이미지 접근성 (alt텍스트)", result: scoreImages(doc) },
    { label: "검색엔진 크롤링 설정", result: await scoreCrawlSetup(url) },
  ];

  const total = Math.round(categories.reduce((sum, c) => sum + c.result.score, 0) / categories.length);
  const jsRendered = looksJsRendered(doc);

  const bars = document.getElementById("scoreBars");
  bars.innerHTML = "";
  categories.forEach((c) => renderBar(bars, c.label, c.result));

  const circle = document.getElementById("scoreCircle");
  const msgEl = document.getElementById("scoreMessage");

  if (jsRendered) {
    // 자동 진단이 부정확할 수 있는 사이트 — 거짓 점수 대신 수동 확인 안내
    circle.style.borderColor = "var(--color-mid)";
    document.getElementById("scoreTotal").textContent = "?";
    msgEl.innerHTML =
      "⚠️ 이 홈페이지는 접속 후 자바스크립트로 화면을 그리는 방식이라, 자동 진단 도구가 실제 내용을 정확히 읽지 못합니다. " +
      "아래 점수는 <strong>참고용</strong>이며 실제보다 낮게 나올 수 있으니, 정확한 진단은 직접 문의해 주시면 수동으로 확인해 드립니다.";
    return;
  }

  circle.style.borderColor = colorFor(total);
  document.getElementById("scoreTotal").textContent = total;

  if (total >= 70) {
    msgEl.textContent = "검색·AI검색 노출 기본기는 갖춰져 있습니다. 다만 부분적으로 보완하면 더 많은 노출 기회를 잡을 수 있습니다.";
  } else if (total >= 40) {
    msgEl.textContent = "검색·AI검색에 절반 정도만 노출되고 있을 가능성이 높습니다. 비어있는 항목부터 보완이 필요합니다.";
  } else {
    msgEl.textContent = "현재 상태로는 검색엔진과 AI검색이 병원 정보를 거의 읽지 못하고 있을 가능성이 큽니다. 두 번째 홈페이지로 빠르게 보완하는 것을 권장합니다.";
  }
}

document.getElementById("checkForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  let url = document.getElementById("urlInput").value.trim();
  if (url && !/^https?:\/\//i.test(url)) url = "https://" + url;
  const btn = document.getElementById("checkBtn");
  const resultEl = document.getElementById("result");
  const errorEl = document.getElementById("errorBox");

  btn.disabled = true;
  btn.textContent = "진단 중...";
  errorEl.hidden = true;

  try {
    await runCheck(url);
    resultEl.hidden = false;
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    resultEl.hidden = true;
    errorEl.hidden = false;
    errorEl.querySelector("p").textContent =
      "진단 중 문제가 발생했습니다. 사이트가 외부 접근을 차단했거나 주소가 올바르지 않을 수 있습니다. (오류: " + err.message + ") 잠시 후 다시 시도하시거나, 직접 문의해 주시면 수동으로 확인해 드립니다.";
  } finally {
    btn.disabled = false;
    btn.textContent = "진단 시작";
  }
});
