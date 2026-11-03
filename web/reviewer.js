(() => {
  "use strict";
  if (window.powerfulStudiesReview) return;
  const rootId = "ps-review-header";
  const send = (action) => pycmd("powerful-studies:" + JSON.stringify({ action }));
  let currentQuestion = null;

  function header() {
    let element = document.getElementById(rootId);
    if (element) return element;
    element = document.createElement("header");
    element.id = rootId;
    element.innerHTML =
      '<nav class="ps-review-breadcrumb"></nav><div class="ps-review-actions"><button data-ps-review="reviewer-decks">Decks</button><button data-ps-review="reviewer-overview">Visão geral</button><button data-ps-review="reviewer-edit">Editar</button><button data-ps-review="reviewer-delete">Excluir nota</button></div>';
    document.body.prepend(element);
    return element;
  }

  function rememberQuestionPanel() {
    const front = document.querySelector("#qa .ps-review-panel--question");
    if (front?.dataset.psCardId) {
      currentQuestion = { cardId: front.dataset.psCardId, panel: front };
    }
  }

  function keepAnswerOnly(back) {
    const content = back.querySelector(".ps-review-panel__content");
    const divider = content?.querySelector("hr#answer");
    if (!content || !divider) return;
    while (content.firstChild && content.firstChild !== divider) {
      content.removeChild(content.firstChild);
    }
    divider.remove();
  }

  function showAnswerBelowQuestion() {
    const qa = document.getElementById("qa");
    const back = qa?.querySelector(".ps-review-panel--answer");
    if (!qa || !back || !currentQuestion || back.dataset.psCardId !== currentQuestion.cardId)
      return;

    keepAnswerOnly(back);
    // Anki may replace #qa when it reveals an answer. The question panel is
    // retained by this module and then restored as the first visual block.
    qa.replaceChildren(currentQuestion.panel, back);
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-ps-review]");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    send(button.dataset.psReview);
  });

  window.powerfulStudiesReview = {
    show(data) {
      const element = header();
      const breadcrumb = element.querySelector(".ps-review-breadcrumb");
      breadcrumb.replaceChildren();
      data.breadcrumb.forEach((part, index) => {
        if (index) breadcrumb.append(" / ");
        const item = document.createElement("span");
        item.textContent = part;
        breadcrumb.append(item);
      });
      document.body.classList.add("ps-review-enabled");
      document.body.classList.toggle("ps-review-compat", Boolean(data.compatibility));
      document.body.classList.toggle("ps-review-layout", Boolean(data.visualLayout));
      document.body.classList.toggle("ps-review-base-type", Boolean(data.baseTypography));
      document.body.classList.toggle("ps-review-highlight-answer", Boolean(data.highlightAnswer));
      document.documentElement.style.setProperty("--ps-review-card-width", `${data.cardWidth}px`);
      if (data.side === "answer") showAnswerBelowQuestion();
      else rememberQuestionPanel();
    },
    clear() {
      document.body.classList.remove(
        "ps-review-enabled",
        "ps-review-compat",
        "ps-review-layout",
        "ps-review-base-type",
        "ps-review-highlight-answer",
      );
      document.getElementById(rootId)?.remove();
      currentQuestion = null;
    },
  };
})();
