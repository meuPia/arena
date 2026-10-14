## ADDED Requirements

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
