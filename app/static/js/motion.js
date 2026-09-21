(() => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  if (prefersReducedMotion.matches) {
    return;
  }

  document.documentElement.classList.add("motion-ready");

  const revealItems = document.querySelectorAll('[data-motion="reveal"]');
  const journeyPaths = document.querySelectorAll("[data-journey-path]");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.18, rootMargin: "0px 0px -36px" }
  );

  revealItems.forEach((item) => observer.observe(item));
  journeyPaths.forEach((path) => observer.observe(path));
})();
