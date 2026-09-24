"""Cliente leve para a API compatível com OpenAI da Moonshot / Kimi."""

from __future__ import annotations

import os
import re
from typing import Optional

from openai import (
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    APIConnectionError,
    APIStatusError,
    OpenAIError,
    RateLimitError,
)


class KimiServiceError(Exception):
    """Base para erros traduzidos do serviço Kimi/Moonshot.

    Cada subclasse carrega um ``error_type`` estável (usado pelo frontend para
    identificar a mensagem amigável) e uma ``message`` em português.
    """

    error_type: str = "generic_api_error"
    default_message: str = "erro genérico da API"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class KimiAuthError(KimiServiceError):
    """Chave de API inválida ou não configurada."""

    error_type = "auth_error"
    default_message = "chave inválida ou não configurada"


class KimiRateLimitError(KimiServiceError):
    """Quota ou limite de requisições atingido."""

    error_type = "rate_limit"
    default_message = "limite de requisições atingido; aguarde ou verifique créditos"


class KimiServiceUnavailableError(KimiServiceError):
    """Erro temporário no serviço da Moonshot (HTTP 5xx)."""

    error_type = "service_unavailable"
    default_message = "erro temporário no serviço da Moonshot"


class KimiConnectionError(KimiServiceError):
    """Sem conexão com a internet ou serviço indisponível."""

    error_type = "connection_error"
    default_message = "sem conexão com a internet ou serviço indisponível"


class KimiInvalidRequestError(KimiServiceError):
    """Requisição inválida (prompt vazio, modelo inexistente, payload muito grande)."""

    error_type = "invalid_request"
    default_message = "requisição inválida"


class KimiService:
    """Chama a API de chat Kimi/Moonshot e interpreta a resposta em markdown."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        request_timeout: float = 60.0,
        max_code_chars: int = 32000,
    ) -> None:
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.base_url = base_url or os.getenv(
            "KIMI_BASE_URL", "https://api.moonshot.cn/v1"
        )
        self.model = model or os.getenv("KIMI_MODEL", "kimi-k2.5-lite")
        self.request_timeout = request_timeout
        self.max_code_chars = max_code_chars

        # Permite que o servidor inicie e sirva a interface sem uma chave, mas falhe
        # de forma clara quando o endpoint de composição for usado.
        self._client: Optional[AsyncOpenAI] = None
        if self.api_key:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.request_timeout,
            )

    @property
    def configured(self) -> bool:
        return self._client is not None

    async def compose(
        self,
        code: str,
        instruction: str,
        language: str = "python",
    ) -> dict[str, str]:
        """Solicita ao Kimi que reescreva *code* de acordo com *instruction*.

        Retorna um dicionário com:
            - explanation: texto livre antes do bloco de código.
            - code: o código atualizado extraído, ou o código original se nenhum for encontrado.
            - language: o identificador da linguagem passado.
        """
        if not self._client:
            raise KimiAuthError("A chave de API (KIMI_API_KEY) não está configurada")

        instruction = (instruction or "").strip()
        if not instruction:
            raise KimiInvalidRequestError("O prompt de instrução não pode estar vazio")

        code = code or ""
        if len(code) > self.max_code_chars:
            raise KimiInvalidRequestError(
                f"O código enviado excede o limite de {self.max_code_chars} caracteres"
            )

        system_prompt = (
            "Você é um tutor de programação útil, baseado na Kimi/Moonshot. "
            "O usuário fornece um código-fonte e uma instrução. "
            "Explique brevemente as alterações que você planeja fazer e, em seguida, forneça "
            "o código atualizado completo em um único bloco de código markdown cercado por ```. "
            "Se não houver alterações necessárias, diga isso e devolva o código original inalterado. "
            "Responda sempre em português do Brasil."
        )

        user_prompt = (
            f"Linguagem: {language}\n\n"
            f"Código original:\n```{language}\n{code}\n```\n\n"
            f"Instrução: {instruction}\n\n"
            "Por favor, responda com uma breve explicação seguida do bloco de código atualizado."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except AuthenticationError as exc:
            raise KimiAuthError() from exc
        except RateLimitError as exc:
            raise KimiRateLimitError() from exc
        except BadRequestError as exc:
            detail = getattr(exc, "message", None) or str(exc)
            raise KimiInvalidRequestError(f"requisição inválida: {detail}") from exc
        except APIConnectionError as exc:
            raise KimiConnectionError() from exc
        except APIStatusError as exc:
            if getattr(exc, "status_code", 0) >= 500:
                raise KimiServiceUnavailableError() from exc
            raise KimiServiceError(
                f"erro {getattr(exc, 'status_code', 'desconhecido')} na API Kimi"
            ) from exc
        except OpenAIError as exc:
            raise KimiServiceError(f"erro genérico da API: {exc}") from exc

        content = response.choices[0].message.content or ""
        return self._parse_response(content, fallback_code=code, language=language)

    @staticmethod
    def _parse_response(
        content: str,
        fallback_code: str,
        language: str,
    ) -> dict[str, str]:
        """Extrai a explicação e o último bloco de código cercado da resposta do modelo.

        Usar o último bloco é defensivo: se o modelo repetir o código original primeiro
        e depois o código atualizado, preferimos a atualização.
        """
        content = content.strip()
        if not content:
            return {
                "explanation": "O modelo retornou uma resposta vazia.",
                "code": fallback_code,
                "language": language,
            }

        # Match ``` optionally followed by a language tag, then any text until ```.
        code_block_re = re.compile(r"```(?:[^\n]*)\n(.*?)```", re.DOTALL)
        blocks = code_block_re.findall(content)

        if blocks:
            # Take the last code block to avoid picking up example snippets.
            code = blocks[-1].strip()
            # Remove all fenced blocks so the explanation only contains prose.
            explanation = code_block_re.sub("", content).strip()
            return {
                "explanation": explanation,
                "code": code,
                "language": language,
            }

        # No fenced block: treat the whole response as the explanation and keep code.
        return {
            "explanation": content,
            "code": fallback_code,
            "language": language,
        }
