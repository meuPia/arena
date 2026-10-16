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

### Requirement: IDE no celular
Em telas de até 768 px de largura, e em celulares deitados (até 500 px de altura com tela de toque), a IDE (`ide.html`) SHALL usar um layout de uma coluna que ocupa a altura
visível da tela, sem rolagem horizontal da página e sem divisores de arrastar:

- **Cabeçalho compacto**: marca reduzida ao ícone, botão de voltar às missões só com ícone (com nome acessível) e
  a faixa da missão em uma linha com selo do código, módulo (truncado com reticências se não couber), melhor
  pontuação e cronômetro. O cronômetro MUST continuar visível.
- **Menu "Mais"**: abrir, salvar, limpar, tema, ajuda e configurações SHALL ficar num menu aberto por um botão
  de ícone com nome acessível; desfazer e refazer SHALL continuar a um toque no cabeçalho. O menu MUST fechar com
  Esc, com toque fora dele e depois de escolher uma opção.
- **Abas**: Código, Missão e Terminal SHALL ser abas; só o painel ativo aparece e ocupa toda a área entre o
  cabeçalho e a barra de ação. A aba inicial é Código. A aba ativa MUST ser anunciada a leitores de tela.
- **Barra de ação**: Rodar e Submeter SHALL ficar fixos no rodapé, sempre visíveis, com alvos de pelo menos
  44 px, com os mesmos estados (desabilitado, julgando, espera) e textos do desktop.
- **Rodar**: ao tocar em Rodar, a IDE SHALL mostrar a aba Terminal; os resultados dos testes de exemplo
  continuam no fim da aba Missão.
- **Editor**: o texto do editor MUST ter pelo menos 16 px no celular, para o navegador não ampliar a página
  ao focar o editor; a configuração de tamanho de fonte vale acima desse mínimo.
- **Modais**: submeter, veredito, ajuda e configurações SHALL ocupar a tela toda, com o botão de fechar
  visível. A opção de layout do painel auxiliar MUST ficar oculta no celular.

Trocar de aba, girar o aparelho ou abrir o teclado virtual MUST NOT perder o código, o histórico de desfazer, a
saída do terminal nem os resultados dos testes. Fora desses casos (mais de 768 px de largura, ou sem tela de toque) a IDE SHALL manter o layout de desktop atual,
inclusive os divisores e a escolha de layout salva.

#### Scenario: Abrir a missão no celular
- **WHEN** uma equipe abre `ide.html?desafio=B91` com 360 px de largura
- **THEN** o cabeçalho ocupa no máximo duas linhas com selo, módulo, melhor pontuação e cronômetro visíveis, a
  aba Código está ativa com o editor ocupando a área central, Rodar e Submeter aparecem no rodapé e não há
  rolagem horizontal da página

#### Scenario: Rodar mostra o terminal
- **WHEN** no celular a equipe está na aba Código e toca em Rodar
- **THEN** a aba Terminal fica ativa, mostra a saída da execução com o terminal na largura da tela, e a aba
  Missão traz os resultados dos testes de exemplo no fim

#### Scenario: Trocar de aba preserva o trabalho
- **WHEN** a equipe edita o código, vai para a aba Missão e volta para Código
- **THEN** o código e o histórico de desfazer continuam iguais e o cursor fica onde estava

#### Scenario: Menu Mais
- **WHEN** a equipe toca no botão "Mais" e escolhe "Ajuda"
- **THEN** o menu fecha e o cartão do dialeto abre em tela cheia

#### Scenario: Foco no editor sem zoom
- **WHEN** a equipe toca no editor num celular com a fonte configurada em 14 px
- **THEN** o texto do editor aparece com 16 px e o navegador não amplia a página

#### Scenario: Submeter no celular
- **WHEN** a equipe toca em Submeter na barra do rodapé
- **THEN** o modal de participantes abre em tela cheia e, depois de enviar, o veredito aparece também em tela
  cheia com os mesmos textos do desktop

#### Scenario: Girar para paisagem
- **WHEN** o celular gira de retrato (390×844) para paisagem (844×390) com a aba Terminal ativa
- **THEN** a IDE continua em abas, e o terminal se reajusta à nova largura sem perder a saída

#### Scenario: Desktop inalterado
- **WHEN** a IDE é aberta com 1280 px de largura
- **THEN** o cabeçalho, os botões, os divisores de arrastar e o layout salvo nas configurações aparecem como antes
  desta mudança, sem abas nem barra de rodapé
