document.querySelectorAll(".role-card").forEach(card => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  card.addEventListener("mousemove", e => {
    const r = card.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    card.style.transform =
      `rotateY(${x * 18}deg) rotateX(${-y * 18}deg) translateY(-6px)`;
  });
  card.addEventListener("mouseleave", () => {
    card.style.transform = "";
  });
});