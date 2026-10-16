## ADDED Requirements

### Requirement: Resultado dos testes de exemplo no Rodar
Depois de cada Rodar numa missão, a área de resultados da aba Missão SHALL mostrar um cartão por linha de teste de exemplo do desafio (cada linha `esperar_*` dos testes de exemplo), na ordem do desafio, e um resumo no topo no formato `<a> de <t> exemplos aprovados`. Cada cartão SHALL mostrar:
- o rótulo: a mensagem da linha de teste quando ela é um texto literal (por exemplo "Exemplo 1"), senão `Exemplo <k>`;
- a **entrada**: o primeiro argumento da linha de teste, como está escrito no desafio (por exemplo `dobro(2)`); se a linha não puder ser separada em argumentos, a linha inteira;
- o estado: aprovado, reprovado ou não executado.

Um teste aprovado SHALL aparecer compacto (rótulo, entrada e estado). Um teste reprovado SHALL aparecer aberto, com o **esperado** e o **obtido** lado a lado (um embaixo do outro quando a área for estreita), cada valor com o seu tipo. Para cada função de teste, o esperado mostrado é:
- `esperar_igual`: o valor esperado;
- `esperar_diferente`: `diferente de <valor>`;
- `esperar_maior` / `esperar_menor`: `maior que <valor>` / `menor que <valor>`;
- `esperar_contem`: `conter <item>`, e o obtido é a coleção;
- `esperar_verdadeiro` / `esperar_falso`: `verdadeiro` / `falso`, e o obtido é o valor da condição.

Os testes que não chegaram a concluir, porque o programa parou antes (por exemplo, erro de execução ao calcular a entrada deste teste ou de um anterior), SHALL aparecer como `não executado` e contar como não aprovados no resumo. Em erro de compilação, a área de resultados SHALL ficar vazia. Cada Rodar SHALL substituir os cartões do Rodar anterior.

O critério de aprovação MUST ser o mesmo do juiz (igualdade, diferença, maior, menor, pertence e truthiness, com a mesma semântica do plugin `testes`). Uma comparação que lança erro (por exemplo, `esperar_maior` entre cadeia e inteiro) SHALL reprovar só aquele teste, com a explicação `não dá para comparar <tipo> com <tipo>`, e os testes seguintes SHALL rodar.

#### Scenario: Exemplo reprovado com tipos diferentes
- **WHEN** o teste de exemplo é `esperar_igual(dobro(2), 4, "Exemplo 1")` e a função do aluno devolve o texto `"4"`
- **THEN** o cartão "Exemplo 1" aparece reprovado, com entrada `dobro(2)`, esperado `4` (inteiro) e obtido `"4"` (cadeia)

#### Scenario: Exemplo aprovado
- **WHEN** a função do aluno devolve `4` para `dobro(2)`
- **THEN** o cartão "Exemplo 1" aparece compacto e aprovado, sem esperado e obtido

#### Scenario: Resumo
- **WHEN** o aluno roda um desafio com 3 testes de exemplo e passa em 2
- **THEN** o topo da área de resultados mostra `2 de 3 exemplos aprovados`

#### Scenario: Programa parou antes
- **WHEN** a função do aluno lança erro de execução na entrada do 2º de 3 testes de exemplo
- **THEN** o 1º cartão mostra o resultado dele, o 2º e o 3º aparecem como `não executado`, e o terminal mostra o erro como hoje

#### Scenario: Comparação inválida
- **WHEN** um teste de exemplo é `esperar_maior(f(1), 10, "Exemplo 2")` e `f(1)` devolve `"abc"`
- **THEN** o cartão "Exemplo 2" aparece reprovado com `não dá para comparar cadeia com inteiro`, e o "Exemplo 3" roda normalmente

#### Scenario: Erro de compilação
- **WHEN** o código do aluno não compila
- **THEN** a área de resultados fica vazia e o terminal mostra o erro de compilação como hoje

### Requirement: Valores no formato do Portugol
Os valores do esperado e do obtido SHALL aparecer como no Portugol, com o nome do tipo do dialeto:
- cadeia entre aspas duplas (`"4"`), com o rótulo `cadeia`;
- inteiro (`4`) e real (`2.5`, `4.0`) com os rótulos `inteiro` e `real`;
- lógico como `verdadeiro` ou `falso`, com o rótulo `logico`;
- lista como `[1, "a", verdadeiro]` e dicionário como `{"a": 1}`, com os elementos no mesmo formato e os rótulos `lista` e `dicionario`;
- a ausência de valor (função que termina sem `retorne`) como `sem valor`.

Dentro de uma cadeia, espaço, tabulação e quebra de linha SHALL ficar visíveis com marcadores próprios (`·`, `→`, `↵`), discretos fora do trecho destacado. Valores com mais de 300 caracteres SHALL ser encurtados com `…`, mantendo visível o trecho que difere.

#### Scenario: Espaço sobrando no fim
- **WHEN** o esperado é `"ok"` e o obtido é `"ok "`
- **THEN** o obtido aparece como `"ok·"`, com o `·` destacado

#### Scenario: Quebra de linha
- **WHEN** o esperado é `"a"` e o obtido é `"a\n"` (com quebra de linha no fim)
- **THEN** o obtido aparece como `"a↵"`, com o `↵` destacado

#### Scenario: Função sem retorne
- **WHEN** a função do aluno termina sem `retorne` e o esperado é `4`
- **THEN** o obtido aparece como `sem valor`

### Requirement: Destaque das diferenças e dicas
Num `esperar_igual` reprovado, o cartão SHALL destacar o que difere: o trecho diferente nos dois valores quando os tipos são iguais, e o rótulo do tipo nos dois lados quando os tipos são diferentes. O destaque MUST NOT depender só de cor (por exemplo, também sublinhado) e SHALL ter contraste de texto ≥ 4,5:1 nos temas claro e escuro.

Quando a diferença é de um tipo comum, o cartão SHALL mostrar uma dica curta, no máximo uma, na primeira regra que se aplicar:
1. obtido `sem valor`: a função terminou sem `retorne`;
2. esperado inteiro e obtido real: em Portugol `/` sempre dá real; para divisão inteira, `piso(a / b)`;
3. tipos diferentes: o tipo esperado e o tipo obtido (por exemplo, "o esperado é inteiro e o obtido é cadeia");
4. cadeias iguais sem os espaços das pontas: sobra ou falta espaço no início ou no fim;
5. cadeias iguais sem espaços e quebras de linha: diferença só em espaços ou quebras de linha;
6. cadeias iguais ignorando maiúsculas: diferença só em maiúsculas e minúsculas;
7. cadeias iguais ignorando acentos: diferença só em acentos;
8. reais muito próximos: diferença só nas últimas casas decimais (arredondamento).

Sem nenhuma regra aplicável, o cartão SHALL mostrar só o esperado e o obtido com o destaque.

#### Scenario: Cinco texto contra cinco número
- **WHEN** o esperado é `5` (inteiro) e o obtido é `"5"` (cadeia)
- **THEN** os rótulos `inteiro` e `cadeia` aparecem destacados e a dica diz que o esperado é inteiro e o obtido é cadeia

#### Scenario: Divisão que dá real
- **WHEN** o esperado é `3` e o obtido é `3.5`
- **THEN** a dica fala que `/` sempre dá real e sugere `piso(a / b)`

#### Scenario: Maiúsculas
- **WHEN** o esperado é `"Ola"` e o obtido é `"ola"`
- **THEN** o `o`/`O` inicial aparece destacado nos dois lados e a dica diz que a diferença é só em maiúsculas e minúsculas

#### Scenario: Tema claro
- **WHEN** a equipe está no tema claro e um exemplo reprova
- **THEN** o cartão, o destaque e os marcadores de espaço usam as cores do tema claro, com texto legível

### Requirement: Resultado dos exemplos independente da saída do aluno
Os cartões SHALL ser montados a partir do resultado das próprias linhas de teste do desafio, e não da saída de texto do programa. Um `escreva` do aluno com `[TESTE_OK]` ou `[TESTE_FALHA]` MUST NOT criar nem alterar cartões. Uma chamada `esperar_*` feita pelo código do aluno fora das linhas de teste MUST NOT criar cartão. Os valores vindos do programa do aluno MUST ser exibidos como texto, nunca interpretados como HTML.

O terminal SHALL continuar mostrando uma linha por teste de exemplo, com o rótulo e, na reprovação, o esperado e o obtido com os tipos (por exemplo, `Exemplo 1: esperado 4 (inteiro), obtido "4" (cadeia)`).

Os resultados dos testes extras MUST NOT aparecer na IDE além do `N de M` do veredito da submissão: esta área mostra só os testes de exemplo, que já são públicos.

Se a forma estruturada de obter os resultados não puder ser ativada no navegador, a IDE SHALL voltar a mostrar os resultados como antes desta mudança (uma linha de texto por teste), e Rodar e Submeter MUST continuar funcionando.

#### Scenario: Marcador forjado
- **WHEN** o código do aluno faz `escreva("[TESTE_OK] Sucesso: tudo certo")` e a função devolve um valor errado
- **THEN** nenhum cartão aprovado extra aparece, e o cartão do exemplo fica reprovado

#### Scenario: HTML no valor
- **WHEN** a função do aluno devolve `"<b>oi</b>"`
- **THEN** o obtido aparece como o texto `"<b>oi</b>"`, sem negrito

#### Scenario: esperar_* do aluno
- **WHEN** o `inicio` do aluno chama `esperar_igual(1, 1)` antes dos testes
- **THEN** a área de resultados tem só os cartões das linhas de teste do desafio

#### Scenario: Extras fora da IDE
- **WHEN** a equipe roda e depois submete o código
- **THEN** a área de resultados mostra só os testes de exemplo, e o veredito mostra os extras só como `N de M`
