# Furyu — chat

O código do chat está em [`pearai-submodule`](pearai-submodule), checkout de [trypear/pearai-submodule](https://github.com/trypear/pearai-submodule) no commit `51eceef62a90c29f712b3a9607ea70a9dca657e9` (arquivo `.furyu-upstream-commit`). A licença Apache 2.0 está em `pearai-submodule/LICENSE`.

A primeira fatia (perfil local sem telemetria, catálogos `en`/`pt-BR`, splash e erro do Ollama) está aplicada nessa árvore. O aplicativo Python na raiz e `docs/furyu/` não fazem parte dela.

Testes da fatia, sem instalar o monorepo:

```bash
node --experimental-strip-types --test furyu/pearai-submodule/furyu-tests/primeira-fatia.node-test.ts
```

O editor VS Code e a interface em `gui/` continuam dependendo de `npm install` e do build do PearAI. Nesta fatia isso não é executado.
