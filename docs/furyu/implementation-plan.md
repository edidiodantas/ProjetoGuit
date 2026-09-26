# Plano de implementação — Furyu

Leitura do código público em 26 de setembro de 2026. Nenhum fork foi criado.

Commits lidos:

| Repositório | Commit |
| --- | --- |
| `trypear/pearai-app` `main` | `d930f0233c14668df9f85c6a78a81828f4251194` (2025-05-15) |
| `trypear/pearai-submodule` `main` | `51eceef62a90c29f712b3a9607ea70a9dca657e9` (2026-06-19) |
| `trypear/PearAI-Roo-Code` `main` | `0b6df736c9b2799c38b9ee629668407521a7bdda` (2026-06-19) |

O editor que o usuário vê é três projetos. A casca é o fork do VS Code. O chat, a indexação e os provedores de modelo estão no fork do Continue. O agente que cria arquivos e pede aprovação está no fork do Roo Code.

## Repositórios

### Os que o app consome

| Papel | URL | Branch padrão | Licença no GitHub | Upstream |
| --- | --- | --- | --- | --- |
| Casca do editor | https://github.com/trypear/pearai-app | `main` | MIT (`LICENSE.txt`, copyright Microsoft). O README do mesmo repo diz Apache 2.0; o arquivo de licença e o metadado do GitHub são MIT | `microsoft/vscode` |
| Extensão de chat | https://github.com/trypear/pearai-submodule | `main` | Apache 2.0 | `continuedev/continue` |
| Agente | https://github.com/trypear/PearAI-Roo-Code | `main` | Apache 2.0 | `RooCodeInc/Roo-Code` |

`pearai-app` está em VS Code 1.96.4 (`package.json`). `product.json` marca `nameShort` PearAI, `pearAIVersion` 2.0.0, `dataFolderName` `.pearai`, `enableTelemetry` true. Último push do app: 2025-05-20. Submodule e Roo seguiram até junho de 2026.

Cada fork do Furyu conserva a licença do repositório de origem. O README do app, que afirma Apache 2.0, fica como está até decisão explícita de licença.

### Como o app consome o submodule

`.gitmodules` na raiz de `pearai-app`:

- `extensions/pearai-submodule` → `https://github.com/trypear/pearai-submodule.git`, `branch = main`
- `extensions/PearAI-Roo-Code` → `https://github.com/trypear/PearAI-Roo-Code`, `branch = main`

`scripts/pearai/setup-environment.sh` faz o resto:

1. `git submodule update --init --recursive`
2. `git submodule update --recursive --remote` (acompanha a ponta de `main`, ignora o SHA pinado)
3. Symlink `extensions/pearai-ref` → `extensions/pearai-submodule/extensions/vscode`
4. `./scripts/install-and-build.sh` dentro do submodule e, em seguida, `git reset --hard`
5. `npm run install:all` e `npm run build` em `extensions/PearAI-Roo-Code`
6. `npm install` na raiz do app

A extensão publicada no VS Code é `pearai.pearai` 2.0.0 (`extensions/vscode/package.json` do submodule). As views são `pearai.chatView`, `pearai.searchView`, `pearai.mem0View`, `pearai.creatorView` e o overlay `pearai.overlayView` (`extensions/vscode/src/util/pearai/pearaiViewTypes.ts`). O `CONTRIBUTING.md` do app descreve o empacotamento manual: `npm run package` gera um `.vsix`, que é copiado para `extensions/` do app empacotado.

O `main` atual do app perdeu os gitlinks. `extensions/pearai-submodule` e `extensions/PearAI-Roo-Code` respondem 404 na árvore de `d930f02` e na tag `v2.0.0-beta-linux` (2025-05-16). O último commit que ainda os contém é `2e813e51` (2025-04-14, “Update .gitmodules”) e a tag `v1.8.9-Linux`, com estes SHAs:

- submodule `c85d5d314912a926136c7d1a1c4137f374b7b298` (2025-02-06, “Added working inventory”)
- Roo `18607dac7a33424389c7e08cbd2352de0aa3dee6` (2025-03-22)

Esses pinos estão mais de um ano atrás das pontas lidas acima. `git submodule update --init` no `main` atual não clona nada, porque não há gitlink.

### Irmãos que o editor não compila

| URL | Branch | Licença | Relação |
| --- | --- | --- | --- |
| https://github.com/trypear/pearai-master | `main` | nenhuma no GitHub | Agregador. O `.gitmodules` lista app, submodule, Roo, landing, documentação, `pearai-server`, `pearai-mcp` e o repo de issues. `update_submodules.sh` faz checkout de `origin/main` em todos, exceto o server |
| https://github.com/trypear/pearai-documentation | `main` | nenhuma | Docs em inglês (`docs/index.md`). Site citado como https://trypear.ai/docs |
| https://github.com/trypear/pear-landing-page | `main` | Apache 2.0 | Site, fora do build do editor |
| https://github.com/trypear/pearai-server-issues-public | `main` | nenhuma | Só issues |
| https://github.com/trypear/pearai-aider | `main` | Apache 2.0 | Fork separado. O app não o referencia. O chat tem uma integração própria em `gui/src/integrations/aider/` |

`pearai-server` e `pearai-mcp` aparecem no `.gitmodules` do master e a API pública devolve 404. O cliente do server está no submodule: `SERVER_URL = "https://server.trypear.ai/pearai-server-api2"` em `core/util/parameters.ts`.

## Estado atual

### pt-BR e i18n

Três superfícies, três mecanismos.

A casca do VS Code já usa `nls.localize` (`src/vs/nls.ts`). As traduções oficiais vêm de um language pack, não do repositório. `product.json` aponta `extensionsGallery.nlsBaseUrl` para `https://www.vscode-unpkg.net/_lp/` e a galeria para `https://market.trypear.ai`. Não há `package.nls.pt-BR.json` nem language pack dentro do app. Textos novos do Pear, como “Get Started With PearAI” em `src/vs/workbench/contrib/welcomeGettingStarted/common/gettingStartedContent.ts`, usam chaves próprias e ficam em inglês mesmo com o pack da Microsoft instalado. O locale do editor é o de `argv.json` / “Configure Display Language”.

O submodule do chat não tem catálogo. Não há `i18next`, `useTranslation` nem pasta `locales` em `gui/`. As frases estão no JSX: `gui/src/pages/onboarding/Onboarding.tsx` (“Welcome to PearAI!”, “Begin your journey by logging in”), `gui/src/pages/onboarding/LocalOnboarding.tsx`, `gui/src/pages/welcome/splashScreen.tsx` (“Welcome to PearAI”).

O Roo já tem i18n completa. `webview-ui/src/i18n/setup.ts` carrega `locales/**/*.json`. pt-BR cobre `chat.json` (162 chaves, paridade com o inglês), `settings.json`, `common.json`, `welcome.json`, `history.json`, `mcp.json`, `prompts.json`, `humanRelay.json`, mais `src/i18n/locales/pt-BR/` e `package.nls.pt-BR.json` (29/29). O idioma segue `vscode.env.language` via `formatLanguage` em `src/shared/language.ts`. Sem language pack no editor, `vscode.env.language` não é `pt-BR` e o agente permanece em inglês. Há seletor próprio: a UI chama `i18n.changeLanguage(extensionState.language)`.

A documentação em `pearai-documentation` está em inglês.

### Ollama e outros provedores locais

O Continue já fala com servidor local.

| Provedor | Classe | Base padrão | UI |
| --- | --- | --- | --- |
| Ollama | `core/llm/llms/Ollama.ts` | `http://localhost:11434/` | `gui/src/pages/AddNewModel/configs/providers.ts` (`ollama`) |
| LM Studio | `core/llm/llms/LMStudio.ts` | `http://localhost:1234/v1/` | mesmo arquivo (`lmstudio`) |
| llamafile | `core/llm/llms/Llamafile.ts` | — | `llamafile` |
| llama.cpp | `core/llm/llms/LlamaCpp.ts` | servidor local | `llama.cpp` |
| API compatível com OpenAI | provider `openai` com `apiBase` | placeholder `http://localhost:8000/v1/` | “Other OpenAI-compatible API” |

`core/config/onboarding.ts` `setupLocalMode` grava chat `llama3` e um modelo `AUTODETECT`, autocomplete `starcoder2:3b`, embeddings Ollama `nomic-embed-text`. `LocalOnboarding.tsx` acompanha o download com `ollama run llama3`, `starcoder2:3b` e `nomic-embed-text`, e faz polling de `llm/listModels` a cada 1 s.

Indexação local: `core/indexing/CodebaseIndexer.ts` (SQLite + LanceDB). Sem provedor de embeddings, `core/config/load.ts` cai em `TransformersJsEmbeddingsProvider` (`all-MiniLM-L6-v2` no comentário de `core/config/types.ts`). O modo local troca isso para Ollama.

O Roo repete Ollama e LM Studio em `src/api/providers/ollama.ts` e `lmstudio.ts`, nas mesmas portas.

O onboarding local recomenda `llama3`, modelo grande para o mínimo de 8 GB do RNF03. O texto do provedor cita exemplos `codellama:7b-instruct` e `llama2:7b-text`. Não há perfil de quantizado pequeno escolhido no código.

### Provedores online

No mesmo `providers.ts` e em `core/llm/llms/index.ts`: PearAI Server, OpenAI, Anthropic, Azure, OpenRouter, Mistral, Cohere, Groq, DeepSeek, Gemini, Together, Replicate, Hugging Face, Bedrock, Cloudflare, Fireworks, Flowise, DeepInfra, WatsonX, Perplexity, free trial.

PearAI Server (`core/llm/llms/PearAIServer.ts`) usa `PearAICredentials` e `https://server.trypear.ai/pearai-server-api2`. Login: `https://trypear.ai/signin?callback=pearai://pearai.pearai/auth` (`extensions/vscode/src/webviewProtocol.ts`). Conta e uso: `gui/src/inventory/pearSettings/general.tsx` e `hooks/useAccountSettings.ts`. Preço: `https://trypear.ai/pricing`.

O onboarding de chat começa pelo login (`Onboarding.tsx`). Dá para pular, com um aviso de que isso é desaconselhado sem `config.json`.

Troca de modelo no chat: `gui/src/components/modelSelection/ModelSelect.tsx`. O menu lista os modelos do perfil, atalho Ctrl/Cmd+`'`, e não reinicia o editor. Perfis: `core/config/ConfigHandler.ts` e `gui/src/components/ProfileSwitcher.tsx`. O perfil `"local"` existe. Não existe um interruptor único “modo local / modo online” que também desligue telemetria, login e prompt do sistema.

Sincronização de configurações do editor continua a do VS Code: `product.json` `configurationSync.store` aponta para `https://vscode-sync.trafficmanager.net/`, com login GitHub ou Microsoft.

### Aprovação do agente

A UI de aprovação está no Roo, não no submodule.

- Botões: `webview-ui/src/components/chat/ChatRow.tsx`, `ChatView.tsx`, `AutoApproveMenu.tsx`
- Configuração: `webview-ui/src/components/settings/AutoApproveSettings.tsx`
- Execução: `src/core/Cline.ts`, `src/core/webview/webviewMessageHandler.ts`

pt-BR já diz “Aprovar” / “Aprovar esta ação” (`webview-ui/src/i18n/locales/pt-BR/chat.json`) e descreve aprovação automática de leitura, edição, terminal, MCP e subtarefas (`settings.json`). O padrão pede aprovação. A aprovação automática é opt-in, com texto de risco.

O agente também tem provedor PearAI em `src/api/providers/pearai/`.

### Telemetria e autenticação

Vários canais, com opt-out incompleto.

| Canal | Onde | Comportamento lido |
| --- | --- | --- |
| PostHog no GUI | `gui/src/hooks/CustomPostHogProvider.tsx` | Chave `phc_EixCfQZYA5It6ZjtZG2C8THsUQzPzXZsdCsvR8AYhfh`, host `https://us.i.posthog.com`. Identifica `vscMachineId` e, se houver login, o id Pear. O `useEffect` chama `posthog.init` e `opt_in_capturing` sempre. `allowAnonymousTelemetry` só decide se o `PostHogProvider` envolve a árvore |
| Telemetria anônima ao server Pear | `core/llm/index.ts` `streamChat` → `core/pearaiServer/util.ts` `anonymousTelemetryLog` | Se `Telemetry.allow`, GET `${SERVER_URL}/anonymousTelemetry` com model, provider e event. O comentário diz que o conteúdo do prompt não vai. O comentário cita a chave `sendAnonymousTelemetry`; o código usa `allowAnonymousTelemetry` |
| Default | `core/config/load.ts` | `allowAnonymousTelemetry` vira `true` se omitido. `core/config/profile/doLoadConfig.ts` faz AND com `ide.isTelemetryEnabled()` |
| PostHog no core | `core/util/posthog.ts` | O cliente `posthog-node` está comentado. `Telemetry.allow` ainda governa o GET acima |
| Editor | `product.json` | `enableTelemetry: true`, `showTelemetryOptOut: true`, `aiConfig.ariaKey` da Microsoft, `crashReporter` productName `VSCode` / companyName `Microsoft` |
| Settings Sync | `product.json` | Host Microsoft, contas GitHub/Microsoft |

Memórias “mem0” gravam JSON em `~/.pearai` (`extensions/vscode/src/integrations/mem0/localMemoryService.ts`). A integração vem ligada em `core/config/default.ts`. O arquivo lido não chama a API da Mem0.

Free trial exige telemetria: `core/llm/llms/FreeTrial.ts`.

## Requisitos

### RF01 — Português nativo

Existe: `nls` na casca; i18n pt-BR pronta no Roo, condicionada ao locale do editor; prompts de sistema em inglês só nos modelos free trial (`core/config/default.ts`, “You are an expert software developer…”). `setupLocalMode` não define `systemMessage`.

Lacuna: casca sem pack pt-BR embutido e com strings Pear fora do pack da Microsoft; chat, onboarding, erros e docs em inglês; o modelo local não é instruído a responder em português.

Arquivos: language pack novo ao lado de `extensions/` em `pearai-app` (sem editar cada `nls.localize`); chaves Pear em `src/vs/workbench/contrib/welcomeGettingStarted/common/gettingStartedContent.ts` e `product.json` (`nameShort` já é PearAI); catálogo novo `gui/src/i18n/` no submodule; `systemMessage` no perfil local; docs só se o produto passar a embutir o site — o repo `pearai-documentation` é separado.

### RF02 — Modo local offline

Existe: Ollama, LM Studio, llama.cpp, llamafile e API local; indexação LanceDB/SQLite; embeddings `transformers.js` ou Ollama; onboarding local; memórias em arquivo local.

Lacuna: o primeiro fluxo pede login Pear; telemetria do editor, PostHog, `anonymousTelemetryLog` e Settings Sync saem da máquina enquanto não forem desligados; o pack de idioma, se instalado pela galeria, depende de rede (`vscode-unpkg.net` e `market.trypear.ai` — este host não resolveu nesta leitura, então a galeria não foi verificada); `llama3` precisa ser baixado.

Arquivos: `core/config/onboarding.ts`, `core/config/furyu/` (novo), `core/llm/index.ts`, `gui/src/hooks/CustomPostHogProvider.tsx`, `product.json` (`enableTelemetry`, `configurationSync.store`), `gui/src/pages/onboarding/Onboarding.tsx`.

### RF03 — Modo online

Existe: chaves em `providers.ts` para OpenAI, Anthropic e os demais; PearAI Server como hosted; “Other OpenAI-compatible API” cobre servidor próprio; Settings Sync do VS Code.

Lacuna: sync é o serviço Microsoft, não um sync do Furyu; o modo online não é um perfil nomeado que o usuário ligue ao lado do local; login Pear e free trial continuam no caminho padrão.

Arquivos: `gui/src/pages/AddNewModel/configs/providers.ts`, `core/llm/llms/PearAIServer.ts`, `core/util/parameters.ts`, `gui/src/inventory/pearSettings/general.tsx`, `product.json`.

### RF04 — Alternância sem reiniciar

Existe: `ModelSelect.tsx` troca o modelo na sessão; `ConfigHandler.ts` troca perfil e chama `reloadConfig` (`core/core.ts`).

Lacuna: falta um controle único que troque provedor, prompt em português, telemetria e login juntos. Trocar só o modelo deixa o PostHog e o `streamChat` no estado anterior.

Arquivos: `gui/src/components/modelSelection/ModelSelect.tsx`, `gui/src/components/ProfileSwitcher.tsx`, `core/config/ConfigHandler.ts`, perfil novo em `core/config/furyu/`.

### RF05 — Agente com aprovação em português

Existe: agente Roo com aprovação explícita e cópia pt-BR completa, desde que o locale seja `pt-BR`.

Lacuna: o locale efetivo segue o editor, que abre em inglês sem language pack; o prompt do agente não pede resposta em português; o submodule de chat não é o agente.

Arquivos: `PearAI-Roo-Code` `webview-ui/src/i18n/locales/pt-BR/chat.json`, `src/shared/language.ts`, `src/core/webview/ClineProvider.ts` (onde o language entra no estado), prompts do agente no mesmo repo. A casca precisa default `pt-BR` para essa UI aparecer em português.

### RF06 — i18n estruturada

Existe: JSON + i18next no Roo, inclusive pt-BR e outros idiomas já entregues pelo upstream. A casca usa o mecanismo de language pack do VS Code.

Lacuna: o submodule, que concentra chat e onboarding, não tem JSON de tradução. Outros idiomas ficam de fora do escopo; a estrutura no submodule precisa nascer com `en` e `pt-BR` para não espalhar strings novas no JSX.

Arquivos novos: `pearai-submodule/gui/src/i18n/setup.ts` e `gui/src/i18n/locales/{en,pt-BR}/*.json`. Roo permanece como está nesta fatia.

### RF07 — Onboarding e tutoriais em português

Existe: splash e setup em `gui/src/pages/welcome/` (`splashScreen.tsx`, `SetupPage.tsx`, `setup/SignIn.tsx`, `InstallTools.tsx`); onboarding de modelo em `gui/src/pages/onboarding/`; walkthrough “Get Started With PearAI” em `gettingStartedContent.ts`, ainda com passos de Copilot.

Lacuna: todo esse texto está em inglês; o setup não explica modo local versus online; não há tutorial de vibe coding em pt-BR.

Arquivos: os de welcome/onboarding acima, mais o walkthrough do app na fatia da casca.

### RNF01 — Privacidade no modo local

Existe: inferência local não envia o prompt ao provedor remoto; o comentário de `anonymousTelemetryLog` diz que o corpo do pedido não vai nesse GET; memórias locais; free trial declara que modelo próprio não exige telemetria.

Lacuna: o default liga telemetria; o GUI inicializa o PostHog mesmo com a flag falsa; `streamChat` chama o server Pear quando `Telemetry.allow` é true, inclusive com Ollama; o editor manda telemetria Microsoft (`ariaKey`) e o crash reporter está ativo; Settings Sync fala com a Microsoft se o usuário entrar. Indexação com embeddings `free-trial` ou PearAI Server sairia da máquina — o `setupLocalMode` já evita isso ao usar Ollama.

Arquivos: `CustomPostHogProvider.tsx`, `core/llm/index.ts`, `core/config/load.ts`, `core/pearaiServer/util.ts`, `product.json`.

### RNF02 — UI abaixo de 100 ms, editor livre enquanto a IA responde

Existe: chat por stream assíncrono (`streamChat` / webview). A geração não é um request bloqueante da UI do workbench.

Lacuna: não há orçamento medido de 100 ms. `LocalOnboarding` dispara `llm/complete` ao detectar o modelo, o que carrega o modelo na máquina e pode travar o webview. Indexação LanceDB compete com a UI em máquina de 8 GB.

Arquivos: `gui/src/pages/onboarding/LocalOnboarding.tsx`, `core/indexing/CodebaseIndexer.ts`, `gui/src/hooks/useChatHandler.ts`.

### RNF03 — 8 GB, GPU integrada, quantizados

Existe: Ollama e LM Studio aceitam o modelo que o usuário já baixou, inclusive GGUF via LM Studio / llama.cpp. Autocomplete de exemplo é `starcoder2:3b`.

Lacuna: o chat padrão do modo local é `llama3`, sem tag quantizada pequena. Não há teste de memória nem seleção automática por RAM.

Arquivos: `core/config/onboarding.ts`, `LocalOnboarding.tsx`, `providers.ts` (texto que cita `codellama:7b-instruct`). A tag exata do modelo pequeno é decisão de produto, não está fechada no código.

### RNF04 — Troca local/online clara, pouco intrusiva

Existe: seletor de modelo no campo de chat e tags `Local` / `RequiresApiKey` em `providers.ts` (`ModelProviderTag`).

Lacuna: a troca de modo está espalhada entre login, onboarding, menu de modelo e Settings do VS Code. Não há um indicador persistente “Local” / “Online”.

Arquivos: `ModelSelect.tsx`, `ProfileSwitcher.tsx`, splash/onboarding.

### RNF05 — Customização separada do upstream

Existe: o próprio Pear já separa casca, submodule e Roo, e o README do master pede cuidado ao puxar upstream. O setup atual trabalha contra isso: `--remote` mais `git reset --hard` apaga mudança local no submodule, e o `main` do app perdeu os gitlinks.

Lacuna e desenho: seção seguinte.

### RNF06 — Erro em português com alternativa

Existe: `extensions/vscode/src/webviewProtocol.ts` traduz falha de rede para inglês. `ECONNREFUSED` vira “Connection was refused…” e aponta `apiBase` / docs em trypear.ai. Falha de login Pear abre “Login To PearAI”. O construtor de `Ollama.ts` engole erro de `/api/show`.

Lacuna: não há a frase “Modelo local não encontrado. Verifique se o Ollama está rodando ou mude para o modo Online.”

Arquivos: `webviewProtocol.ts`, `core/llm/llms/Ollama.ts`, `core/llm/llms/LMStudio.ts`, catálogo `gui/src/i18n/locales/pt-BR/errors.json`.

## Fork e sync (RNF05)

Três forks, um remote `upstream` cada, SHA pinado no app. Customização só em diretórios que o upstream não possui, mais um arquivo de marca inevitável.

| Fork | Upstream | O que é do Furyu | O que o merge upstream continua dono |
| --- | --- | --- | --- |
| app | `trypear/pearai-app` | `extensions/furyu-pt-br/` (pack e chaves só do Furyu); `product.json` só nas chaves de nome, locale padrão e telemetria | `src/vs/**` |
| submodule | `trypear/pearai-submodule` | `gui/src/i18n/**`; `core/config/furyu/**` (perfil local, prompt pt-BR, telemetria off) | `core/llm/**`, `gui/src/pages/**` exceto o encaixe mínimo do `t()` |
| Roo | `trypear/PearAI-Roo-Code` | um default de idioma pt-BR num ponto só (`formatLanguage` / estado inicial). As strings pt-BR já são upstream | `webview-ui/src/i18n/locales/**` |

Regras de sync:

1. Restaurar os gitlinks a partir de `2e813e51` e piná-los nos SHAs do Furyu. Parar de usar `git submodule update --remote` e o `git reset --hard` de `setup-environment.sh` nos checkouts do Furyu. Esse script aponta para o GitHub do Pear e apaga o trabalho local.
2. O primeiro sync do app não é um rebase para o VS Code atual. A casca parou em 1.96.4 (dezembro de 2024 no `product.json`). Subir de versão do VS Code é outro projeto.
3. O submodule e o Roo de junho de 2026 são a base do Furyu. O pino de fevereiro/março de 2025 dentro do app antigo não é a base do chat.
4. Conflito esperado fica em `product.json` e nos poucos call sites do `t()`. JSON novo e `core/config/furyu/` não conflitam com o Continue.
5. `pearai-master` não entra no fork. É um agregador sem licença e com submódulos privados.

Publicar esses remotes depende das decisões abaixo. Até lá o trabalho pode viver em patches locais, sem push.

## Primeira fatia

Só o submodule. Sem empacotar o VS Code, sem language pack, sem mexer no Roo. Cabe numa sequência curta e deixa a casca em inglês de propósito.

1. **Cortar saída de rede no perfil local.** Em `CustomPostHogProvider.tsx`, não chamar `posthog.init` nem `opt_in_capturing` quando `allowAnonymousTelemetry` é false. Em `core/config/furyu/localMode.ts`, forçar `allowAnonymousTelemetry: false` e provedor de embeddings local (`ollama` / `nomic-embed-text`, com fallback `transformers.js` se o Ollama não tiver o modelo de embedding). Conferir que `Telemetry.setup` recebe false antes do primeiro `streamChat`.
2. **Catálogo.** Criar `gui/src/i18n/setup.ts` no estilo do Roo (`i18next`, JSON por namespace) com `en` e `pt-BR`. Namespaces desta fatia: `onboarding` e `errors`.
3. **Textos desta fatia.** Passar para o catálogo: `splashScreen.tsx`, `Onboarding.tsx`, `LocalOnboarding.tsx` e as mensagens de `webviewProtocol.ts` (`ECONNREFUSED`, timeout, falha genérica). A mensagem de Ollama recusado usa o texto do RNF06 e oferece mudar para online.
4. **Entrada local antes do login.** O splash oferece “Usar neste computador” e “Usar um modelo online”. O primeiro aplica `localMode` e não chama `pearaiLogin`. O segundo mantém o fluxo atual de chaves / PearAI Server.
5. **Prompt.** O modelo do perfil local recebe `systemMessage` pedindo resposta em português do Brasil.
6. **Troca já existente.** Não reimplementar `ModelSelect`. O perfil local e o online aparecem no `ProfileSwitcher`. A troca continua sem reinício.

Fora desta fatia: pack pt-BR da casca, tutoriais, default de idioma do Roo, escolha do quantizado de 8 GB, branding, instalador.

### Riscos da fatia

- O `useEffect` do PostHog hoje inicializa o cliente mesmo com a flag falsa. A fatia falha o RNF01 se só gravar a flag no JSON.
- `anonymousTelemetryLog` usa `Telemetry.allow`, não a string `sendAnonymousTelemetry` do comentário. Os dois nomes precisam ser unificados no perfil, senão um opt-out no `config.json` não desliga o GET.
- `setup-environment.sh` do app, se alguém o rodar num clone do submodule Furyu aninhado, dá `reset --hard` na ponta do Pear e apaga `core/config/furyu/`.
- `Onboarding.tsx` manda o overlay direto para `/` (`window.isPearOverlay`). O splash novo tem que valer nesse caminho, senão o overlay continua caindo no login.
- Erros de Ollama engolidos em `Ollama.ts` (`/api/show`) não chegam ao `webviewProtocol`. A mensagem do RNF06 precisa nascer também quando `listModels` falha, que é o que `LocalOnboarding` já observa.
- A casca, os menus do VS Code e o agente continuam em inglês. Esta fatia não fecha RF01.
- `llama3` pode não caber em 8 GB. A fatia não troca o modelo padrão; isso fica em aberto.

### Depois, em ordem

1. Pack pt-BR embutido na casca e locale padrão `pt-BR`, para o Roo passar a abrir em português sem trabalho novo de cópia.
2. Interruptor visível Local/Online no `ModelSelect`, reusando o perfil da fatia 1.
3. Default de idioma do agente e prompt em português no Roo.
4. Walkthrough e tutoriais, em cima do catálogo, não de strings novas soltas.
5. Restaurar gitlinks e o script de setup sem `--remote` nem `reset --hard`.

## Publicação

A conta ligada a este projeto é a pessoal `edidiodantas`. Em 26 de setembro de 2026 o plano foi para o único repositório em que o Cursor consegue escrever: [edidiodantas/ProjetoGuit](https://github.com/edidiodantas/ProjetoGuit), pasta `docs/furyu/`. Esse repositório também contém o tutor IPEIA. Criar um repositório separado `furyu` foi recusado pela integração do GitHub (`createRepository`).

Os forks do código (`pearai-app`, `pearai-submodule`, `PearAI-Roo-Code`) ainda não existem.

## Decisões ainda em aberto

- Organização ou só a conta pessoal: a publicação deste plano usou a conta pessoal porque era a única acessível. Uma org continua sem nome.
- Onde moram os forks do editor, quando forem criados: na mesma conta, numa org, ou neste repositório.
