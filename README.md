# IPEIA_VIBE_CODE

Um tutor de código educacional que usa a API Kimi/Moonshot para sugerir melhorias no seu código. A interface mostra o código original ao lado de um diff com as alterações propostas.

## Funcionalidades

- Backend em FastAPI com duas rotas: `GET /api/health` e `POST /api/composer`.
- Frontend com Monaco Editor e visualizador de diff.
- Tratamento de erros claro quando a chave de API não está configurada.
- CORS configurável via variável de ambiente.
- Limite de tamanho do payload e timeout nas chamadas à API Kimi.

> **Nota sobre streaming:** as respostas da API são recebidas de forma completa (buffering). O streaming pode ser adicionado no futuro para melhorar a experiência em reescritas longas.

## Requisitos

- Python 3.12+
- Uma chave de API da Moonshot/Kimi (opcional para testar a interface localmente)

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

Sem a `KIMI_API_KEY`, a interface carrega normalmente, mas o botão **Compor** retorna um erro 503 até que a chave seja configurada.

## Testes

```bash
pytest
```

Os testes cobrem:

- health check
- retorno 503 quando a chave de API está ausente
- validação do prompt e do código
- extração do último bloco de código da resposta do modelo
- precedência entre rotas da API e arquivos estáticos

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `KIMI_API_KEY` | Chave da API Moonshot/Kimi | — |
| `KIMI_BASE_URL` | URL base compatível com OpenAI | `https://api.moonshot.cn/v1` |
| `KIMI_MODEL` | Modelo usado (use `kimi-k2.5-lite` no free tier) | `kimi-k2.5-lite` |
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
