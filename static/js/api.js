/** Cliente da API de backend. */

import { API_ENDPOINT } from "./config.js";

const REQUEST_TIMEOUT_MS = 70000;

/**
 * Erro enriquecido com o tipo retornado pelo backend (``error_type``) e o
 * status HTTP. O frontend pode escolher uma mensagem amigável de acordo com
 * o tipo.
 */
export class ApiError extends Error {
  constructor(message, errorType, status) {
    super(message);
    this.errorType = errorType;
    this.status = status;
  }
}

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
      const errorType = payload.error_type || "generic";
      const message =
        payload.message || `Requisição falhou (${response.status})`;
      throw new ApiError(message, errorType, response.status);
    }

    return payload.data || {};
  } catch (error) {
    if (error.name === "AbortError") {
      throw new ApiError(
        "A requisição demorou muito. Tente novamente em breve.",
        "timeout",
        408
      );
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}
