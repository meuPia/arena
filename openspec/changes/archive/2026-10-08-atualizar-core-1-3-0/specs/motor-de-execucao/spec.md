## MODIFIED Requirements

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
