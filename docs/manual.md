# Manual do IPEIA_VIBE_CODE

Bem-vindo! Este manual explica como usar o **IPEIA_VIBE_CODE**, um tutor de código que usa a inteligência artificial da Kimi/Moonshot para sugerir melhorias no seu código.

---

## O que é este app?

O IPEIA_VIBE_CODE é uma ferramenta educacional para aprender programação. Você escreve um código, descreve o que quer mudar (por exemplo, "adicione comentários" ou "corrija os erros") e a IA devolve uma sugestão com as alterações marcadas em um diff.

Ele é útil para:

- Entender como melhorar trechos de código.
- Aprender novas formas de escrever a mesma lógica.
- Revisar códigos antes de entregar em exercícios.

---

## Como abrir o app

1. No terminal, entre na pasta do projeto:

   ```bash
   cd /caminho/para/IPEIA_VIBE_CODE
   ```

2. Ative o ambiente virtual e inicie o servidor:

   ```bash
   source .venv/bin/activate
   python3 main.py
   ```

3. Abra o navegador e acesse:

   ```text
   http://localhost:8000
   ```

Você verá duas áreas principais: o editor com seu código original à esquerda e, depois de usar o botão **Compor**, o diff com a sugestão à direita.

---

## Como usar

1. Escolha a linguagem do código no menu suspenso.
2. Cole ou edite o código no editor **Original**.
3. Escreva no campo **Prompt** o que você quer que o Kimi faça, por exemplo:
   "Adicione tratamento de erros e anotações de tipo".
4. Clique em **Compor** e aguarde a resposta.
5. Revise o diff. Se quiser recomeçar, clique em **Redefinir**.

---

## Como selecionar a linguagem

No canto superior da tela há um menu suspenso para escolher a linguagem (por exemplo, Python, JavaScript, C, etc.). Escolha a linguagem do código que você colou para que a IA entenda melhor o contexto.

---

## Como escrever um prompt

O prompt é a instrução que você dá para a IA. Escreva de forma clara e direta.

Exemplos bons:

- "Adicione tipos às funções."
- "Transforme esse loop em uma list comprehension."
- "Explique o que esse código faz e corrija possíveis erros."

Dicas:

- **Seja específico.** Quanto mais clara a instrução, melhor a resposta.
- **Comece pequeno.** Teste com pedidos curtos antes de pedir grandes refatorações.
- **Revise antes de aceitar.** A IA pode sugerir código que parece certo, mas não é.

---

## O que significa o diff?

O diff é a comparação entre o seu código original e a sugestão da IA.

- Linhas **verdes** ou marcadas com `+` mostram código que a IA **adicionou**.
- Linhas **vermelhas** ou marcadas com `-` mostram código que a IA **removeu**.
- Linhas sem marcação permanecem iguais.

Ler o diff ajuda você a entender exatamente o que mudou.

---

## Como aceitar ou rejeitar a sugestão

Depois que a resposta aparecer:

- **Aceitar:** clique no botão **Aplicar** (ou equivalente) para copiar a sugestão para o editor original.
- **Rejeitar:** clique em **Rejeitar** para descartar a sugestão e continuar com seu código.
- **Tentar de novo:** edite o prompt e clique em **Compor** novamente.

Não se preocupe em errar: a versão original fica salva até você decidir aplicar.

---

## Configuração da API gratuita (free tier)

O projeto já vem configurado para usar o modelo **`kimi-k2.5-lite`**, indicado
para o plano gratuito da Moonshot e suficiente para pequenos projetos e
estudantes.

### 1. Criar uma conta e obter a chave

1. Acesse a plataforma da Moonshot / Kimi (https://platform.moonshot.cn/).
2. Crie uma conta ou faça login.
3. Gere uma chave de API (*API Key*) na área de configuração da conta.

### 2. Configurar o arquivo `.env`

Copie o exemplo:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e cole sua chave:

```env
KIMI_API_KEY=sua_chave_aqui
KIMI_MODEL=kimi-k2.5-lite
```

> **Dica:** mantenha `KIMI_MODEL=kimi-k2.5-lite` para continuar no free tier.
> Se você tiver créditos pagos, pode trocar por outro modelo, como
> `kimi-latest`.

### 3. Verificar a cota / limite de requisições

- O plano gratuito da Moonshot costuma ter um número limitado de requisições
  por minuto e/ou um total de tokens disponíveis por dia.
- Você pode acompanhar o consumo e os créditos restantes no painel da sua
  conta na plataforma Moonshot.
- Se atingir o limite, a aplicação mostrará a mensagem:
  **"Cota gratuita esgotada ou limite de requisições atingido. Aguarde alguns
  minutos ou verifique sua chave e créditos na plataforma Moonshot."**

---

## Mensagens de aviso e o que significam

A interface traduz os erros da API em mensagens claras em português:

| Mensagem exibida | O que aconteceu | O que fazer |
|---|---|---|
| **Chave de API inválida ou não configurada...** | A `KIMI_API_KEY` está em branco, foi recusada (HTTP 401) ou não foi lida pelo servidor. | Preencha a chave no `.env` e reinicie o servidor. |
| **Cota gratuita esgotada ou limite de requisições atingido...** | A API retornou erro 429 (*rate limit* / quota excedida). | Aguarde alguns minutos ou verifique seus créditos na plataforma Moonshot. |
| **O serviço da Moonshot está temporariamente indisponível...** | Erro 5xx no servidor da Moonshot. | Aguarde e tente novamente em instantes. |
| **Sem conexão com a internet ou serviço indisponível...** | O backend não conseguiu conectar-se à API (problema de rede). | Verifique sua conexão de rede. |
| **Requisição inválida...** | Erro 400. Pode ser prompt vazio, modelo inexistente ou código muito grande. | Verifique o prompt e o tamanho do código. |
| **Erro na API (502/503)...** | Erro genérico ou indisponibilidade da API. | Tente novamente mais tarde. |

---

## Dicas para estudantes

1. **Mantenha os prompts curtos no começo.** Assim você aprende aos poucos o que a IA faz bem.
2. **Sempre leia o código sugerido.** A IA pode cometer erros ou inventar funções que não existem.
3. **Use a ferramenta para aprender, não para copiar.** Tente entender por que a sugestão foi feita.
4. **Não envie dados pessoais ou senhas.** O código vai para a API da Moonshot.
5. **No plano gratuito, economize chamadas.** Espere ter uma ideia clara do que pedir antes de clicar em **Compor**.

---

## Erros comuns

### `401` — Chave de API inválida ou ausente

Você esqueceu de configurar a chave no arquivo `.env`, ou a chave está errada.

**Solução:**

1. Abra o arquivo `.env` na raiz do projeto.
2. Verifique se `KIMI_API_KEY` está preenchida corretamente.
3. Reinicie o servidor.

### `429` — Limite de requisições ou cota gratuita esgotada

A API retornou um erro de *rate limit* ou a cota gratuita acabou.

**Solução:**

- Aguarde alguns minutos e tente novamente.
- No painel da Moonshot, verifique seu saldo de tokens e créditos.
- Se estiver usando `kimi-latest`, considere trocar para `kimi-k2.5-lite`.

### `503` — Serviço da Moonshot indisponível

A API da Moonshot está com instabilidade temporária.

**Solução:**

- Aguarde um pouco e tente novamente.
- Verifique o status da plataforma Moonshot.

### O modelo retorna código estranho ou em outra linguagem

Verifique se você selecionou a linguagem correta no menu suspenso. Se o problema continuar, tente um prompt mais específico, como "responda em português do Brasil e mantenha a linguagem Python".

### O texto do meu código é muito grande e dá erro

O app limita o tamanho do código enviado (padrão de 32.000 caracteres). Se precisar enviar um arquivo grande, divida-o em partes menores.

---

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `KIMI_API_KEY` | Chave da API Moonshot/Kimi | — |
| `KIMI_BASE_URL` | URL base compatível com OpenAI | `https://api.moonshot.cn/v1` |
| `KIMI_MODEL` | Modelo usado (use `kimi-k2.5-lite` no free tier) | `kimi-k2.5-lite` |
| `APP_HOST` | Host do servidor | `0.0.0.0` |
| `APP_PORT` | Porta do servidor | `8000` |
| `CORS_ORIGINS` | Origens permitidas pelo CORS | `*` |
| `MAX_CODE_CHARS` | Tamanho máximo do campo `code` | `32000` |
| `KIMI_REQUEST_TIMEOUT` | Timeout da chamada à API, em segundos | `60` |

---

## Execução e testes

Para iniciar o servidor localmente:

```bash
python3 main.py
```

Acesse no navegador: `http://localhost:8000`

Para rodar os testes automatizados:

```bash
python3 -m pytest tests/ -q
```

---

## Precisa de mais ajuda?

- Leia o `README.md` para instruções de instalação e variáveis de ambiente.
- Consulte a documentação oficial da Moonshot em https://platform.moonshot.cn/.
- Abra uma issue no repositório do projeto se encontrar um bug.

Bons estudos e boas sugestões de código!
