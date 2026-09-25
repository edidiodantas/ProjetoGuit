# IPEIA_VIBE_CODE

Um tutor de código educacional que usa a API Kimi/Moonshot para sugerir melhorias no seu código. A interface mostra o código original ao lado de um diff com as alterações propostas.

## Funcionalidades

- Backend em FastAPI com duas rotas: `GET /api/health` e `POST /api/composer`.
- Frontend com Monaco Editor e visualizador de diff.
- Tratamento de erros claro quando a chave de API não está configurada.
- CORS configurável via variável de ambiente.
- Limite de tamanho do payload e timeout nas chamadas à API Kimi.
- Tradução de erros da API Moonshot (401, 429, 5xx, conexão, etc.) em mensagens amigáveis em português.

> **Nota sobre streaming:** as respostas da API são recebidas de forma completa (buffering). O streaming pode ser adicionado no futuro para melhorar a experiência em reescritas longas.

## Requisitos

- Python 3.12+
- Uma chave de API da Moonshot/Kimi (opcional para testar a interface localmente)

## Criando uma chave gratuita (free tier)

1. Acesse https://platform.moonshot.cn/ e crie uma conta.
2. No painel, vá em **API Keys** (ou "密钥管理") e gere uma nova chave.
3. Copie a chave e cole no arquivo `.env` como `KIMI_API_KEY`.

O plano gratuito tem uso limitado, mas costuma ser suficiente para estudantes e projetos pequenos.

> **Dica:** para economizar tokens no free tier, o projeto já vem configurado com:
>
> ```env
> KIMI_MODEL=kimi-k2.5-lite
> ```
>
> Se você tiver créditos pagos e preferir usar sempre o modelo mais recente
> disponível para a sua chave, altere para `KIMI_MODEL=kimi-latest`.

## Configuração

1. Clone ou copie o projeto para a pasta desejada.
2. Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Copie o arquivo de exemplo e preencha sua chave:

```bash
cp .env.example .env
```

Edite `.env`:

```env
KIMI_API_KEY=sua_chave_aqui
# Opcional: mantenha o modelo gratuito recomendado
KIMI_MODEL=kimi-k2.5-lite
```

## Execução

```bash
python3 main.py
```

Ou, explicitamente com uvicorn:

```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
```

Acesse http://localhost:8000 no navegador.

Sem a `KIMI_API_KEY`, a interface carrega normalmente, mas o botão **Construir** retornará um erro `401` até que a chave seja configurada. Se a cota gratuita acabar, a interface mostrará uma mensagem sobre limite de requisições atingido (`429`).

Veja o guia passo a passo em [`docs/manual.md`](docs/manual.md).

## Testes

```bash
python3 -m pytest tests/ -q
```

Os testes cobrem:

- health check
- retorno 401 quando a chave de API está ausente
- retorno 429 em caso de limite de requisições
- retorno 502/503 em erros genéricos ou indisponibilidade da API
- validação do prompt e do código
- extração do último bloco de código da resposta do modelo
- precedência entre rotas da API e arquivos estáticos
- tradução das exceções do OpenAI SDK para exceções tipadas em português

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `KIMI_API_KEY` | Chave da API Moonshot/Kimi | — |
| `KIMI_BASE_URL` | URL base compatível com OpenAI | `https://api.moonshot.cn/v1` |
| `KIMI_MODEL` | Modelo usado. Use `kimi-k2.5-lite` para economizar no plano gratuito. | `kimi-k2.5-lite` |
| `APP_HOST` | Host do servidor | `0.0.0.0` |
| `APP_PORT` | Porta do servidor | `8000` |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula | `*` |
| `MAX_CODE_CHARS` | Tamanho máximo do campo `code` | `32000` |
| `KIMI_REQUEST_TIMEOUT` | Timeout da chamada à API, em segundos | `60` |

Em produção, defina `CORS_ORIGINS` com a origem exata do seu frontend e nunca use `*`.

## Estrutura

```text
.
├── config/
│   ├── __init__.py
│   └── settings.py
├── docs/
│   └── manual.md
├── services/
│   ├── __init__.py
│   └── kimi_service.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── js/
│       ├── app.js
│       ├── config.js
│       ├── editor.js
│       └── api.js
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   └── test_kimi_service.py
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```
