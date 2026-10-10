# motor-de-execucao Specification

## Purpose
Compilar o código Portugol do editor com o meupia-core dentro do Pyodide, executar o programa gerado e apresentar ao aluno, no terminal, o resultado ou um erro de compilação claro e localizado na linha do editor.

## Requirements

### Requirement: Versão do compilador
O Lab SHALL instalar e usar o meupia-core na versão `1.3.0`.

#### Scenario: Inicialização do motor
- **WHEN** o Lab inicializa o motor WebAssembly
- **THEN** o terminal anuncia `Baixando Compilador meuPiá v1.3.0`
- **AND** o pacote instalado é `meupia-core==1.3.0`

#### Scenario: Recursos da linguagem do core 1.2.0
- **WHEN** o aluno executa um programa válido que usa `escreva("x=", 5)` e `se x != 1 entao`
- **THEN** o terminal mostra `x=5`
- **AND** o bloco `se` é avaliado sem erro de compilação

#### Scenario: Recursos da linguagem do core 1.3.0
- **WHEN** o aluno executa um programa válido com `funcao dobro(a)`, que contém `var r: inteiro <- a * 2` e `retorne r`, e com `escreva(dobro(4))` no `inicio`
- **THEN** o terminal mostra `8`

### Requirement: Detecção de sucesso da compilação
O Lab SHALL considerar a compilação bem-sucedida somente quando o compilador retornar `0` **e** o programa Python gerado existir. Qualquer outro caso MUST ser tratado como erro de compilação, e o programa MUST NOT ser executado.

#### Scenario: Compilação bem-sucedida
- **WHEN** o compilador retorna `0` e gera o programa Python
- **THEN** o terminal mostra `[EXECUTANDO]` e executa o programa

#### Scenario: Compilador retorna código de erro
- **WHEN** o compilador retorna `1` ou `2`
- **THEN** o terminal mostra `[ERRO DE COMPILAÇÃO]`
- **AND** nada é executado

#### Scenario: Retorno zero sem programa gerado
- **WHEN** o compilador retorna `0`, mas o programa Python não foi gerado
- **THEN** o resultado é tratado como erro de compilação e nada é executado

### Requirement: Mensagem de erro de compilação limpa
Em erro de compilação, o terminal SHALL mostrar apenas o cabeçalho `[ERRO DE COMPILAÇÃO]` seguido de uma mensagem. O log de depuração do compilador (por exemplo `(Lexer started)` e `Scanning line [n]...`) MUST NOT aparecer.
- Se a saída do compilador tiver uma linha no formato `Erro <léxico|sintático|semântico> na linha L, coluna C: <descrição>`, a mensagem SHALL ser essa linha, com `L` trocado pela linha do editor (ver requisito de mapeamento).
- Senão, se houver o marcador `[COMPILATION ERROR]:`, a mensagem SHALL ser o texto que vem depois do marcador, sem espaços sobrando nas pontas.
- Senão, a mensagem SHALL ser a saída completa do compilador.

#### Scenario: Erro léxico padronizado
- **WHEN** o aluno compila um programa sem desafio com `x <- 7 $ 2` na linha 4
- **THEN** o terminal mostra `[ERRO DE COMPILAÇÃO]` e uma única linha que começa com `Erro léxico na linha 4, coluna`
- **AND** nenhuma linha `(Lexer started)` ou `Scanning line` aparece

#### Scenario: Erro fora do formato padronizado
- **WHEN** a saída do compilador contém `[COMPILATION ERROR]:` seguido de um texto que não segue o formato padronizado (por exemplo, arquivo inexistente)
- **THEN** o terminal mostra `[ERRO DE COMPILAÇÃO]` e esse texto

### Requirement: Linha do erro referente ao editor
A linha mostrada ao aluno e usada para marcar o editor SHALL ser a linha do editor, e não a do programa montado para o desafio. Linhas e colunas do core começam em 1. Quando o Lab insere `usar "testes"` depois da linha `algoritmo "..."`, os erros nas linhas seguintes MUST ser reportados com a linha diminuída em 1. Um erro na linha `usar "testes"` inserida ou dentro do `codigoTeste` anexado SHALL ser mostrado como `Erro nos testes automáticos do desafio: <descrição>`, sem número de linha, e MUST NOT marcar o editor. O caso do `fim_algoritmo` anexado é tratado no requisito "Bloco não fechado em desafio".

#### Scenario: Sem desafio
- **WHEN** não há desafio carregado e o compilador reporta erro na linha 5
- **THEN** o aluno vê a linha 5

#### Scenario: Desafio com `usar "testes"` inserido
- **WHEN** um desafio está carregado, o editor não tem `usar "testes"` e há um erro na linha 5 do editor
- **THEN** o compilador reporta a linha 6 do programa montado
- **AND** o aluno vê a linha 5

#### Scenario: Desafio em que o aluno já escreveu `usar "testes"`
- **WHEN** um desafio está carregado, o editor já tem `usar "testes"` e há um erro na linha 5 do editor
- **THEN** o aluno vê a linha 5

#### Scenario: Erro na linha anterior à inserção
- **WHEN** a inserção ocorreu depois da linha 1 e o compilador reporta erro na linha 1
- **THEN** o aluno vê a linha 1

#### Scenario: Erro dentro do código de teste do desafio
- **WHEN** o compilador reporta erro numa linha que pertence ao `codigoTeste` anexado
- **THEN** o terminal mostra `Erro nos testes automáticos do desafio: <descrição>`
- **AND** nenhuma linha do editor é marcada

### Requirement: Bloco não fechado em desafio
Quando um desafio está carregado e o compilador reporta o erro na linha do `fim_algoritmo` anexado pelo Lab (a última linha do programa montado), o terminal SHALL mostrar, depois de `[ERRO DE COMPILAÇÃO]`, a orientação `Algum bloco não foi fechado. Confira se cada se, enquanto, para, funcao e classe tem o seu fim_… correspondente.` Nesse caso, o Lab MUST NOT mostrar número de linha e MUST NOT marcar o editor.

#### Scenario: `fim_se` faltando num desafio
- **WHEN** um desafio está carregado, o aluno esquece um `fim_se` e o compilador reporta `Erro sintático … comando inesperado: "fim_algoritmo"` na última linha do programa montado
- **THEN** o terminal mostra `[ERRO DE COMPILAÇÃO]` e a orientação sobre bloco não fechado
- **AND** não aparece "Erro nos testes automáticos do desafio"
- **AND** nenhuma linha do editor é marcada

#### Scenario: `fim_se` faltando sem desafio
- **WHEN** não há desafio carregado, o aluno esquece um `fim_se` e o compilador reporta o erro na linha do `fim_algoritmo` do próprio aluno
- **THEN** o terminal mostra a mensagem padronizada com essa linha e o editor marca essa linha

### Requirement: Execuções isoladas
Cada execução SHALL rodar o programa gerado num namespace novo, que contém só `__name__ = "__main__"` (mais os builtins que o Python injeta). Variáveis, funções e classes definidas numa execução MUST NOT existir na seguinte.

#### Scenario: Função apagada entre execuções
- **WHEN** o aluno executa um programa que define e chama a função `f`, depois apaga a definição de `f` (mantendo a chamada) e executa de novo
- **THEN** a segunda execução falha ao chamar `f`

### Requirement: Erros de execução inalterados
Exceções Python levantadas durante a execução do programa gerado SHALL continuar sendo mostradas como hoje: `[ERRO DO SISTEMA]` seguido do texto da exceção. `SystemExit` continua sendo ignorado em silêncio.

#### Scenario: Divisão por zero em tempo de execução
- **WHEN** o programa compila e, ao executar, levanta `ZeroDivisionError`
- **THEN** o terminal mostra `[ERRO DO SISTEMA]` e o texto da exceção, como antes desta mudança
