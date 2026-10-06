# Suíte de avaliação RAG do Furyu
#
# Documentação: PLANO_AVALIACAO_RAG.md
# Execução:     python testes/run_avaliacao.py
#
# Estrutura:
#   corpus/           PDFs + golden.json
#   lib/              pipeline PaperQA + métricas estilo Ragas
#   test_01_*.py      Retrieval
#   test_02_*.py      Geração (+ DeepEval opcional)
#   test_03_*.py      5 edge cases
#   resultados/       relatórios JSON/MD gerados na execução
