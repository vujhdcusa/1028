// 捲動動畫：只在使用者沒有關閉動畫時啟用。
(() => {
  document.documentElement.classList.remove("no-js");
  document.documentElement.classList.add("js");

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 五年路徑：依實際長度設定虛線，才能做出「一路畫過去」的效果
  document.querySelectorAll(".route__line path").forEach((path) => {
    path.style.setProperty("--len", Math.ceil(path.getTotalLength()));
  });

  if (reduce || !("IntersectionObserver" in window)) {
    document.querySelectorAll("[data-motion], .route, .stack").forEach((el) => el.classList.add("is-visible"));
    document.querySelectorAll("[data-scatter]").forEach((el) => el.classList.add("is-sorted"));
    return;
  }

  document.documentElement.classList.add("motion-ready");

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.2, rootMargin: "0px 0px -40px" });

  document.querySelectorAll('[data-motion="reveal"], .route, .stack').forEach((el) => observer.observe(el));

  // 首頁第一幕：往下捲一點，散落的資料就自動排整齊
  const scatter = document.querySelector("[data-scatter]");
  if (scatter) {
    const state = scatter.querySelector("[data-scatter-state]");
    const update = () => {
      const sorted = window.scrollY > 80;
      scatter.classList.toggle("is-sorted", sorted);
      if (state) state.textContent = sorted ? "已整理" : "散落中";
    };
    window.addEventListener("scroll", update, { passive: true });
    update();
  }
})();
