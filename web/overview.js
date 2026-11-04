(() => {
  "use strict";
  if (window.__powerfulStudiesOverviewBound) return;
  window.__powerfulStudiesOverviewBound = true;
  const command = (action, extra = {}) =>
    pycmd("powerful-studies:" + JSON.stringify({ action, ...extra }));
  const root = () => document.querySelector("#ps-overview");

  document.addEventListener("click", (event) => {
    const target = event.target.closest("[data-overview-action]");
    if (!target || !root()) return;
    event.preventDefault();
    event.stopPropagation();
    const action = target.dataset.overviewAction;
    const cardId = Number(target.dataset.cardId);
    if (action === "previous" || action === "next") {
      const current = Number(
        document.querySelector(".ps-pagination span").textContent.match(/\d+/)?.[0] || 1,
      );
      command("page", { page: action === "previous" ? current - 1 : current + 1 });
    } else if (["answer", "preview", "edit", "delete"].includes(action)) {
      command(action, { card_id: cardId });
    } else if (action === "open-deck") {
      command(action, { deck_id: Number(target.dataset.deckId) });
    } else {
      command(action);
    }
  });

  document.addEventListener("change", (event) => {
    if (!root()) return;
    const target = event.target;
    if (target.classList.contains("ps-card-select")) {
      command("select", { card_id: Number(target.dataset.cardId), selected: target.checked });
    } else if (target.id === "ps-select-page") {
      command("select-page", { selected: target.checked });
    } else if (target.id === "ps-card-state" || target.id === "ps-include-subdecks") {
      command("query", queryValues());
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.target.id === "ps-card-search" && event.key === "Enter") {
      event.preventDefault();
      command("query", queryValues());
    }
  });

  function queryValues() {
    return {
      search: document.querySelector("#ps-card-search").value,
      state: document.querySelector("#ps-card-state").value,
      include_subdecks: document.querySelector("#ps-include-subdecks").checked,
    };
  }
})();
