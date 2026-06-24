function won(n) {
  return n.toLocaleString("ko-KR") + "원";
}

function render() {
  const clientName = document.getElementById("clientName").value.trim() || "-";
  const contactName = document.getElementById("contactName").value.trim();
  const specialty = document.getElementById("specialty").value;
  const note = document.getElementById("note").value.trim();

  const checked = Array.from(document.querySelectorAll(".checkbox input[type=checkbox][data-price]:checked"));
  const optionTotal = checked.reduce((sum, el) => sum + Number(el.dataset.price), 0);

  const BASE_LIST_PRICE = 4400000;
  const discountApplied = document.getElementById("discountToggle").checked;
  const basePrice = discountApplied ? BASE_LIST_PRICE / 2 : BASE_LIST_PRICE;
  const buildTotal = basePrice + optionTotal;

  const planEl = document.querySelector('input[name="plan"]:checked');
  const planPrice = Number(planEl.value);

  document.getElementById("outClient").textContent = clientName;
  document.getElementById("outContact").textContent = contactName ? `(${contactName})` : "";
  document.getElementById("outSpecialty").textContent = specialty;

  const rows = document.getElementById("quoteRows");
  rows.innerHTML = `<tr><td>기본 구축 (검색·AI검색 최적화 세컨 홈페이지) 정가</td><td>${won(BASE_LIST_PRICE)}</td></tr>`;
  if (discountApplied) {
    rows.innerHTML += `<tr><td>초기 레퍼런스 고객 한정 50% 할인</td><td>-${won(BASE_LIST_PRICE / 2)}</td></tr>`;
  }
  checked.forEach((el) => {
    rows.innerHTML += `<tr><td>${el.dataset.label}</td><td>${won(Number(el.dataset.price))}</td></tr>`;
  });

  document.getElementById("outBuildTotal").textContent = won(buildTotal);
  document.getElementById("outPlanTotal").textContent =
    planPrice === 0 ? "없음" : `${won(planPrice)} / 월 (${planEl.dataset.label})`;

  document.getElementById("outNote").textContent = note;

  const today = new Date();
  document.getElementById("quoteDate").textContent =
    `발행일: ${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, "0")}.${String(today.getDate()).padStart(2, "0")}`;
}

document.querySelectorAll("input, select, textarea").forEach((el) => {
  el.addEventListener("input", render);
  el.addEventListener("change", render);
});

render();
