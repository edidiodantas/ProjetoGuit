/** Backend API client. */

import { API_ENDPOINT } from "./config.js";

/**
 * Send the code, prompt and language to the composer endpoint.
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
    throw new Error(
      payload.detail || payload.message || `Request failed (${response.status})`
    );
  }

  return payload.data || {};
}
