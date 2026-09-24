/** Cliente da API de backend. */

import { API_ENDPOINT } from "./config.js";

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
  const response = await fetch(API_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, prompt, language }),
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok || !payload.success) {
    const errorType = payload.error_type || "generic";
    const message =
      payload.message || `Requisição falhou (${response.status})`;
    throw new ApiError(message, errorType, response.status);
  }

  return payload.data || {};
}
