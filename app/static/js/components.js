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
