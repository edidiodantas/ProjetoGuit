/** Ligação principal da aplicação para a interface do IPEIA_VIBE_CODE. */

import { DEFAULT_LANGUAGE, DEFAULT_CODE } from "./config.js";
import { initEditors, setModelLanguage, disposeModel, createModel } from "./editor.js";
import { composeCode } from "./api.js";

const STATUS_ICONS = {
  info: "ℹ",
  success: "✓",
  warning: "⚠",
  error: "✕",
};

async function main() {
  const originalContainer = document.getElementById("originalEditor");
  const diffContainer = document.getElementById("diffEditor");
  const composeForm = document.getElementById("composeForm");
  const promptInput = document.getElementById("prompt");
  const languageSelect = document.getElementById("language");
  const composeBtn = document.getElementById("composeBtn");
  const resetBtn = document.getElementById("resetBtn");
  const statusEl = document.getElementById("status");
  const diffEmptyState = document.getElementById("diffEmptyState");

  let hasComposed = false;

  function setStatus(message, type = "") {
    statusEl.textContent = message;
    statusEl.className = "status" + (type ? ` ${type}` : "");
    if (type) {
      statusEl.setAttribute("role", type === "error" ? "alert" : "status");
    } else {
      statusEl.setAttribute("role", "status");
    }
  }

  function setLoading(isLoading) {
    composeBtn.disabled = isLoading;
    resetBtn.disabled = isLoading;
    composeForm.setAttribute("aria-busy", isLoading ? "true" : "false");
    composeBtn.classList.toggle("loading", isLoading);
  }

  function showDiffEmptyState(show) {
    if (show) {
      diffEmptyState.classList.remove("hidden");
    } else {
      diffEmptyState.classList.add("hidden");
    }
  }

  let { originalModel, modifiedModel, diffEditor } = await initEditors(
    originalContainer,
    diffContainer
  );

  async function onCompose(event) {
    if (event) {
      event.preventDefault();
    }

    if (!originalModel || !diffEditor) {
      setStatus("O editor ainda está carregando. Aguarde um instante.", "error");
      return;
    }

    const code = originalModel.getValue();
    const prompt = promptInput.value.trim();
    const language = languageSelect.value;

    if (!prompt) {
      setStatus("Digite um prompt descrevendo a melhoria desejada.", "warning");
      promptInput.focus();
      return;
    }

    if (!code.trim()) {
      setStatus("O editor original está vazio. Cole ou digite algum código primeiro.", "warning");
      originalContainer.focus();
      return;
    }

    setStatus("Consultando Kimi/Moonshot... isso pode levar alguns segundos.", "info");
    setLoading(true);

    try {
      const data = await composeCode(code, prompt, language);
      const explanation = data.explanation || "Composição concluída.";
      const updatedCode = data.code || code;

      const firstLine = explanation.split("\n")[0];
      setStatus(firstLine, "success");

      disposeModel(modifiedModel);
      modifiedModel = createModel(window.monaco, updatedCode, language);
      diffEditor.setModel({ original: originalModel, modified: modifiedModel });

      hasComposed = true;
      showDiffEmptyState(false);
      statusEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (error) {
      setStatus(`Erro: ${error.message}`, "error");
      console.error("Falha na composição:", error);
    } finally {
      setLoading(false);
    }
  }

  function onReset() {
    promptInput.value = "";
    languageSelect.value = DEFAULT_LANGUAGE;
    if (originalModel) {
      originalModel.setValue(DEFAULT_CODE);
      setModelLanguage(window.monaco, originalModel, DEFAULT_LANGUAGE);
    }
    if (diffEditor) {
      disposeModel(modifiedModel);
      modifiedModel = createModel(window.monaco, DEFAULT_CODE, DEFAULT_LANGUAGE);
      diffEditor.setModel({ original: originalModel, modified: modifiedModel });
    }
    hasComposed = false;
    showDiffEmptyState(true);
    setStatus("");
    promptInput.focus();
  }

  languageSelect.addEventListener("change", () => {
    const language = languageSelect.value;
    setModelLanguage(window.monaco, originalModel, language);
    setModelLanguage(window.monaco, modifiedModel, language);
  });

  composeForm.addEventListener("submit", onCompose);
  resetBtn.addEventListener("click", onReset);

  promptInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      onCompose();
    }
  });

  // Ajusta o estado inicial.
  showDiffEmptyState(true);
  setStatus("Pronto. Cole seu código, escreva o prompt e clique em Compor.", "info");
}

main().catch((error) => {
  console.error("Falha ao iniciar a interface IPEIA_VIBE_CODE:", error);
});
