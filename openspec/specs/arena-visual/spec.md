# arena-visual Specification

## Purpose
Definir a identidade visual da Code Arena (painel, IDE, placar e admin), os temas escuro e claro, como a escolha
de tema é aplicada e lembrada, e os requisitos de legibilidade e acessibilidade das páginas.

## Requirements

### Requirement: Identidade visual comum
As páginas `index.html`, `ide.html`, `placar.html` e `admin.html` SHALL usar o mesmo sistema visual: as mesmas
cores de fundo, superfície, borda, texto e destaque; a mesma marca "meuPiá ARENA"; e uma cor fixa por nível
(Bronze, Silver, Gold, Extra) em todo lugar onde o nível aparece (selos, código do módulo, cabeçalhos do placar).
Títulos, botões e selos SHALL usar a fonte de destaque (Chakra Petch); texto corrido, a fonte de texto (IBM Plex
Sans); código, números, cronômetro e terminal, a fonte monoespaçada (JetBrains Mono). As fontes MUST ser servidas
pela própria aplicação, sem depender de serviço externo de fontes.

#### Scenario: Cor do nível consistente
- **WHEN** o módulo S91 aparece no painel, na IDE, no placar e no admin
- **THEN** o código e o selo do nível usam a mesma cor de Silver nas quatro páginas, no tema ativo

#### Scenario: Fontes sem internet externa
- **WHEN** a página é aberta numa rede que bloqueia `fonts.googleapis.com`
- **THEN** títulos, texto e código aparecem nas fontes do sistema visual

### Requirement: Temas escuro e claro
Cada página SHALL ter dois temas, escuro e claro, com os mesmos componentes e a mesma disposição. O tema escuro
SHALL ser o padrão quando não houver escolha salva. No tema claro, textos em cor de destaque SHALL usar a variante
escura da cor (o verde-limão continua só como fundo de botões e selos).

#### Scenario: Primeira visita
- **WHEN** um navegador sem escolha salva abre `index.html`
- **THEN** a página aparece no tema escuro

#### Scenario: Mesmo layout nos dois temas
- **WHEN** a equipe alterna o tema no painel de missões
- **THEN** os cartões, níveis e cabeçalho continuam nas mesmas posições, só com as cores do outro tema

### Requirement: Alternância e persistência do tema
O painel (depois do login), a IDE e o admin SHALL ter um botão para alternar entre escuro e claro, com rótulo
acessível. A escolha SHALL valer para todas as páginas da Arena naquele navegador e ser lembrada entre visitas. Se o
navegador não permitir guardar a escolha, a alternância SHALL funcionar na página atual e o padrão volta a ser o
escuro na próxima carga. A página MUST NOT mostrar o tema errado por um instante antes de aplicar o tema salvo. O
placar do telão SHALL seguir a escolha salva, sem botão visível.

#### Scenario: Escolha vale para a IDE
- **WHEN** a equipe escolhe o tema claro no painel e abre uma missão
- **THEN** a IDE abre no tema claro, inclusive o editor e o terminal

#### Scenario: Escolha lembrada
- **WHEN** a equipe escolhe o tema claro, fecha o navegador e volta à Arena
- **THEN** as páginas abrem no tema claro

#### Scenario: Armazenamento bloqueado
- **WHEN** o navegador recusa gravar a escolha e a equipe alterna para o claro
- **THEN** a página atual muda para o claro sem erro, e uma nova página abre no escuro

### Requirement: Editor e terminal confortáveis
Na IDE, o editor de código e o terminal SHALL ter um tema próprio para cada tema da página, de fundo neutro e
sem efeitos decorativos (grade, brilho, cantos chanfrados) dentro da área de código. O realce de sintaxe SHALL
manter as classes de token definidas em `editor-portugol` com cores distintas entre si e contraste mínimo de
4,5:1 sobre o fundo do editor; comentários podem ficar abaixo disso, desde que acima de 3:1. A linha do cursor
SHALL ser destacada, e a fonte do editor SHALL ser monoespaçada, respeitando o tamanho escolhido nas
configurações. Trocar de tema MUST NOT apagar o código, o histórico de desfazer nem a saída do terminal.

#### Scenario: Troca de tema preserva o trabalho
- **WHEN** a equipe tem código digitado, saída no terminal e alterna o tema
- **THEN** o código, o desfazer e a saída do terminal continuam iguais, só com as cores do novo tema

#### Scenario: Contraste do realce
- **WHEN** o editor mostra palavras-chave, tipos, strings, números e operadores, em qualquer dos temas
- **THEN** cada classe de token tem contraste de pelo menos 4,5:1 com o fundo do editor

### Requirement: Estados das missões no painel
Os cartões do painel SHALL diferenciar visualmente os estados completo, parcial, aberta e bloqueada, não só por
cor: cada estado tem rótulo em texto, e a missão bloqueada SHALL mostrar um cadeado com nome acessível e o
requisito para liberar. Cartões liberados SHALL ser links navegáveis por teclado; cartões bloqueados MUST NOT ser
focáveis nem clicáveis.

#### Scenario: Missão bloqueada
- **WHEN** a equipe ainda não liberou o nível Gold
- **THEN** o cartão de G91 mostra o cadeado, o texto "Bloqueada" e o requisito, e a tecla Tab passa por ele sem parar

### Requirement: Placar legível no telão
O placar SHALL ser legível a distância numa tela de 1920×1080: nome da equipe e pontos em fonte grande, os
símbolos ●/◐/○ com cores distintas e também diferentes na forma, e uma legenda dos símbolos. A 1ª posição SHALL ter
destaque visual. Quando o placar estiver congelado, a página SHALL mostrar um aviso de placar congelado visível.

#### Scenario: Placar congelado
- **WHEN** faltam menos de 20 minutos e o placar público está congelado
- **THEN** o telão mostra o aviso "Placar congelado" junto do tempo restante

### Requirement: Acessibilidade e responsividade
Todas as páginas SHALL ter texto com contraste de pelo menos 4,5:1 (3:1 para textos de 24 px ou mais) nos dois
temas, alvos de toque de pelo menos 44 px nos controles principais, foco de teclado visível, botões só com ícone
com nome acessível, e funcionar a partir de 360 px de largura sem rolagem horizontal da página (tabelas largas
rolam dentro da própria caixa). Animações decorativas MUST ser desligadas quando o sistema pedir movimento
reduzido.

#### Scenario: Botão de ícone
- **WHEN** um leitor de tela chega ao botão de voltar da IDE ou ao botão de tema
- **THEN** ele anuncia o nome do botão

#### Scenario: Celular
- **WHEN** o painel de missões é aberto com 360 px de largura
- **THEN** os cartões ficam em uma coluna e não há rolagem horizontal da página
