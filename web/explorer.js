(() => {
  "use strict";
  if (window.__powerfulStudiesExplorerBound) return;
  window.__powerfulStudiesExplorerBound = true;
  const send = (action, payload = {}) =>
    pycmd("powerful-studies:" + JSON.stringify({ action, ...payload }));

  function selectableCards() {
    return [...document.querySelectorAll(".ps-deck-card")];
  }

  function updateSelectionControls() {
    const cards = selectableCards();
    const checked = cards.filter((card) => card.querySelector("[data-deck-select]")?.checked);
    const count = document.getElementById("ps-selection-count");
    const selectAll = document.getElementById("ps-select-all");
    const clear = document.getElementById("ps-clear-selection");
    const remove = document.getElementById("ps-delete-selected");
    if (count) count.textContent = `${checked.length} selecionado(s)`;
    if (selectAll) {
      selectAll.checked = cards.length > 0 && checked.length === cards.length;
      selectAll.indeterminate = checked.length > 0 && checked.length < cards.length;
    }
    if (clear) clear.disabled = checked.length === 0;
    if (remove) remove.disabled = checked.length === 0;
  }

  document.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action]");
    if (!target) return;
    event.preventDefault();
    event.stopPropagation();
    const action = target.dataset.action;
    if (action === "clear-selection") {
      document.querySelectorAll("[data-deck-select]").forEach((checkbox) => {
        checkbox.checked = false;
      });
      updateSelectionControls();
    }
    send(action, target.dataset.id === undefined ? {} : { id: target.dataset.id });
  });
  document.addEventListener("input", (event) => {
    if (event.target.id !== "ps-search") return;
    const query = event.target.value.trim().toLocaleLowerCase();
    document.querySelectorAll(".ps-deck-card").forEach((card) => {
      card.hidden = Boolean(query) && !card.dataset.name.includes(query);
    });
    updateSelectionControls();
  });
  document.addEventListener("change", (event) => {
    if (event.target.id === "ps-sort") {
      send("sort", { value: event.target.value });
      return;
    }
    if (event.target.matches("[data-deck-select]")) {
      send("select", { id: event.target.dataset.id, selected: event.target.checked });
      updateSelectionControls();
      return;
    }
    if (event.target.id !== "ps-select-all") return;
    const cards = selectableCards();
    const ids = cards
      .map((card) => card.querySelector("[data-deck-select]")?.dataset.id)
      .filter(Boolean);
    cards.forEach((card) => {
      const checkbox = card.querySelector("[data-deck-select]");
      if (checkbox) checkbox.checked = event.target.checked;
    });
    send(
      event.target.checked ? "select-all" : "clear-selection",
      event.target.checked ? { ids } : {},
    );
    updateSelectionControls();
  });
  updateSelectionControls();
})();
