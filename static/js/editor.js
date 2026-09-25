/** Monaco editor setup and model lifecycle. */

import { DEFAULT_LANGUAGE, DEFAULT_CODE } from "./config.js";

/**
 * @typedef {import("monaco-editor").editor.IStandaloneCodeEditor} IStandaloneCodeEditor
 * @typedef {import("monaco-editor").editor.IStandaloneDiffEditor} IStandaloneDiffEditor
 * @typedef {import("monaco-editor").editor.ITextModel} ITextModel
 */

/** Bootstrap the Monaco loader and return the global `monaco` object. */
export async function loadMonaco() {
  return new Promise((resolve, reject) => {
    if (window.monaco) {
      resolve(window.monaco);
      return;
    }

    require.config({
      paths: {
        vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs",
      },
    });

    require(["vs/editor/editor.main"], () => {
      if (window.monaco) {
        resolve(window.monaco);
      } else {
        reject(new Error("Monaco editor failed to load"));
      }
    }, reject);
  });
}

/** Create a text model with the given value and language. */
export function createModel(monaco, value, language) {
  return monaco.editor.createModel(value || "", language);
}

/** Update the language mode of an existing model. */
export function setModelLanguage(monaco, model, language) {
  if (model) {
    monaco.editor.setModelLanguage(model, language);
  }
}

/** Dispose a model safely. */
export function disposeModel(model) {
  if (model) {
    model.dispose();
  }
}

/**
 * Build the original editor and the diff editor, then wire the initial models.
 * @returns {Promise<{originalEditor: IStandaloneCodeEditor, diffEditor: IStandaloneDiffEditor, originalModel: ITextModel, modifiedModel: ITextModel}>}
 */
export async function initEditors(originalContainer, diffContainer) {
  const monaco = await loadMonaco();

  const originalModel = createModel(monaco, DEFAULT_CODE, DEFAULT_LANGUAGE);

  const originalEditor = monaco.editor.create(originalContainer, {
    model: originalModel,
    theme: "vs",
    automaticLayout: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    fontSize: 14,
  });

  const diffEditor = monaco.editor.createDiffEditor(diffContainer, {
    theme: "vs",
    automaticLayout: true,
    readOnly: true,
    renderSideBySide: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    fontSize: 14,
  });

  const modifiedModel = createModel(monaco, DEFAULT_CODE, DEFAULT_LANGUAGE);
  diffEditor.setModel({ original: originalModel, modified: modifiedModel });

  return { originalEditor, diffEditor, originalModel, modifiedModel };
}
