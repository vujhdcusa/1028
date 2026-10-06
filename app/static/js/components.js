// 互動元件：五年資料夾分頁、可編輯表格。

// ---------- 五年資料夾分頁 ----------
document.querySelectorAll("[data-folders]").forEach((root) => {
  const tabs = [...root.querySelectorAll('[role="tab"]')];
  const panels = [...root.querySelectorAll('[role="tabpanel"]')];

  const select = (tab, focus = false) => {
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
    });
    panels.forEach((p) => { p.hidden = p.id !== tab.getAttribute("aria-controls"); });
    if (focus) tab.focus();
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (event) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
      if (!step) return;
      event.preventDefault();
      select(tabs[(index + step + tabs.length) % tabs.length], true);
    });
  });

  const initial = tabs.find((t) => t.dataset.initial === "true") || tabs[0];
  if (initial) select(initial);
});

// ---------- 可編輯表格：送出時轉成 JSON 給後端 ----------
document.querySelectorAll("[data-record-table]").forEach((table) => {
  const body = table.querySelector("tbody");
  const template = table.querySelector("template");
  const fields = JSON.parse(table.dataset.fields);
  const output = document.getElementById(table.dataset.output);
  const form = table.closest("form");
  const emptyRow = body.querySelector(".empty-row");

  const refreshEmpty = () => {
    if (emptyRow) emptyRow.hidden = body.querySelectorAll("tr[data-row]").length > 0;
  };

  const addRow = (values = {}) => {
    const row = template.content.firstElementChild.cloneNode(true);
    fields.forEach((name) => {
      const input = row.querySelector(`[data-field="${name}"]`);
      if (input && values[name] !== undefined && values[name] !== null) input.value = values[name];
    });
    row.querySelector("[data-remove]").addEventListener("click", () => { row.remove(); refreshEmpty(); });
    body.appendChild(row);
    refreshEmpty();
    return row;
  };

  JSON.parse(table.dataset.initial || "[]").forEach((values) => addRow(values));
  refreshEmpty();

  document.querySelectorAll(`[data-add-row="${table.id}"]`).forEach((button) => {
    button.addEventListener("click", () => {
      const row = addRow();
      const first = row.querySelector("input, select");
      if (first) first.focus();
    });
  });

  form.addEventListener("submit", () => {
    const rows = [...body.querySelectorAll("tr[data-row]")].map((row) => {
      const item = {};
      fields.forEach((name) => {
        const input = row.querySelector(`[data-field="${name}"]`);
        item[name] = input ? input.value.trim() : "";
      });
      return item;
    }).filter((item) => Object.values(item).some((value) => value !== ""));
    output.value = JSON.stringify(rows);
  });
});

// ---------- 缺件比對：容器依序裝滿、數字往上跳、點容器看細節 ----------
document.querySelectorAll("[data-gap-board]").forEach((board) => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const vessels = [...board.querySelectorAll(".vessel")];
  vessels.forEach((vessel, index) => vessel.style.setProperty("--delay", reduce ? "0s" : `${index * 0.18}s`));
  requestAnimationFrame(() => vessels.forEach((vessel) => vessel.classList.add("is-filled")));

  const panels = [...document.querySelectorAll("[data-gap-detail]")];
  const open = (vessel) => {
    vessels.forEach((v) => v.setAttribute("aria-expanded", String(v === vessel)));
    panels.forEach((panel) => { panel.hidden = panel.id !== vessel.getAttribute("aria-controls"); });
  };
  vessels.forEach((vessel) => vessel.addEventListener("click", () => open(vessel)));
  // 先打開「最需要補」的那一格：加權最大、還沒滿的項目
  const first = vessels.find((v) => v.dataset.priority === "true") || vessels[0];
  if (first) open(first);
});

document.querySelectorAll("[data-count]").forEach((el) => {
  const target = Number(el.dataset.count);
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || Number.isNaN(target)) { el.textContent = target; return; }
  const start = performance.now();
  const step = (now) => {
    const t = Math.min((now - start) / 1400, 1);
    el.textContent = Math.round(target * (1 - Math.pow(1 - t, 3)));
    if (t < 1) requestAnimationFrame(step);
  };
  el.textContent = "0";
  requestAnimationFrame(step);
});
