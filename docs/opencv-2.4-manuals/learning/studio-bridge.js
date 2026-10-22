// Same-origin embedding only. A standalone classroom keeps its existing behavior.
if (
  window.parent !== window &&
  new URLSearchParams(location.search).get("embedded") === "1"
) {
  document.documentElement.classList.add("embedded");
  window.addEventListener("message", (event) => {
    if (
      event.origin !== location.origin ||
      event.source !== window.parent ||
      event.data?.type !== "studio-learning-context"
    )
      return;
    const context = event.data;
    if (LANGUAGES.some((l) => l.id === context.locale)) locale = context.locale;
    if (["python", "cpp", "c", "java"].includes(context.program))
      program = context.program;
    if (window.LESSONS.some((l) => l.id === context.topic))
      current = context.topic;
    render();
  });
  const sendPreference = () =>
    window.parent.postMessage(
      { type: "learning-preference", locale, program },
      location.origin,
    );
  get("locale").addEventListener("change", sendPreference);
  get("program").addEventListener("change", sendPreference);
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      window.parent.postMessage({ type: "learning-close" }, location.origin);
    }
  });
}
