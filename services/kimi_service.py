"""Cliente leve para a API compatível com OpenAI da Moonshot / Kimi."""

from __future__ import annotations

import os
import re
from typing import Optional

from openai import AsyncOpenAI, OpenAIError


class KimiServiceError(Exception):
    """Levantada quando o serviço Kimi/Moonshot não consegue completar uma requisição."""


class KimiService:
    """Chama a API de chat Kimi/Moonshot e interpreta a resposta em markdown.

    O modelo é configurável via argumento `model`, variável de ambiente
    `KIMI_MODEL` ou o padrão "kimi-latest". Para o plano gratuito da
    Moonshot, escolha um modelo menor (ex.: kimi-k2.5-lite) e salve-o no
    arquivo `.env` para economizar tokens.
    """

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
        # Modelo escolhido: prioridade é argumento > env > padrão.
        self.model = model or os.getenv("KIMI_MODEL", "kimi-latest")
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
            raise KimiServiceError("A KIMI_API_KEY não está configurada")

        instruction = (instruction or "").strip()
        if not instruction:
            raise KimiServiceError("O prompt de instrução não pode estar vazio")

        code = code or ""
        if len(code) > self.max_code_chars:
            raise KimiServiceError(
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
        except OpenAIError as exc:
            raise KimiServiceError(f"Erro na API Kimi: {exc}") from exc

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
