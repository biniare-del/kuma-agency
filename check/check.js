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

async function fetchText(url) {
  let lastErr;
  for (const buildProxyUrl of PROXIES) {
    try {
      const res = await fetch(buildProxyUrl(url));
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

async function fetchOk(url) {
  for (const buildProxyUrl of PROXIES) {
    try {
      const res = await fetch(buildProxyUrl(url));
      if (res.ok) return true;
    } catch {}
  }
  return false;
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
  const origin = new URL(pageUrl).origin;
  const [robots, sitemap] = await Promise.all([
    fetchOk(origin + "/robots.txt"),
    fetchOk(origin + "/sitemap.xml"),
  ]);
  let score = 0;
  const notes = [];
  if (robots) score += 50; else notes.push("robots.txt 없음");
  if (sitemap) score += 50; else notes.push("sitemap.xml 없음 — 검색엔진이 전체 페이지를 못 찾을 수 있음");
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

async function runCheck(url) {
  const html = await fetchText(url);
  const doc = new DOMParser().parseFromString(html, "text/html");

  const categories = [
    { label: "메타데이터 (제목/설명)", result: scoreMeta(doc) },
    { label: "구조화 데이터 (AI검색용 JSON-LD)", result: scoreStructuredData(doc) },
    { label: "모바일 대응", result: scoreMobile(doc) },
    { label: "해외환자 대응 (다국어)", result: scoreI18n(doc) },
    { label: "이미지 접근성 (alt텍스트)", result: scoreImages(doc) },
    { label: "검색엔진 크롤링 설정", result: await scoreCrawlSetup(url) },
  ];

  const total = Math.round(categories.reduce((sum, c) => sum + c.result.score, 0) / categories.length);

  const bars = document.getElementById("scoreBars");
  bars.innerHTML = "";
  categories.forEach((c) => renderBar(bars, c.label, c.result));

  const circle = document.getElementById("scoreCircle");
  circle.style.borderColor = colorFor(total);
  document.getElementById("scoreTotal").textContent = total;

  const msgEl = document.getElementById("scoreMessage");
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
