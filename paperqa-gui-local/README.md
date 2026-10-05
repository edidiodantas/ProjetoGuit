# Furyu

Perguntas sobre PDFs neste computador, com PaperQA2, Streamlit e Ollama.
Não usa chave da OpenAI.

O modelo é o Amadeus Verbo de 0,5 bilhão, no Ollama com o nome `amadeus-verbo`.
O `llm`, o `summary_llm` e o `agent_llm` apontam para esse modelo. Sem o
`agent_llm`, o PaperQA2 tenta a API paga.

## Neste Ubuntu

O Ollama já está instalado. Na pasta `Furyu-teste` do pendrive:

```bash
ollama create amadeus-verbo -f Modelfile
```

## Rodar esta interface

```bash
cd paperqa-gui-local
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Abra o endereço que aparecer, em geral http://localhost:8501.

Não defina `OPENAI_API_KEY`.

## Uso

1. Envie um ou mais PDFs.
2. Espere a indexação.
3. Digite a pergunta e clique em Perguntar.
4. Abra Mostrar fontes se quiser ver os trechos.

A primeira indexação baixa o modelo de embeddings. Nas seguintes, usa o cache.

## Se aparecer erro de OpenAI

O `app.py` já configura `llm`, `summary_llm` e `agent_llm` com
`llm_config` para `http://localhost:11434`. Confira o `.env`:
`OLLAMA_MODEL=amadeus-verbo`.
