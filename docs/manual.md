# Manual do IPEIA VIBE CODING

Este guia mostra como usar o **IPEIA VIBE CODING**, um tutor de código para estudantes. Você escreve um programa, pede uma melhoria em português e compara a sugestão com o que escreveu.

## O que é esta tela

A tela principal cabe em uma única janela no computador, sem rolagem da página. O visual é claro (tema claro), com a fonte Ubuntu.

De cima para baixo:

- O nome **IPEIA VIBE CODING** e, ao lado, o botão **Manual**, que abre este guia.
- A barra de controles: menu **Linguagem**, campo **Prompt**, botão **Construir** e botão **Redefinir**.
- Uma caixa de status colorida. Azul é informação, verde é sucesso, amarelo é aviso e vermelho é erro.
- O editor **Original**, onde fica o seu código.
- O painel **Diferença**, logo abaixo do Original. Ele fica visível o tempo todo. Antes do primeiro **Construir**, mostra a mensagem "Nenhuma sugestão ainda".

A rolagem acontece dentro de cada editor, não na página.

## Passo a passo

1. **Escolha a linguagem** no menu (Python, JavaScript, HTML e outras). Use a linguagem do código que você vai colar.
2. **Cole ou edite o código** no editor **Original**. Você pode mudar o exemplo que já vem na tela.
3. **Escreva o prompt** no campo Prompt. Diga com clareza o que a IA deve fazer. Exemplos: "Adicione tratamento de erros" ou "Explique este código e corrija os erros".
4. **Clique em Construir.** Também vale pressionar `Ctrl+Enter` (ou `Cmd+Enter` no Mac). O botão mostra um indicador de espera enquanto a resposta não chega.
5. **Leia a explicação** na caixa de status, embaixo dos botões. Em caso de sucesso ela fica verde e traz a primeira frase da explicação da IA.
6. **Compare o Original com a Diferença.** O Original continua em cima, com o código que você enviou. A Diferença fica embaixo e mostra o que mudou: trechos adicionados em verde (ou com `+`) e trechos removidos em vermelho (ou com `-`).
7. **Clique em Redefinir** quando quiser começar de novo. O prompt é apagado, a linguagem volta para Python, o Original volta ao exemplo inicial e a Diferença mostra outra vez a dica de que ainda não há sugestão.

## Modelo gratuito

As sugestões vêm da API Kimi/Moonshot. O modelo configurado para o plano gratuito é **kimi-k2.5-lite**. Ele gasta menos e costuma bastar para exercícios e trechos curtos.

No arquivo `.env` do projeto:

```env
KIMI_API_KEY=sua_chave_aqui
KIMI_MODEL=kimi-k2.5-lite
```

Se a conta tiver créditos pagos, o modelo pode ser trocado, por exemplo para `kimi-latest`. Enquanto estiver no plano gratuito, mantenha `kimi-k2.5-lite`.

## O que significam os erros

A caixa de status em vermelho traduz a resposta da API.

### 401 — chave inválida ou ausente

Mensagem: "Chave de API inválida ou não configurada. Verifique se a variável KIMI_API_KEY está preenchida corretamente no arquivo .env."

A chave não foi colocada no `.env`, não foi lida pelo servidor ou a Moonshot recusou a chave. Corrija `KIMI_API_KEY` e reinicie o servidor. A tela abre mesmo sem chave, mas **Construir** responde 401 até a chave existir.

### 429 — limite ou cota gratuita

Mensagem: "Cota gratuita esgotada ou limite de requisições atingido. Aguarde alguns minutos ou verifique sua chave e créditos na plataforma Moonshot."

O plano gratuito tem um limite de pedidos. Espere um pouco ou confira os créditos em https://platform.moonshot.cn/. Continuar em `kimi-k2.5-lite` ajuda a economizar.

### Outros erros

- **503 — serviço indisponível.** "O serviço da Moonshot está temporariamente indisponível. Aguarde alguns instantes e tente novamente."
- **503 — sem conexão.** "Sem conexão com a internet ou serviço indisponível. Verifique sua conexão de rede e tente novamente."
- **400 — requisição inválida.** O prompt, o modelo ou o tamanho do código foi recusado. A mensagem começa com "Requisição inválida".
- **502 ou outro código.** A caixa mostra "Erro na API" seguido do número. Tente de novo mais tarde.
- **Aviso amarelo.** O prompt está vazio, ou o editor Original está vazio. Preencha os dois antes de clicar em **Construir**.

## Dicas

- Peça uma coisa de cada vez.
- Leia a Diferença antes de copiar a sugestão. A IA pode errar.
- Não cole senhas nem dados pessoais. O código é enviado à Moonshot.
- No plano gratuito, espere ter o pedido claro antes de clicar em **Construir**.
