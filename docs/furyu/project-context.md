# Furyu

Fork do PearAI (editor baseado no VS Code, com IA baseada no Continue) com português do Brasil nativo e dois modos de operação: local (offline) e online.

Idioma do produto e desta conversa: português (Brasil).

## Objetivo

Um editor em que o desenvolvedor escreve em português, escolhe se a IA roda na própria máquina ou na nuvem, e permanece no fluxo de trabalho. No modo local, código, prompts e uso não saem da máquina.

## Estratégia

1. Fork de `pearai-app` (fork do VS Code): interface, pacote de idioma pt-BR, onboarding.
2. Fork de `pearai-submodule` (baseado no Continue): escolha de provedor (local vs online), instrução do modelo em português, telemetria opcional.
3. i18n: aproveitar a internacionalização do VS Code com um pacote pt-BR; no submódulo, adicionar camada de tradução (arquivos JSON).
4. LLM local: o Continue já fala com Ollama; a configuração do fork deve tornar isso simples e em português (Ollama, LM Studio, modelos quantizados).
5. Modo offline: telemetria e autenticação com o servidor do PearAI desligadas ou opcionais quando o usuário escolhe o modo local.
6. Organização do fork para facilitar sync com o upstream (RNF05): customizações (i18n, modo local) separadas do código base.

## Requisitos funcionais

- **RF01 — Suporte nativo ao português (Brasil).** Interface (menus, configurações, tooltips), documentação embutida e mensagens de erro integralmente em pt-BR. O modelo de IA é instruído a responder preferencialmente em português.
- **RF02 — Modo local (offline).** Funcionar sem internet: indexação do código local, LLM local (Ollama, LM Studio) para chat e geração, sem telemetria obrigatória para servidores remotos.
- **RF03 — Modo online.** Opcional: chaves de API (OpenAI, Anthropic e outros) ou servidor próprio; sincronização opcional de configurações e preferências; modelos mais potentes na nuvem.
- **RF04 — Alternância de provedores.** Trocar entre LLM local e LLMs online (ou servidor próprio) numa configuração unificada, sem reiniciar o editor.
- **RF05 — Agente de código autônomo (opcional).** Manter o agente do PearAI para tarefas multi-etapa (criar arquivos, rodar testes) com permissão explícita e interface de aprovação em português.
- **RF06 — i18n estruturada.** Arquivos de tradução (JSON) que permitam outros idiomas no futuro, com foco em pt-BR.
- **RF07 — Onboarding e tutoriais em português.** Boas-vindas explicando como configurar modo local e online, e tutoriais das funcionalidades de vibe coding.

## Requisitos não funcionais

- **RNF01 — Privacidade no modo local.** Nenhum código, prompt ou dado de uso sai da máquina. Indexação e processamento 100% locais.
- **RNF02 — Desempenho.** Ações de UI em menos de 100 ms. A latência da IA depende do provedor; o editor não trava enquanto espera a resposta.
- **RNF03 — Hardware.** Modo local em máquina de desenvolvedor padrão (mínimo 8 GB RAM, GPU integrada), com modelos quantizados para CPU/GPU de baixo consumo.
- **RNF04 — Usabilidade.** Interface limpa. Troca local/online visualmente clara e pouco intrusiva. Manter o desenvolvedor em estado de fluxo.
- **RNF05 — Manutenção do fork.** Customizações (i18n, modo local) separadas do código base para sincronizar com o PearAI upstream.
- **RNF06 — Erros.** Falha de modelo local ou API online produz mensagem clara em português e sugere alternativa. Exemplo: "Modelo local não encontrado. Verifique se o Ollama está rodando ou mude para o modo Online."

## Fora de escopo até decisão explícita

- Publicar o fork num remoto (depende da conta GitHub do Edídio).
- Escolher licença diferente da do upstream.
- Adicionar idiomas além de pt-BR (a estrutura i18n prepara, não entrega).
