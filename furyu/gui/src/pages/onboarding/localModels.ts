/**
 * `Ollama.ts` engole o erro de `/api/show`. O `LocalOnboarding` só vê
 * `llm/listModels`. Falha nessa lista é o modelo local ausente.
 */
export async function observeOllamaModels(
  listModels: () => Promise<unknown>,
): Promise<{ ok: true; models: string[] } | { ok: false; failure: "ollama-missing" }> {
  try {
    const models = await listModels();
    if (!Array.isArray(models) || models.some((item) => typeof item !== "string")) {
      return { ok: false, failure: "ollama-missing" };
    }
    return { ok: true, models };
  } catch {
    return { ok: false, failure: "ollama-missing" };
  }
}
