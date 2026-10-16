## Purpose

Dar à banca da Code Arena um painel web para organizar o evento sem redeploy: equipes e códigos de acesso, participantes, perfis de admin e juiz, desafios, acompanhamento das submissões, ajuste de pontos e auditoria de tudo o que foi feito.

## ADDED Requirements

### Requirement: Cadastro de desafios
O painel SHALL ter uma seção **Desafios**, só para admin, que lista os desafios (código, nível, pontos, título, número de testes extras e resultado da última validação) e permite criar e editar todos os campos: código, módulo, problema técnico, nível, pontos, formato, tempo esperado, inspiração, título, descrição (markdown), código inicial, testes de exemplo, testes extras e gabarito. O código do desafio é obrigatório, único e não pode ser alterado depois de criado. O nível MUST ser um dos níveis da config, e os pontos um inteiro positivo. Ao salvar, os testes MUST ser conferidos: só linhas `esperar_*`, sem aspas duplas nem barra invertida dentro de textos. Editar um desafio que já recebeu submissões SHALL pedir confirmação, avisando que a mudança não rejulga as submissões antigas. A auditoria SHALL registrar a criação e a edição com o código do desafio e a lista dos campos alterados, sem o conteúdo.

#### Scenario: Criar desafio
- **WHEN** o admin cria o desafio B04 no nível Bronze, com 10 pts e todos os campos preenchidos
- **THEN** B04 aparece para as equipes no nível Bronze em até 30 segundos

#### Scenario: Juiz não vê a seção
- **WHEN** um juiz entra no painel
- **THEN** a seção Desafios não aparece, e as ações de desafio respondem 403

#### Scenario: Edição auditada sem conteúdo
- **WHEN** o admin altera os testes extras de S03
- **THEN** a auditoria registra "desafio editado: S03 (testesExtras)" sem o texto dos testes

### Requirement: Validação de desafios pelo painel
O admin SHALL poder validar um desafio, ou todos, com o juiz real, pelo painel, com os mesmos critérios do `npm run validar`. O resultado mostra, por desafio, o veredito do gabarito (exemplos e extras), o veredito do código inicial, o maior tempo por teste e os erros encontrados. O painel SHALL também permitir validar o formulário antes de salvar.

#### Scenario: Gabarito quebrado
- **WHEN** o admin valida um desafio cujo gabarito falha em 2 extras
- **THEN** o painel mostra "gabarito não é aceito e completo" com extras 18/20

### Requirement: Exportação e importação de desafios
O admin SHALL poder exportar todos os desafios (partes pública e secreta) num arquivo JSON e importar um arquivo nesse formato. A importação mostra o que será criado e o que será substituído, pede confirmação, valida cada desafio com o juiz e grava só os válidos. Exportação e importação SHALL ir para a auditoria.

#### Scenario: Backup antes do evento
- **WHEN** o admin exporta os desafios
- **THEN** ele baixa um JSON com os 9 desafios, inclusive testes extras e gabaritos, que pode ser reimportado em outro banco
