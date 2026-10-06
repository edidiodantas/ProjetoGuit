# Checklist QA — Furyu (tela principal Streamlit)

Checklist de testes manuais de interface (UI/UX) antes de uso em produção (ambiente local / escola).

**Pré-condições**

- Ubuntu LTS (ou Windows com o mesmo app)
- Ollama rodando com o modelo definido no `.env` (`OLLAMA_MODEL`)
- App em `http://127.0.0.1:8501` (`streamlit run app.py` dentro de `Furyu2/`)
- Pasta `documentos/` gravável
- `CONTACT_EMAIL` no `.env` (recomendado para Unpaywall)

**Ambientes a cobrir**

- Desktop (≥ 1280 px) e janela estreita (~ 375–768 px)
- Chrome e Firefox (pelo menos um navegador completo + smoke no segundo)

**Como marcar**

- `[x]` passou · `[ ]` pendente · `N/A` não aplicável · anotar bugs com evidência (print/vídeo)

---

## 0. Smoke (antes de tudo)

- [ ] App carrega sem traceback no terminal / painel Streamlit
- [ ] Logo (livro) + título **Furyu** + tagline visíveis no topo (branding hero)
- [ ] Chips de modelo / embeddings / Ollama legíveis (sem branco-sobre-branco)
- [ ] Banner Ollama: verde se ok, vermelho se offline — texto compreensível
- [ ] Sem artefato visual no botão **Perguntar** (ex.: só a letra “r”)
- [ ] Sem scroll horizontal indevido no desktop

---

## 1. Sidebar — Configuração

### Visual

- [ ] Texto da sidebar com contraste adequado
- [ ] Chips (`.env`, caminhos, modelo) não estouram o layout
- [ ] Aviso de “primeira resposta lenta” visível e legível

### Funcional

- [ ] **Limpar sessão** zera PDFs indexados, resultados de busca e última resposta
- [ ] Após limpar, **Perguntar** fica desabilitado se não houver documentos
- [ ] Mensagem “Sessão limpa.” aparece

---

## 2. Seção 1 — Enviar PDFs

### Visual

- [ ] Título **1. Enviar PDFs** claro
- [ ] Área de upload fácil de achar (borda tracejada / destaque)
- [ ] Com sessão vazia: “Nenhum PDF indexado ainda.”
- [ ] Com docs: lista “Documentos na sessão: …” legível

### Funcional — caminho feliz

- [ ] Upload de 1 PDF com texto selecionável → status de progresso → “Indexado: …”
- [ ] Nome aparece em “Documentos na sessão”
- [ ] Upload de vários PDFs processa um a um sem travar a UI sem feedback

### Funcional — erros / limites

- [ ] Arquivo > 40 MB → erro claro; não indexa
- [ ] Arquivo renomeado `.pdf` que não é PDF → “não parece um PDF válido”
- [ ] PDF só imagem (scan) → erro sobre texto selecionável / OCR
- [ ] Reenviar o mesmo PDF → “Já indexado”
- [ ] Ollama offline → falha de indexação com mensagem legível (sem stacktrace cru)

---

## 3. Seção 2 — Buscar artigos (acesso aberto)

### Visual

- [ ] Caption do fluxo (localizar → baixar / guardar) legível
- [ ] Campo de busca + botão **Buscar** alinhados
- [ ] Cada resultado em card: título, ano, autores, venue/source, DOI, abstract sem overflow
- [ ] Três ações por hit (**Abrir link** | **Guardar link** | **Baixar e indexar**) com rótulos completos

### Funcional — busca

- [ ] Buscar com campo vazio → warning “Digite um tema para buscar.”
- [ ] Tema válido (ex.: `educação ambiental`) → spinner → N resultados + fonte (Oasisbr / …)
- [ ] Contagem “X com link de PDF/página aberta” coerente com os hits
- [ ] Sem resultados → “Nenhum artigo encontrado…”
- [ ] Falha de rede/API → erro com mensagem útil

### Funcional — Abrir link

- [ ] Com URL: abre nova aba no destino correto
- [ ] Sem URL: botão desabilitado; caption “Sem link aberto…”

### Funcional — Guardar link

- [ ] Primeiro clique → “Link guardado para baixar depois.”
- [ ] Segundo clique no mesmo link → “Esse link já estava na lista.”
- [ ] Item aparece em “Links guardados para baixar depois”
- [ ] **Abrir** no bloco de links salvos funciona
- [ ] **Limpar lista** esvazia a lista e atualiza a UI
- [ ] `documentos/links_salvos.json` só com `http(s)` públicos (sem `javascript:` / localhost)

### Funcional — Baixar e indexar

- [ ] Ollama ok + PDF com texto → spinner → success “Indexado na sessão: …”
- [ ] Nome entra em “Documentos na sessão”
- [ ] Já indexado → botão desabilitado + caption “Já indexado nesta sessão”
- [ ] Ollama offline → botão desabilitado
- [ ] SciELO / anti-bot ou scan → erro com orientação (abrir no navegador / Enviar PDFs)
- [ ] **Não** aparece `NotFoundError: removeChild` no console do browser ao clicar

---

## 4. Seção 3 — Pergunta + Resposta

### Visual

- [ ] Título **3. Pergunta** e caption de cautela sobre fontes
- [ ] Botão **Perguntar** com texto completo (não truncado)
- [ ] Resposta e fontes formatadas; citações legíveis

### Funcional

- [ ] Sem docs indexados → **Perguntar** desabilitado
- [ ] Pergunta vazia → desabilitado
- [ ] Ollama offline → desabilitado
- [ ] Caminho feliz: status (evidências → resumos → resposta) → resposta + fontes
- [ ] Limite de ~2000 caracteres respeitado no campo
- [ ] Erro do modelo → mensagem de falha clara
- [ ] Após **Limpar sessão**, última resposta some

---

## 5. UI/UX transversal (produção)

| Tema | Validar | Status |
|------|---------|--------|
| Contraste | Textos, captions, placeholders, sidebar, erros | [ ] |
| Layout mobile | Botões dos hits usáveis; sem scroll horizontal grave | [ ] |
| Feedback de espera | Spinners/status em busca, download e pergunta | [ ] |
| Persistência | Reload da página: sessão Streamlit pode resetar (comportamento esperado) | [ ] |
| Performance | Busca típica &lt; ~30 s; indexação/pergunta longas com feedback | [ ] |
| Acessibilidade básica | Tab order; botões clicáveis; labels presentes | [ ] |
| Segurança visual | Erros sem stacktraces enormes nem paths sensíveis demais | [ ] |
| Branding | Removendo a “nav mental”, ainda se reconhece como Furyu | [ ] |

---

## 6. Critérios go / no-go

### Go (uso local / escola)

- Smoke + Enviar PDF (feliz) + Buscar (feliz) + ≥1 Baixar/indexar (feliz) + ≥1 Perguntar com citação
- Sem `removeChild` recorrente nos botões OA
- Limites (PDF inválido, scan, &gt;40 MB, busca vazia) com erro claro
- Ollama offline degrada com mensagem, sem crash

### No-go

- Botão **Perguntar** ilegível ou quebrado
- Download OA em spinner infinito sem erro
- Upload/busca corrompe a sessão (precisa refresh forçado sempre)
- Console com erros React repetidos a cada clique

---

## 7. Dados de teste sugeridos

| Caso | Input |
|------|--------|
| PDF ok | Artigo curto com texto selecionável |
| PDF scan | Scan só imagem |
| Fake PDF | `.txt` renomeado para `.pdf` |
| Busca OA | `educação ambiental` (ou tema da escola) |
| Pergunta | “Quais são as principais conclusões do artigo?” |

---

## 8. Registro de execução

| Campo | Valor |
|-------|--------|
| Data | 2026-10-06 |
| Tester | Cloud Agent (Playwright + inspeção visual de screenshots) |
| Commit / branch | `cursor/furyu2-ubuntu-1878` |
| Navegador / SO | Chromium headless · Linux cloud VM |
| Resultado (go/no-go) | **Go condicional** para smoke/busca/guardar/erros de upload; indexação feliz do PDF de teste precisa de &gt;4 min na 1ª carga (embeddings HF) — timeout de 4 min no runner não concluiu; PaperQA `aadd` do mesmo PDF passou isolado |
| Bugs abertos | (corrigido nesta rodada) label Streamlit `rrorErro` → usar “Falha ao indexar…”. Observação: uploader Streamlit ainda exibe “200MB” nativo; app rejeita &gt;40 MB no código |

### Resultado por seção (execução 2026-10-06)

| Seção | Resultado | Evidência |
|-------|----------|-----------|
| 0 Smoke | Pass (UI carregou após restart; banner Ollama ok; logo Furyu) | `qa_01_smoke_home.png` |
| 1 Sidebar / Limpar | Pass | `qa_02_limpar_sessao.png` |
| 2 Upload fake PDF | Pass — “não parece um PDF válido” | `qa_06_fake_pdf.png` |
| 2 Upload scan | Pass — falha de indexação (sem texto) | `qa_07_scan_pdf.png` |
| 2 Upload PDF ok | Parcial — validação OK; indexação ainda em andamento/timeout no runner (~4 min); `aadd` isolado OK | `qa_08_index_result.png` + log PaperQA |
| 3 Busca vazia | Pass — “Digite um tema…” | `qa_03_empty_search.png` |
| 3 Busca “educação ambiental” | Pass — 8 resultados Oasisbr + 3 botões | `qa_04_search_results.png` |
| 3 Guardar link | Pass | `qa_05_guardar_link.png` |
| 4 Perguntar E2E | Não executado (depende de indexação concluída na sessão UI) | — |
| 5 Mobile viewport | Pass smoke | `qa_10_mobile.png` |

### Notas

- Antes do teste a app mostrava `ImportError: MAX_PDF_BYTES` por processo Streamlit antigo — **reinício** resolveu.
- Primeira indexação local baixa pesos HuggingFace e pode passar de 4 minutos; o checklist deve esperar isso em produção escolar.
- Log bruto: `/opt/cursor/artifacts/qa_ui_checklist_run.log`
_
