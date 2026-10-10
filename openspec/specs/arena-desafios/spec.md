# arena-desafios Specification

## Purpose
Definir o formato dos desafios da Code Arena (testes de exemplo e bateria de testes extras), como a bateria extra é gerada de forma reproduzível e como os gabaritos e os códigos iniciais são validados contra o juiz real.

## Requirements

### Requirement: Campos de teste do desafio
Cada `arena/desafios/<COD>.json` SHALL ter `testesPublicos` (os testes de exemplo, que o botão Rodar do Lab executa no navegador) e `testesExtras` (a bateria de submissão, só no servidor). O campo `testesOcultos` MUST NOT existir mais. Cada linha de teste é uma chamada `esperar_*`.

#### Scenario: Campo renomeado
- **WHEN** os 9 desafios (B01, B02, B03, S01, S02, S03, G01, G02, X01) são carregados
- **THEN** todos têm `testesPublicos` e `testesExtras`, e nenhum tem `testesOcultos`

### Requirement: Testes extras nunca saem do servidor
`testesExtras` MUST NOT aparecer em nenhuma resposta da API ao navegador. O desafio público SHALL conter só os campos públicos de hoje: código, id, módulo, problema técnico, nível, pontos, formato, tempo esperado, título, descrição, código inicial e `testesPublicos`.

#### Scenario: Missão sem extras
- **WHEN** uma equipe abre a missão S01
- **THEN** a resposta não contém `testesExtras` nem nenhum texto de teste extra

### Requirement: Tamanho e dificuldade da bateria extra
A bateria extra de cada desafio SHALL ter entre 15 e 25 testes, com a meta de cerca de 20. Ela inclui os casos de borda atuais (os antigos `testesOcultos`) e casos grandes ou aleatórios, nos limites do desafio, por exemplo: listas de até 300 itens, matrizes de até 12×12, números com até 80 dígitos e rotas de até 120 passos. Os textos dos testes gerados MUST NOT conter aspas duplas nem barra invertida dentro de literais de texto.

#### Scenario: Bateria ampliada
- **WHEN** a bateria extra de qualquer desafio é contada
- **THEN** ela tem entre 15 e 25 linhas `esperar_*` e contém todos os casos de borda de `arena/extras_base/<COD>.txt`

### Requirement: Geração determinística
A bateria extra SHALL ser gerada por `scripts/gerar_testes_extras.py` com semente fixa. O script usa uma implementação de referência em Python de cada desafio para calcular os valores esperados e junta, em ordem, os casos de borda de `arena/extras_base/<COD>.txt` e os casos gerados. Rodar o script duas vezes sem mudar as entradas MUST produzir arquivos idênticos. O script SHALL atualizar só o campo `testesExtras` de cada desafio.

#### Scenario: Reprodutível
- **WHEN** o script roda duas vezes seguidas
- **THEN** `git diff` não mostra mudança entre as duas execuções

### Requirement: Validação dos desafios
`npm run validar` SHALL julgar cada desafio com o juiz real e falhar se alguma destas condições não valer:
- o gabarito tem veredito `aceito` e completo (100% dos exemplos e dos extras);
- o código inicial **não** é completo;
- nenhum teste do gabarito chega perto do limite por teste (margem: no máximo metade do limite);
- a bateria extra respeita o tamanho do requisito anterior.

#### Scenario: Gabarito lento
- **WHEN** um teste extra faz o gabarito levar mais da metade do limite por teste
- **THEN** a validação aponta o desafio e o teste e termina com erro

#### Scenario: Tudo certo
- **WHEN** todos os desafios estão corretos
- **THEN** a validação imprime uma linha `OK` por desafio, com exemplos e extras do gabarito e do código inicial, e termina com sucesso

### Requirement: Enunciados explicam a pontuação
A descrição de cada desafio SHALL explicar que enviar exige passar em todos os testes de exemplo, que os pontos dependem da bateria de testes extras ("N de M") e que, no empate, vence o menor código (comentários e indentação não contam).

#### Scenario: Regra visível no enunciado
- **WHEN** uma equipe abre qualquer missão
- **THEN** o enunciado contém a explicação da pontuação por testes extras e do desempate por menor código
