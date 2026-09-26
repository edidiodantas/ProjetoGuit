# Furyu — primeira fatia do chat

Código do chat baseado em [trypear/pearai-submodule](https://github.com/trypear/pearai-submodule) no commit `51eceef62a90c29f712b3a9607ea70a9dca657e9`. A licença continua Apache 2.0 (`LICENSE`).

Esta pasta é só a fatia do modo local. O aplicativo Python na raiz (`main.py`, `services/`, `static/`, `tests/`, `docs/manual.md`) não faz parte dela. O spec continua em `docs/furyu/`.

## O que esta fatia faz

- O perfil `local` grava `allowAnonymousTelemetry` e `sendAnonymousTelemetry` como `false`, pede resposta em português do Brasil e usa embeddings no Ollama (`nomic-embed-text`) ou `transformers.js` se esse modelo não estiver instalado.
- `Telemetry.setup(false)` roda antes do primeiro `streamChat`. Com a flag desligada não há GET para `https://server.trypear.ai/pearai-server-api2/anonymousTelemetry`.
- O PostHog não chama `init` nem `opt_in_capturing` quando `allowAnonymousTelemetry` não é `true`.
- Catálogo i18next `en` e `pt-BR`, namespaces `onboarding` e `errors`. A interface desta fatia abre em pt-BR.
- O splash oferece «Usar neste computador» e «Usar um modelo online» antes do `pearaiLogin`, também no overlay.
- Se o `listModels` do Ollama falha, a mensagem é «Modelo local não encontrado. Verifique se o Ollama está rodando ou mude para o modo Online.» A ação troca o perfil pelo `ProfileSwitcher` existente (`didChangeSelectedProfile`). Não há outro seletor de modelo.

## Testes

```bash
cd furyu
npm install
npm test
```
