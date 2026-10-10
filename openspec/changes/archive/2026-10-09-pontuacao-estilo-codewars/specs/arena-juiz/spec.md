## Purpose

Julgar no servidor o código Portugol enviado por uma equipe: rodar os testes de exemplo e os testes extras com cada teste isolado e devolver um veredito "N de M" por bateria, sem revelar os testes extras nem qual deles falhou.

## ADDED Requirements

### Requirement: Montagem igual à do Lab
O juiz SHALL montar o programa como o meuPiá Lab: remover `fim_algoritmo` do código do aluno, inserir `usar "testes"` depois da linha `algoritmo "..."`, anexar os testes e fechar com `fim_algoritmo`. Os testes de exemplo MUST vir antes dos testes extras, na ordem em que aparecem no desafio. O juiz MUST compilar com a mesma versão do meupia-core que o navegador usa.

#### Scenario: Gabarito monta e compila
- **WHEN** o juiz recebe o gabarito de B01 com os testes de exemplo e os extras de B01
- **THEN** a compilação gera o programa e cada linha `esperar_*` dos testes vira um teste julgado, na mesma ordem

### Requirement: Duas baterias numa só execução
Cada julgamento SHALL compilar e executar o programa uma única vez e informar o resultado separado por bateria: `exemplos` (aprovados e total) e `extras` (aprovados e total). O total de cada bateria SHALL ser o número de linhas de teste (`esperar_*`) da bateria.

#### Scenario: Contagem separada
- **WHEN** um código passa nos 3 testes de exemplo e em 14 dos 20 extras
- **THEN** o resultado informa exemplos 3/3 e extras 14/20

### Requirement: Teste isolado
Cada teste SHALL rodar isolado dos demais. Uma exceção, uma comparação que lança erro, um `esperar_*` que nunca termina ou um laço infinito durante um teste MUST reprovar só esse teste, e os testes seguintes MUST rodar normalmente. Cada teste SHALL ter um limite de tempo próprio de 1 segundo.

#### Scenario: Exceção em um teste
- **WHEN** a função do aluno lança exceção (por exemplo, índice fora da lista) só para a entrada do 5º teste
- **THEN** o 5º teste é reprovado e todos os outros testes são julgados normalmente

#### Scenario: Laço infinito em um teste
- **WHEN** a função do aluno entra em laço infinito só para a entrada do 2º teste extra
- **THEN** o 2º teste extra é reprovado depois de cerca de 1 s e os testes extras seguintes são julgados normalmente

#### Scenario: Comparação que lança erro
- **WHEN** um teste compara o retorno do aluno com o esperado e a comparação lança exceção (por exemplo, `esperar_maior` entre tipos incompatíveis)
- **THEN** esse teste é reprovado e os demais continuam

### Requirement: Limite de tempo total
O processo de execução SHALL ter um limite total de `min(15 s, 2 s + 1 s × número de testes)`. Se o limite estourar, os testes já concluídos MUST manter o resultado, e os testes não concluídos MUST contar como reprovados. A compilação mantém o limite próprio dela.

#### Scenario: Estouro do tempo total
- **WHEN** o processo é interrompido pelo limite total depois de concluir os 3 exemplos e 8 extras
- **THEN** o veredito considera os resultados desses 11 testes, e os extras restantes contam como reprovados

### Requirement: Código do `inicio` do aluno
O bloco `inicio` do aluno SHALL rodar antes dos testes, como no Lab, com o mesmo limite de tempo de um teste. Um erro ou um estouro de tempo nesse bloco MUST NOT impedir os testes de rodar, e o bloco não conta como teste.

#### Scenario: `inicio` com erro
- **WHEN** o `inicio` do aluno lança uma exceção, mas as funções pedidas estão corretas
- **THEN** os testes rodam e são aprovados normalmente

### Requirement: Resultado à prova de fraude
Só as chamadas `esperar_*` das linhas de teste do desafio SHALL produzir resultado. Uma chamada `esperar_*` feita pelo código do aluno fora de um teste MUST ser ignorada. Dentro de um teste, SHALL valer a última chamada, que é a da linha de teste. A saída de texto do aluno MUST ser descartada: um `escreva("[TESTE_OK]")` não aprova nada. O relatório de resultados SHALL ser assinado com um nonce aleatório por julgamento, e só linhas com esse nonce MUST ser aceitas.

#### Scenario: Marcador forjado
- **WHEN** a função do aluno escreve `[TESTE_OK] Sucesso` e devolve um valor errado
- **THEN** o teste é reprovado

#### Scenario: `esperar_*` chamado pelo aluno
- **WHEN** a função do aluno chama `esperar_igual(1, 1)` antes de devolver um valor errado
- **THEN** o teste é reprovado, porque vale a chamada da linha de teste

### Requirement: Semântica dos `esperar_*`
O juiz SHALL avaliar `esperar_igual`, `esperar_diferente`, `esperar_maior`, `esperar_menor`, `esperar_contem`, `esperar_verdadeiro` e `esperar_falso` com a mesma semântica do plugin `testes` do Lab. Em `esperar_verdadeiro` e `esperar_falso`, isso inclui avaliar a condição por *truthiness*.

#### Scenario: Truthiness
- **WHEN** um teste chama `esperar_verdadeiro` com um retorno não vazio que não é booleano
- **THEN** o teste é aprovado, como no Lab

### Requirement: Isolamento do processo
A execução SHALL rodar num processo separado, com ambiente sem variáveis do servidor, limite de memória, limite de CPU e entrada padrão vazia. Segredos do servidor MUST NOT ser acessíveis ao código do aluno.

#### Scenario: Leitura de segredo
- **WHEN** o código do aluno tenta ler `ARENA_SECRET` do ambiente
- **THEN** recebe vazio, e o teste que dependia disso é reprovado

### Requirement: Veredito
O juiz SHALL devolver um destes status:
- `aceito`: passou em 100% dos exemplos. Inclui as contagens de exemplos e extras e `completo` (verdadeiro quando passou em 100% dos extras).
- `reprovado_exemplos`: compilou, mas não passou em todos os exemplos. Inclui as contagens de exemplos e de extras.
- `erro_compilacao`: inclui a mensagem e a linha do editor, quando houver, com o mesmo mapeamento de linhas de hoje.
- `erro_execucao`: o processo terminou sem nenhum relatório válido.

O veredito MUST NOT identificar qual teste extra falhou, nem a entrada, a saída esperada ou a mensagem de um teste extra. Para os exemplos, que já são públicos, o veredito MAY dizer se a falha foi tempo esgotado ou erro de execução.

#### Scenario: Aceito completo
- **WHEN** o gabarito de B01 é julgado
- **THEN** o status é `aceito`, os exemplos dão 3/3, os extras dão N/N e `completo` é verdadeiro

#### Scenario: Reprovado nos exemplos
- **WHEN** um código passa em 2 dos 3 exemplos
- **THEN** o status é `reprovado_exemplos` com exemplos 2/3

#### Scenario: Extras não revelados
- **WHEN** um código aceito falha em alguns extras
- **THEN** a resposta traz só as contagens de extras, sem índice, entrada, mensagem ou valor esperado

### Requirement: Caracteres significativos
O juiz SHALL calcular os caracteres significativos do código enviado exatamente como o aluno o enviou, antes da montagem. A contagem segue as regras léxicas do meupia-core:
- `//` fora de texto inicia um comentário até o fim da linha, e o comentário não conta;
- espaços em branco (espaço, tab, quebra de linha) fora de texto não contam;
- um texto vai de `"` até a próxima `"` da mesma linha que não está escapada (aspas precedidas de um número ímpar de `\` estão escapadas). Todos os caracteres do texto contam, inclusive as aspas, espaços e `//`;
- um texto sem aspas de fechamento conta até o fim da linha.

O valor SHALL ser calculado para todo julgamento que compila.

#### Scenario: Comentários e indentação não contam
- **WHEN** dois códigos diferem só pela indentação, por linhas em branco e por comentários `//`
- **THEN** os dois têm o mesmo número de caracteres significativos

#### Scenario: Espaço dentro de texto conta
- **WHEN** o código `escreva("a b")` é comparado a `escreva("ab")`
- **THEN** o primeiro tem 1 caractere significativo a mais

#### Scenario: `//` dentro de texto
- **WHEN** o código contém `"http://x"`
- **THEN** o `//` e o restante do texto contam como caracteres, não como comentário
