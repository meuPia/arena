## ADDED Requirements

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
