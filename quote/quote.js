function won(n) {
  return n.toLocaleString("ko-KR") + "원";
}

function getPagePrice(count) {
  if (count <= 0) return 0;
  if (count >= 30) return 600000;
  if (count >= 10) return 250000;
  return count * 30000;
}

function getPageLabel(count) {
  if (count <= 0) return null;
  if (count >= 30) return `시술 상세페이지 ${count}개 (30개 이상 묶음)`;
  if (count >= 10) return `시술 상세페이지 ${count}개 (10개 이상 묶음)`;
  return `시술 상세페이지 ${count}개 (개당 30,000원)`;
}

function getPageHint(count) {
  if (count <= 0) return "추가 없음";
  if (count >= 30) return `${count}개 → 60만원 (30개 이상 묶음가)`;
  if (count >= 10) return `${count}개 → 25만원 (10개 이상 묶음가)`;
  return `${count}개 × 30,000원 = ${won(count * 30000)}`;
}

const SOLO_TIER_SPECIALTY = "소상공인 (원페이지형)";
const SOLO_LIST_PRICE = 2000000;
const STANDARD_LIST_PRICE = 4400000;

function render() {
  const clientName = document.getElementById("clientName").value.trim() || "-";
  const contactName = document.getElementById("contactName").value.trim();
  const specialty = document.getElementById("specialty").value;
  const note = document.getElementById("note").value.trim();
  const isSolo = specialty === SOLO_TIER_SPECIALTY;
  const pageCount = isSolo ? 0 : (parseInt(document.getElementById("pageCount").value) || 0);

  document.getElementById("pageCountFieldset").style.display = isSolo ? "none" : "";
  document.getElementById("pageCountHint").textContent = getPageHint(pageCount);

  const checked = Array.from(document.querySelectorAll(".checkbox input[type=checkbox][data-price]:checked"));
  const optionTotal = checked.reduce((sum, el) => sum + Number(el.dataset.price), 0);
  const pagePrice = getPagePrice(pageCount);

  const BASE_LIST_PRICE = isSolo ? SOLO_LIST_PRICE : STANDARD_LIST_PRICE;
  document.getElementById("baseConfigHint").textContent = isSolo
    ? `검색·AI검색 최적화 구조화 데이터, 원페이지 랜딩, 모바일 반응형, robots.txt/sitemap.xml/llms.txt 기본 포함 — 정가 ${won(SOLO_LIST_PRICE)}`
    : `검색·AI검색 최적화 구조화 데이터, 국문 랜딩페이지, 모바일 반응형, robots.txt/sitemap.xml/llms.txt 기본 포함 — 정가 ${won(STANDARD_LIST_PRICE)}`;
  document.getElementById("discountAmountLabel").textContent = `−${won(BASE_LIST_PRICE / 2)}`;
  document.getElementById("discountHint").textContent = isSolo
    ? `한정 기간 특별가입니다. 정식가는 ${won(SOLO_LIST_PRICE * 0.8)}~${won(SOLO_LIST_PRICE)} 구간입니다.`
    : "한정 기간 특별가입니다. 정식가는 3,500,000원~4,400,000원 구간입니다.";

  const discountApplied = document.getElementById("discountToggle").checked;
  const basePrice = discountApplied ? BASE_LIST_PRICE / 2 : BASE_LIST_PRICE;
  const buildTotal = basePrice + optionTotal + pagePrice;

  const planEl = document.querySelector('input[name="plan"]:checked');
  const planPrice = Number(planEl.value);

  document.getElementById("outClient").textContent = clientName;
  document.getElementById("outContact").textContent = contactName ? `(${contactName})` : "";
  document.getElementById("outSpecialty").textContent = specialty;

  const rows = document.getElementById("quoteRows");
  const baseLabel = isSolo ? "기본 구축 (소상공인 원페이지형)" : "기본 구축";
  rows.innerHTML = `<tr><td>${baseLabel}</td><td>검색·AI검색 최적화 세컨 홈페이지</td><td>${won(BASE_LIST_PRICE)}</td></tr>`;

  if (discountApplied) {
    rows.innerHTML += `<tr class="discount-row"><td>오픈 기념 특별 할인</td><td>50% 할인</td><td>−${won(BASE_LIST_PRICE / 2)}</td></tr>`;
  }

  if (pageCount > 0) {
    rows.innerHTML += `<tr><td>시술 상세페이지</td><td>${pageCount}개</td><td>${won(pagePrice)}</td></tr>`;
  }

  checked.forEach((el) => {
    rows.innerHTML += `<tr><td>${el.dataset.label.split(' (')[0].replace(/\s+\S+$/, el.dataset.label.includes('(') ? '' : '')}</td><td>${el.dataset.label}</td><td>${won(Number(el.dataset.price))}</td></tr>`;
  });

  document.getElementById("outBuildTotal").textContent = won(buildTotal);
  document.getElementById("outGrandTotal").textContent = won(buildTotal);
  document.getElementById("outPlanTotal").textContent =
    planPrice === 0 ? "없음" : `${won(planPrice)} / 월 (${planEl.dataset.label})`;

  document.getElementById("outNote").textContent = note;

  const today = new Date();
  document.getElementById("quoteDate").textContent =
    `발행일: ${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, "0")}.${String(today.getDate()).padStart(2, "0")}`;
}

// 페이지 수 +/- 버튼
document.getElementById("pageCountMinus").addEventListener("click", () => {
  const el = document.getElementById("pageCount");
  el.value = Math.max(0, (parseInt(el.value) || 0) - 1);
  render();
});
document.getElementById("pageCountPlus").addEventListener("click", () => {
  const el = document.getElementById("pageCount");
  el.value = (parseInt(el.value) || 0) + 1;
  render();
});

document.querySelectorAll("input, select, textarea").forEach((el) => {
  el.addEventListener("input", render);
  el.addEventListener("change", render);
});

render();
