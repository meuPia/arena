## ADDED Requirements

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
