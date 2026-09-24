/** Main application wiring for the Kimi Vibe composer UI. */

import { DEFAULT_LANGUAGE, DEFAULT_CODE } from "./config.js";
import { initEditors, setModelLanguage, disposeModel, createModel } from "./editor.js";
import { composeCode } from "./api.js";

async function main() {
  const originalContainer = document.getElementById("originalEditor");
  const diffContainer = document.getElementById("diffEditor");
  const promptInput = document.getElementById("prompt");
  const languageSelect = document.getElementById("language");
  const composeBtn = document.getElementById("composeBtn");
  const resetBtn = document.getElementById("resetBtn");
  const statusEl = document.getElementById("status");

  function setStatus(message, type = "") {
    statusEl.textContent = message;
    statusEl.className = "status " + type;
  }

  let { originalModel, modifiedModel, diffEditor } = await initEditors(
    originalContainer,
    diffContainer
  );

  async function onCompose() {
    if (!originalModel || !diffEditor) {
      setStatus("Editor is still loading.", "error");
      return;
    }

    const code = originalModel.getValue();
    const prompt = promptInput.value.trim();
    const language = languageSelect.value;

    if (!prompt) {
      setStatus("Enter a prompt first.", "error");
      promptInput.focus();
      return;
    }

    setStatus("Asking Kimi/Moonshot...");
    composeBtn.disabled = true;

    try {
      const data = await composeCode(code, prompt, language);
      const explanation = data.explanation || "Done.";
      const updatedCode = data.code || code;

      setStatus(explanation.split("\n")[0], "success");

      disposeModel(modifiedModel);
      modifiedModel = createModel(window.monaco, updatedCode, language);
      diffEditor.setModel({ original: originalModel, modified: modifiedModel });
    } catch (error) {
      setStatus(`Error: ${error.message}`, "error");
      console.error("Compose failed:", error);
    } finally {
      composeBtn.disabled = false;
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
    setStatus("");
  }

  languageSelect.addEventListener("change", () => {
    const language = languageSelect.value;
    setModelLanguage(window.monaco, originalModel, language);
    setModelLanguage(window.monaco, modifiedModel, language);
  });

  composeBtn.addEventListener("click", onCompose);
  resetBtn.addEventListener("click", onReset);

  promptInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      onCompose();
    }
  });
}

main().catch((error) => {
  console.error("Failed to start Kimi Vibe UI:", error);
});
