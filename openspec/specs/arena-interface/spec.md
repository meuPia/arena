# arena-interface Specification

## Purpose
Definir o que a IDE da missão, o painel da equipe, o placar do telão e a visão admin mostram sobre o veredito da submissão e a pontuação no modelo de exemplos + extras.

## Requirements

### Requirement: Veredito na IDE
Depois de uma submissão, a IDE SHALL mostrar o veredito nestes formatos:
- aceito e completo: `✅ ACEITO — <a>/<t> testes extras · <p>/<P> pts · <c> caracteres`
- aceito parcial: `🟡 ACEITO PARCIAL — <a>/<t> extras · <p>/<P> pts`
- reprovado nos exemplos: `❌ Passe primeiro em todos os testes de exemplo (<a>/<t>)`
- erro de compilação, erro de execução e cooldown: mensagens como as de hoje.

Para submissões aceitas, a IDE SHALL mostrar também a melhor pontuação da equipe no módulo e os caracteres dessa melhor submissão. A IDE MUST NOT mostrar qual teste extra falhou.

#### Scenario: Completo
- **WHEN** a submissão é aceita com 20/20 extras num módulo de 10 pts e 142 caracteres
- **THEN** a IDE mostra `✅ ACEITO — 20/20 testes extras · 10/10 pts · 142 caracteres`

#### Scenario: Parcial
- **WHEN** a submissão é aceita com 14/20 extras num módulo de 10 pts
- **THEN** a IDE mostra `🟡 ACEITO PARCIAL — 14/20 extras · 7/10 pts` e a melhor pontuação da equipe no módulo

#### Scenario: Reprovado nos exemplos
- **WHEN** a submissão passa em 2 de 3 exemplos
- **THEN** a IDE mostra `❌ Passe primeiro em todos os testes de exemplo (2/3)`

### Requirement: Botão Submeter sempre disponível
O botão Submeter SHALL continuar disponível depois que o módulo estiver completo, enquanto a janela estiver aberta e fora do cooldown. O status da missão na IDE SHALL mostrar a melhor pontuação (por exemplo `Melhor: 7/10 pts`) e o selo de completo quando houver.

#### Scenario: Módulo completo
- **WHEN** a equipe abre a IDE de um módulo completo, fora do cooldown
- **THEN** o botão Submeter está habilitado e o status mostra a melhor pontuação com o selo de completo

### Requirement: Card do painel
Cada card de módulo liberado no painel SHALL mostrar a melhor pontuação da equipe no formato `<p>/<P> pts`, o selo de completo quando completo, e o número de tentativas. Módulo sem submissão aceita SHALL mostrar só os pontos do módulo e as tentativas, como hoje.

#### Scenario: Card parcial
- **WHEN** a equipe tem 7 pts em B01, não completo
- **THEN** o card de B01 mostra `7/10 pts`, sem selo de completo

### Requirement: Placar do telão
O placar SHALL ter as colunas posição, equipe, uma coluna por nível, Pontos, Completos e Caracteres. Em cada nível, cada módulo aparece como `●` (completo), `◐` (aceito parcial) ou `○` (sem submissão aceita). A coluna Caracteres mostra a soma dos caracteres das melhores submissões completas. O placar público MUST NOT mostrar código-fonte nem participantes.

#### Scenario: Linha do telão
- **WHEN** uma equipe tem B01 completo, B02 parcial e B03 sem submissão aceita
- **THEN** a coluna Bronze mostra `●◐○`

### Requirement: Log do admin
O log de submissões SHALL ficar na seção Submissões do painel administrativo (`/admin.html`), e não mais em `/placar.html`. Para cada submissão, ele mostra horário, equipe, módulo, tentativa, status, exemplos aprovados/total, extras aprovados/total, pontos calculados, pontos efetivos (destacando quando há ajuste), caracteres e participantes. O `/placar.html` MUST mostrar só o placar: ele não exibe log, código-fonte nem participantes, mesmo quando aberto por alguém da banca.

#### Scenario: Submissão parcial no log
- **WHEN** um admin ou juiz abre a seção Submissões do painel depois de uma submissão aceita com 14/20 extras
- **THEN** a linha mostra exemplos 3/3, extras 14/20, os pontos e os caracteres dessa submissão

#### Scenario: Submissão ajustada no log
- **WHEN** a submissão foi ajustada de 10 para 0 pts
- **THEN** a linha mostra os pontos calculados (10), os efetivos (0) destacados e o motivo ao abrir a submissão

#### Scenario: Placar do telão sem log
- **WHEN** alguém abre `/placar.html`
- **THEN** a página mostra só o placar, sem a tabela de submissões

### Requirement: Textos da IDE sobre o juiz
Os textos da IDE que hoje falam em "testes ocultos" SHALL falar em "testes extras" e explicar a regra: enviar exige passar em todos os exemplos, os pontos dependem dos extras e o menor código desempata.

#### Scenario: Aviso no modal de submissão
- **WHEN** a equipe abre o modal de submissão
- **THEN** o aviso fala em testes de exemplo e testes extras, não em testes ocultos

### Requirement: Cronômetro na IDE
O cabeçalho da IDE SHALL mostrar o cronômetro do evento, sincronizado com o horário do servidor: o tempo para
abrir antes do início, o tempo restante enquanto estiver aberto e "encerrado" depois do fim; no modo ensaio, o
rótulo do modo ensaio. Para isso, a resposta da missão SHALL incluir a janela do evento (início, fim, freeze,
agora, situação e ensaio), calculada com o horário efetivo (incluindo o definido pelo painel).

#### Scenario: Tempo restante
- **WHEN** a equipe abre uma missão às 20h00 e o evento termina às 21h50
- **THEN** o cabeçalho da IDE mostra `1:50:00` como tempo restante (mesmo formato do painel), diminuindo a cada segundo

#### Scenario: Evento encerrado
- **WHEN** a equipe está na IDE e passa do horário de fim
- **THEN** o cronômetro mostra que o evento foi encerrado

### Requirement: Ajuda do dialeto na IDE
O cabeçalho da IDE da missão SHALL ter um botão Ajuda, com rótulo acessível, que abre um modal "Cartão do dialeto" com o conteúdo de `docs/cartao-dialeto.md`, sem cortes, renderizado como Markdown: títulos, listas, tabelas e blocos de código com a indentação preservada. O conteúdo MUST vir desse arquivo, para que a IDE e o cartão impresso não divirjam. O modal SHALL seguir o tema atual da Arena (claro ou escuro) e rolar por dentro quando o conteúdo passar da altura da tela.

O modal SHALL fechar pelo botão de fechar, pela tecla `Esc` com o campo de busca vazio e por clique fora do conteúdo. Ao fechar, o foco SHALL voltar ao editor. Abrir ou fechar a ajuda, ou buscar nela, MUST NOT alterar o código do editor nem o histórico de desfazer, MUST NOT fazer chamadas à API e MUST NOT interferir em Rodar, Submeter ou no cronômetro.

#### Scenario: Abrir a ajuda
- **WHEN** a equipe clica no botão Ajuda na IDE de uma missão
- **THEN** abre o modal "Cartão do dialeto" com as seções do cartão (Estrutura, Variáveis, Operadores, Decisão, Repetição, Texto, Lista, Dicionário, Matemática e Na Arena), incluindo a tabela "Mensagens comuns"

#### Scenario: Código do cartão legível
- **WHEN** o modal mostra o exemplo da seção Estrutura
- **THEN** o exemplo aparece num bloco de código, com a indentação e os comentários `//` como estão no cartão

#### Scenario: Fechar com Esc
- **WHEN** o modal de ajuda está aberto com o campo de busca vazio e a equipe aperta `Esc`
- **THEN** o modal fecha e o cursor volta ao editor, na posição em que estava

#### Scenario: Fechar clicando fora
- **WHEN** a equipe clica fora do conteúdo do modal
- **THEN** o modal fecha

#### Scenario: Código preservado
- **WHEN** a equipe escreve código, abre a ajuda, busca algo, fecha e depois aperta Desfazer
- **THEN** o código continua igual e Desfazer desfaz a última edição feita antes de abrir a ajuda

#### Scenario: Cartão atualizado
- **WHEN** alguém altera `docs/cartao-dialeto.md` e a Arena é publicada de novo
- **THEN** o modal de ajuda mostra o texto novo, e a busca encontra esse texto, sem nenhuma outra edição

#### Scenario: Tema claro
- **WHEN** a equipe está no tema claro e abre a ajuda
- **THEN** o modal, as tabelas, os blocos de código, o campo de busca e o destaque usam as cores do tema claro

### Requirement: Busca na ajuda do dialeto
O modal de ajuda SHALL ter um campo de busca no topo, que recebe o foco quando o modal abre. Com o campo vazio, o modal SHALL mostrar o cartão inteiro. Com texto, o modal SHALL mostrar só os trechos do cartão que casam, na ordem do cartão e sob o título da seção de cada um. Um trecho é uma linha de tabela (mostrada com o cabeçalho da tabela), um item de lista, um parágrafo ou um bloco de código. Quando o título de uma seção casa, a seção inteira aparece.

A busca SHALL ignorar acentos e maiúsculas e SHALL separar a consulta em termos pelos espaços. Um trecho casa quando **todos** os termos casam nele. Um termo casa com uma palavra do trecho quando é um prefixo dela, um pedaço dela ou quando as letras do termo aparecem na mesma ordem dentro dessa palavra. Um termo MUST NOT casar juntando letras de palavras diferentes. O que casou SHALL aparecer destacado no trecho. A busca MUST NOT tolerar letras erradas (por exemplo, `dicionaro` não acha "dicionario"). Os resultados SHALL atualizar a cada tecla.

Sem nenhum trecho que case, o modal SHALL mostrar "Nada encontrado para "<consulta>"". Com texto no campo, `Esc` SHALL limpar a busca e voltar ao cartão inteiro, sem fechar o modal.

#### Scenario: Prefixo e pedaço de palavra
- **WHEN** a equipe digita `dic` na busca
- **THEN** aparecem a seção Dicionário, a linha `dicionario` da tabela de Variáveis, o bloco de código da Lista (por "índices" e "adicionar") e a linha "um exemplo deu erro durante a execução" de Mensagens comuns (por "índice"), com `dic` destacado em cada um

#### Scenario: Sem acento
- **WHEN** a equipe digita `funcao`
- **THEN** aparecem também os trechos que só têm "função" com acento, como "Os testes chamam a sua função"

#### Scenario: Letras na ordem dentro da palavra
- **WHEN** a equipe digita `dcnr`
- **THEN** aparecem os trechos com "dicionario" ou "Dicionário" e o bloco de código da Lista (por "adicionar"), e não aparece a linha de Mensagens comuns com "índice"

#### Scenario: Letras de palavras diferentes não casam
- **WHEN** a equipe digita `dcnr` e um trecho só tem essas letras espalhadas em palavras diferentes
- **THEN** esse trecho não aparece

#### Scenario: Vários termos
- **WHEN** a equipe digita `divisao inteira`
- **THEN** aparece o item de Operadores sobre `piso(7 / 2)` e não aparecem trechos que só falam de "divisão"

#### Scenario: Nada encontrado
- **WHEN** a equipe digita `xyzw`
- **THEN** o modal mostra `Nada encontrado para "xyzw"`

#### Scenario: Esc limpa a busca
- **WHEN** há texto na busca e a equipe aperta `Esc`
- **THEN** o campo fica vazio, o cartão inteiro volta e o modal continua aberto; um segundo `Esc` fecha o modal

#### Scenario: Foco na busca
- **WHEN** a equipe abre a ajuda
- **THEN** o cursor já está no campo de busca e o que ela digitar vai para a busca, não para o editor

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

### Requirement: Atalhos de teclado na IDE
A IDE da missão SHALL ter dois atalhos de teclado, que valem com o foco em qualquer lugar da página (editor, terminal, painel da missão):
- `Ctrl+Enter` SHALL ter o mesmo efeito de um clique no botão Rodar;
- `Ctrl+Shift+Enter` SHALL ter o mesmo efeito de um clique no botão Submeter, ou seja, abrir o modal de Submeter. O atalho MUST NOT enviar a submissão: a equipe continua marcando os participantes e confirmando no modal.

No Mac, `⌘` SHALL valer no lugar de `Ctrl`. Combinações com `Alt` MUST NOT acionar os atalhos.

Os atalhos MUST NOT agir quando:
- o botão correspondente está desabilitado (motor carregando, cooldown, julgamento em andamento, submissões fechadas);
- algum modal da IDE está aberto (Configurações, Submeter, Ajuda ou resultado do juiz);
- o evento é repetição automática de uma tecla mantida pressionada.

As duas combinações MUST NOT ter outro efeito na IDE, mesmo quando o atalho não age: com o foco no editor, `Ctrl+Enter` MUST NOT inserir linha nem alterar o código ou o histórico de desfazer.

Os botões Rodar e Submeter SHALL mostrar o atalho na dica (`title`): "Rodar os testes de exemplo (Ctrl+Enter)" e "Envia para o juiz (testes de exemplo + testes extras) (Ctrl+Shift+Enter)", com `⌘` no lugar de `Ctrl` no Mac. Os botões SHALL declarar o atalho também em `aria-keyshortcuts`. Com as submissões fechadas, a dica do Submeter continua "Submissões fechadas".

#### Scenario: Rodar pelo editor
- **WHEN** o motor está pronto, o foco está no editor e a equipe aperta `Ctrl+Enter`
- **THEN** os testes de exemplo rodam como num clique em Rodar, e o código e o histórico de desfazer continuam iguais

#### Scenario: Rodar pelo terminal
- **WHEN** o foco está no terminal e a equipe aperta `Ctrl+Enter`
- **THEN** os testes de exemplo rodam

#### Scenario: Abrir o modal de Submeter
- **WHEN** o botão Submeter está habilitado e a equipe aperta `Ctrl+Shift+Enter`
- **THEN** o modal de Submeter abre, e nada é enviado ao juiz

#### Scenario: Mac
- **WHEN** a equipe usa um Mac e aperta `⌘+Enter`
- **THEN** os testes de exemplo rodam, e a dica do botão Rodar mostra `⌘+Enter`

#### Scenario: Motor carregando
- **WHEN** o botão Rodar ainda está desabilitado e a equipe aperta `Ctrl+Enter` com o foco no editor
- **THEN** nada acontece: nada roda e nenhuma linha é inserida

#### Scenario: Cooldown
- **WHEN** o botão Submeter mostra o tempo de espera e a equipe aperta `Ctrl+Shift+Enter`
- **THEN** o modal de Submeter não abre

#### Scenario: Modal aberto
- **WHEN** o modal de Ajuda está aberto e a equipe aperta `Ctrl+Enter`
- **THEN** nada roda, e o modal continua aberto

#### Scenario: Tecla mantida pressionada
- **WHEN** a equipe mantém `Ctrl+Enter` pressionado
- **THEN** o Rodar é acionado uma vez só

#### Scenario: Dica nos botões
- **WHEN** a equipe passa o mouse sobre o botão Rodar num computador com Windows ou Linux
- **THEN** a dica mostra "Rodar os testes de exemplo (Ctrl+Enter)"

### Requirement: Modal de Submeter pelo teclado
Ao abrir o modal de Submeter, por clique ou pelo atalho, o foco SHALL ir para o primeiro participante da lista (ou para o campo de nomes, quando a equipe não tem integrantes cadastrados). Com o modal aberto, `Esc` SHALL fechá-lo sem enviar nada e devolver o foco ao editor. Abrir e fechar o modal MUST NOT alterar o código nem os participantes já marcados.

#### Scenario: Foco ao abrir
- **WHEN** a equipe abre o modal de Submeter
- **THEN** o foco está no primeiro participante, e Espaço o marca

#### Scenario: Fechar com Esc
- **WHEN** o modal de Submeter está aberto e a equipe aperta `Esc`
- **THEN** o modal fecha, nada é enviado ao juiz, e o cursor volta ao editor na posição em que estava

#### Scenario: Fluxo só com teclado
- **WHEN** a equipe aperta `Ctrl+Shift+Enter`, marca um participante com Espaço, vai com Tab até "Enviar para o juiz" e aperta Enter
- **THEN** a submissão é enviada ao juiz e o resultado aparece, como pelo mouse
