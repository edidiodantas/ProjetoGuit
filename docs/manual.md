# Manual do IPEIA_VIBE_CODE

## O que é

O **IPEIA_VIBE_CODE** é um tutor de código que usa a API da **Moonshot / Kimi**
para sugerir melhorias no código que você colar na interface. O resultado é
mostrado lado a lado: o código original à esquerda e o *diff* (diferença) com
as alterações propostas à direita.

## Como usar

1. Escolha a linguagem do código no menu suspenso.
2. Cole ou edite o código no editor **Original**.
3. Escreva no campo **Prompt** o que você quer que o Kimi faça, por exemplo:
   "Adicione tratamento de erros e anotações de tipo".
4. Clique em **Compor** e aguarde a resposta.
5. Revista o diff. Se quiser recomeçar, clique em **Redefinir**.

## Configuração da API gratuita (free tier)

O projeto já vem configurado para usar o modelo **`kimi-k2.5-lite`**, indicado
para o plano gratuito da Moonshot e suficiente para pequenos projetos e
estudantes.

### 1. Criar uma conta e obter a chave

1. Acesse a plataforma da Moonshot / Kimi.
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

## Dicas de uso

- Use prompts curtos e objetivos para gastar menos tokens.
- Se o resultado vier vazio ou com erro, verifique sua cota na plataforma
  Moonshot antes de tentar novamente.
- Em produção, defina `CORS_ORIGINS` com a origem exata do seu frontend e
  nunca deixe `*` ativo.
