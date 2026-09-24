/** Cliente da API de backend. */

import { API_ENDPOINT } from "./config.js";

const REQUEST_TIMEOUT_MS = 70000;

/**
 * Envia o código, o prompt e a linguagem para o endpoint de composição.
 * @returns {Promise<{explanation: string, code: string, language: string}>}
 */
export async function composeCode(code, prompt, language) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, prompt, language }),
      signal: controller.signal,
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok || !payload.success) {
      throw new Error(
        payload.detail || payload.message || `Requisição falhou (${response.status})`
      );
    }

    return payload.data || {};
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("A requisição demorou muito. Tente novamente em breve.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}
