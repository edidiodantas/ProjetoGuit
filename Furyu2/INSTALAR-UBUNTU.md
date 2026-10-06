# Instalar o Furyu no Ubuntu LTS (22.04 ou 24.04)

Guia em **português do Brasil**. A tela é a mesma do Windows; só muda a instalação.

> **Importante:** copie a pasta `Furyu2` do pendrive para o **disco interno** (ext4), por exemplo `~/Furyu2`.  
> Não rode o ambiente virtual (`.venv`) de dentro de um pendrive **exFAT** — ele quebra.

## 0. Copiar do pendrive

No Ubuntu, o pendrive costuma aparecer em `/media/SEU_USUARIO/NOME_DO_PENDRIVE/`.

```bash
# Ajuste o caminho do pendrive e o destino:
cp -a /media/$USER/*/Furyu2 ~/Furyu2
cd ~/Furyu2
ls
# Deve aparecer: app.py  install-ubuntu.sh  rodar-ubuntu.sh  requirements.txt ...
```

Se o pendrive tiver outro rótulo, abra o gerenciador de arquivos, copie a pasta `Furyu2` para a pasta Pessoal e abra o Terminal nela (`clique direito → Abrir no Terminal`).

## 1. Pacotes do sistema

O instalador tenta instalar o necessário. Se preferir fazer à mão:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-dev build-essential curl
python3 --version
# Precisa ser 3.11 ou superior (Ubuntu 22.04 = 3.10 às vezes; 24.04 = 3.12).
```

**Ubuntu 22.04 com Python 3.10:** instale o 3.11+ via deadsnakes ou use Ubuntu 24.04 LTS.

```bash
# Somente se python3 --version for menor que 3.11:
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

## 2. Ollama (IA local)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &          # se o serviço ainda não estiver rodando
ollama pull qwen3.5:4b
ollama run qwen3.5:4b "Olá"
```

Deixe o Ollama escutando em `http://localhost:11434`.  
**Não** crie `OPENAI_API_KEY`.

## 3. Instalar o Furyu

Na pasta `~/Furyu2`:

```bash
bash install-ubuntu.sh
```

Isso cria o `.venv`, instala PyTorch (CPU) + PaperQA + Streamlit e gera o arquivo `.env`.

Edite o `.env` e coloque um **e-mail real** (exigência do Unpaywall para achar PDF aberto — **não é login**):

```bash
nano .env
```

Exemplo:

```env
OLLAMA_MODEL=qwen3.5:4b
CONTACT_EMAIL=seu.email@escola.edu.br
```

## 4. Rodar

```bash
cd ~/Furyu2
bash rodar-ubuntu.sh
```

Ou:

```bash
cd ~/Furyu2
source .venv/bin/activate
streamlit run app.py
```

Abra no navegador: **http://localhost:8501**

Você deve ver o título **Furyu**, a barra lateral azul e as seções 1–3 (Enviar PDFs, Buscar artigos, Pergunta).

## 5. O que testar

Precisa de **internet** só na seção 2 (Oasisbr / Unpaywall). Ollama e a leitura do PDF são locais.

1. Faixa **verde** no topo: Ollama ok e o modelo do `.env` instalado.
2. **2. Buscar artigos** — tema `educação inclusiva` → Buscar.
3. Se o botão **Baixar PDF aberto e indexar** estiver ativo, teste um. Senão, baixe um PDF curto e use **1. Enviar PDFs**.
4. **3. Pergunta** → Perguntar. A 1ª resposta pode levar alguns minutos. Não feche a aba.
5. Abra **Mostrar fontes**.

Textos da tela: [FUNCOES.txt](FUNCOES.txt).

## 6. Levar de volta no pendrive

Depois de usar no PC:

1. Feche o Streamlit (`Ctrl+C` no terminal).
2. Você **não precisa** copiar `.venv` de volta (é grande e específico da máquina).
3. Se quiser levar PDFs indexados, copie a pasta `documentos/` (e opcionalmente `.pqa/`) para o pendrive.
4. A pasta `Furyu2` com o código (sem `.venv`) já basta para instalar em outro Ubuntu/Windows.

## Não faça

- Não instale `.venv` no pendrive exFAT
- Não comece a demo com o modelo 9B sem ter ensaiado
- Não rode com um `.env` do Deepin apontando para `/media/.../pqa-linux` neste Ubuntu
- Não misture pasta antiga `Furyu` com `Furyu2` (use nomes separados)

## Problemas comuns

| Problema | Solução |
| --- | --- |
| `python3: No module named venv` | `sudo apt install -y python3-venv` |
| `Connection refused :11434` | `ollama serve` ou abra o app Ollama |
| Modelo não encontrado | `ollama pull qwen3.5:4b` |
| pip / torch lento | deixe terminar; na 1ª vez demora |
| Porta 8501 ocupada | `streamlit run app.py --server.port 8502` |
