# Manual do usuário — IPEIA_VIBE_CODE

Interface web do tutor de código educacional IPEIA_VIBE_CODE.

## Visão geral

A tela é dividida em três áreas principais:

1. **Cabeçalho**: nome do projeto e descrição rápida.
2. **Painel de controle**: escolha da linguagem, campo de prompt, botões de ação e a caixa de status.
3. **Editores lado a lado**: código original à esquerda e diff com as alterações propostas à direita.

## Como usar

1. Escolha a linguagem do código no menu suspenso **Linguagem**.
2. Cole ou digite o código no editor **Original** (à esquerda).
3. Escreva no campo **Prompt** o que o modelo deve fazer, por exemplo:
   - "Adicione tratamento de erros"
   - "Inclua anotações de tipo"
   - "Melhore a legibilidade"
4. Clique em **Compor** ou pressione `Ctrl+Enter` / `Cmd+Enter`.
5. Aguarde a resposta. O botão entra em estado de carregamento e a caixa de status mostra o andamento.
6. Quando a resposta chegar, o editor **Diferença** (à direita) exibe o diff lado a lado.
7. Para recomeçar, clique em **Redefinir**.

## Estados e feedback

- **Caixa azul**: informação (carregando, instrução inicial).
- **Caixa verde**: sucesso na composição.
- **Caixa amarela**: aviso, como prompt ou código vazio.
- **Caixa vermelha**: erro na API ou no servidor.

A caixa de status usa `aria-live`, então leitores de tela anunciam automaticamente as mensagens.

## Acessibilidade

- Todos os campos possuem rótulos semânticos associados via atributo `for`.
- Os botões ficam desabilitados durante a chamada à API.
- Foco visível em todos os controles interativos.
- A aplicação respeita a preferência `prefers-reduced-motion`.

## Responsividade

- Em telas maiores, os editores aparecem lado a lado.
- Abaixo de **1024 px**, os editores se empilham verticalmente para melhor aproveitamento da tela.
- Em telas pequenas (até **640 px**), os controles também se empilham e os botões ocupam a largura total.
