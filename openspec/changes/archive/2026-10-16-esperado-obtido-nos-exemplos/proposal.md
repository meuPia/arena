## Why

Quando um teste de exemplo falha no Rodar, a aba Missão mostra só uma linha de texto do plugin `meupia-testes`, por exemplo `❌ Esperava '4', mas recebeu '4' - Exemplo 1`. O plugin formata os dois valores com `str()`, então o texto `"4"` e o inteiro `4` aparecem iguais, e um espaço sobrando no fim ou uma quebra de linha a mais ficam invisíveis. A equipe vê "esperava 4, recebeu 4", conclui "mas está igual!" e gasta tempo (e tentativas de submissão) sem entender a falha. Os testes de exemplo já são públicos (vão ao navegador para o botão Rodar), então mostrar o detalhe deles não revela nada novo.

## What Changes

- Cada teste de exemplo vira um cartão na área de resultados da aba Missão, com o rótulo do teste (por exemplo "Exemplo 1"), a **entrada** (a expressão testada, como está na linha do teste: `dobro(2)`), o **esperado** e o **obtido** lado a lado (um embaixo do outro em tela estreita).
- Os valores aparecem como no Portugol e com o tipo: `"4"` (cadeia) contra `4` (inteiro), `verdadeiro`/`falso`, `[1, 2, 3]` (lista), `2.5` (real). Uma função que termina sem `retorne` aparece como "sem valor".
- Em cadeias, espaços, tabulações e quebras de linha ficam visíveis (`·`, `→`, `↵`) e o trecho que difere fica destacado nos dois lados.
- Uma dica curta explica a diferença quando ela é de um tipo comum: tipos diferentes, só espaços, quebra de linha, só maiúsculas/minúsculas, real contra inteiro com casas decimais, "sem valor".
- Testes aprovados aparecem compactos (rótulo e entrada); os reprovados, abertos com o detalhe. Um resumo no topo mostra `N de M exemplos aprovados`.
- Testes que não chegaram a rodar (o programa parou antes, por erro de execução) aparecem como "não executado".
- O painel deixa de ser montado a partir da saída de texto do programa: um `escreva("[TESTE_OK] ...")` do aluno não cria mais um cartão falso de aprovação, e o texto dos valores é inserido como texto, não como HTML.
- A semântica de aprovação continua a mesma do juiz (`==`, `!=`, `>`, `<`, `in`, truthiness). Uma comparação que lança erro passa a reprovar só aquele teste, com a mensagem "não dá para comparar", como o juiz já faz, em vez de derrubar o programa.
- Os testes extras continuam só "N de M" no veredito da submissão: nada desta mudança toca o juiz, a API ou a submissão.

Fora do escopo: isolar cada teste de exemplo no navegador (como o juiz faz, com limite de tempo por teste), detalhar no veredito da submissão quais exemplos falharam e qualquer mudança no pacote `meupia-testes` publicado no PyPI.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `arena-interface`: novo requisito "Resultado dos testes de exemplo no Rodar", que define o cartão por teste (entrada, esperado, obtido, tipo), o destaque das diferenças, as dicas, os testes não executados, que o resultado não vem da saída de texto do aluno e que os testes extras nunca aparecem ali.

## Impact

- **Frontend**:
  - novo `src/arena/testes-exemplo.js`: funções puras (ler as linhas `esperar_*` do `testesPublicos`, separar os argumentos, formatar valores, calcular o trecho diferente e escolher a dica) e a renderização dos cartões;
  - novo trecho Python (embutido no build) que, no Pyodide, troca as funções do plugin `meupia_testes.plugin_testes` por versões que mantêm a comparação e entregam o resultado estruturado ao JavaScript por um módulo registrado (`pyodide.registerJsModule`), não pelo stdout;
  - `src/main.js`: liga o novo painel ao botão Rodar e deixa de chamar `parseTestLine` quando o plugin da Arena está ativo (se a troca falhar, o comportamento antigo continua);
  - `src/arena/arena.css`: estilo dos cartões, do destaque e dos marcadores de espaço, só com tokens `--a-*`, contraste ≥ 4,5:1 nos dois temas;
  - `src/arena/ide-mobile.js`: sem mudança de código, desde que cada cartão mantenha a classe `test-item` (é ela que marca a aba Missão como "nova" no celular).
- **Arquivos herdados do Lab** (`src/engine/wasm.js`, `src/ui/instructions.js`): sem mudança; a troca do plugin acontece depois da inicialização do motor, pelo `main.js`.
- **Testes**: novo `src/arena/testes-exemplo.test.js` (`node --test`) e um teste Python que roda o trecho do plugin contra o código gerado pelo `meupia-core` 1.3.0 de um desafio de exemplo.
- **Sem mudanças** no backend, na API, no juiz (`api/_lib/*`), nas dependências ou nos desafios. Prazo: o evento é em 21/10; se não der para conferir a mudança no laboratório antes disso, ela fica para depois. O fallback para o comportamento antigo reduz o risco de levá-la ao evento.
