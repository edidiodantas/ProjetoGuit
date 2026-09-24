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

### `503` — Serviço indisponível ou chave não configurada

A aplicação carrega, mas o botão **Compor** devolve um erro 503. Isso acontece quando:

- A `KIMI_API_KEY` não foi configurada.
- A API da Moonshot está com instabilidade temporária.
- Você atingiu o limite do plano gratuito.

**Solução:**

- Confira se `.env` existe e tem a chave.
- Aguarde um pouco e tente novamente.
- No painel da Moonshot, verifique seu saldo de tokens.

### O modelo retorna código estranho ou em outra linguagem

Verifique se você selecionou a linguagem correta no menu suspenso. Se o problema continuar, tente um prompt mais específico, como "responda em português do Brasil e mantenha a linguagem Python".

### O texto do meu código é muito grande e dá erro

O app limita o tamanho do código enviado (padrão de 32.000 caracteres). Se precisar enviar um arquivo grande, divida-o em partes menores.

---

## Configurando o modelo para o plano gratuito

Se você está usando a chave gratuita da Moonshot, pode economizar tokens alterando o modelo no `.env`:

```env
KIMI_MODEL=kimi-k2.5-lite
```

Para usar sempre o modelo mais recente disponível, mantenha:

```env
KIMI_MODEL=kimi-latest
```

Reinicie o servidor após qualquer alteração no `.env`.

---

## Precisa de mais ajuda?

- Leia o `README.md` para instruções de instalação e variáveis de ambiente.
- Consulte a documentação oficial da Moonshot em https://platform.moonshot.cn/.
- Abra uma issue no repositório do projeto se encontrar um bug.

Bons estudos e boas sugestões de código!
