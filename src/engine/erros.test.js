import { describe, test } from "node:test";
import assert from "node:assert/strict";
import {
    extrairMensagemErro,
    mapearLinhaErro,
    formatarMensagemErro,
    MENSAGEM_BLOCO_ABERTO
} from "./erros.js";

const comLogDoLexer = (mensagem) => [
    "(Lexer started)",
    "Scanning line [1]...",
    "Scanning line [2]...",
    "Scanning line [3]...",
    "Scanning line [4]...",
    "[COMPILATION ERROR]:",
    mensagem,
    ""
].join("\n");

describe("extrairMensagemErro", () => {
    test("erro léxico cercado pelo log do lexer", () => {
        const erro = extrairMensagemErro(comLogDoLexer('Erro léxico na linha 4, coluna 8: caractere inesperado: "$"'));
        assert.deepEqual(erro, {
            tipo: "léxico",
            linha: 4,
            coluna: 8,
            descricao: 'caractere inesperado: "$"',
            texto: 'Erro léxico na linha 4, coluna 8: caractere inesperado: "$"'
        });
    });

    test("saída real do core 1.2.0 (mensagem indentada com tab)", () => {
        const saida = 'Compilando main.por...\n(Lexer started)\nScanning line [1]...\talgoritmo "Teste"\n' +
            'Scanning line [4]...\tx <- 7 $ 2\n[COMPILATION ERROR]:\n\tErro léxico na linha 4, coluna 8: caractere desconhecido "$"\n';
        const erro = extrairMensagemErro(saida);
        assert.equal(erro.linha, 4);
        assert.equal(erro.coluna, 8);
        assert.equal(erro.texto, 'Erro léxico na linha 4, coluna 8: caractere desconhecido "$"');
    });

    test("erro sintático", () => {
        const erro = extrairMensagemErro(comLogDoLexer('Erro sintático na linha 6, coluna 1: comando inesperado: "fim_algoritmo"'));
        assert.equal(erro.tipo, "sintático");
        assert.equal(erro.linha, 6);
        assert.equal(erro.coluna, 1);
        assert.equal(erro.descricao, 'comando inesperado: "fim_algoritmo"');
    });

    test("erro semântico", () => {
        const erro = extrairMensagemErro(comLogDoLexer("Erro semântico na linha 3, coluna 5: variável 'y' não declarada"));
        assert.equal(erro.tipo, "semântico");
        assert.equal(erro.linha, 3);
        assert.equal(erro.coluna, 5);
    });

    test("arquivo vazio aponta linha 1, coluna 1", () => {
        const erro = extrairMensagemErro("[COMPILATION ERROR]:\nErro sintático na linha 1, coluna 1: fim de arquivo inesperado\n");
        assert.equal(erro.linha, 1);
        assert.equal(erro.coluna, 1);
    });

    test("texto fora do formato depois do marcador", () => {
        const erro = extrairMensagemErro("(Lexer started)\n[COMPILATION ERROR]:\n  Arquivo 'main.por' não encontrado  \n");
        assert.equal(erro.linha, null);
        assert.equal(erro.texto, "Arquivo 'main.por' não encontrado");
    });

    test("saída sem marcador devolve a saída inteira", () => {
        const erro = extrairMensagemErro("(Lexer started)\nScanning line [1]...\tx\n  algo inesperado aconteceu\n");
        assert.equal(erro.linha, null);
        assert.equal(erro.texto, "algo inesperado aconteceu");
    });
});

describe("mapearLinhaErro", () => {
    // Editor com 5 linhas; "usar testes" inserido depois da linha 1 -> montado tem 6 linhas do aluno.
    // Anexo: linha 7 em branco, 8 comentário, 9-10 codigoTeste, 11 fim_algoritmo.
    const infoInserido = { linhaUsarTestes: 2, inicioAnexo: 7, linhaFimAnexado: 11 };
    const infoJaPresente = { linhaUsarTestes: null, inicioAnexo: 6, linhaFimAnexado: 10 };

    test("sem desafio a linha não muda", () => {
        assert.deepEqual(mapearLinhaErro(5, null), { origem: "editor", linha: 5 });
    });

    test("com usar testes inserido, linhas seguintes voltam 1", () => {
        assert.deepEqual(mapearLinhaErro(6, infoInserido), { origem: "editor", linha: 5 });
    });

    test("linha anterior à inserção não muda", () => {
        assert.deepEqual(mapearLinhaErro(1, infoInserido), { origem: "editor", linha: 1 });
    });

    test("a própria linha inserida é dos testes", () => {
        assert.deepEqual(mapearLinhaErro(2, infoInserido), { origem: "testes" });
    });

    test("com usar testes já presente, a linha não muda", () => {
        assert.deepEqual(mapearLinhaErro(5, infoJaPresente), { origem: "editor", linha: 5 });
    });

    test("linha dentro do codigoTeste é dos testes", () => {
        assert.deepEqual(mapearLinhaErro(9, infoInserido), { origem: "testes" });
        assert.deepEqual(mapearLinhaErro(7, infoInserido), { origem: "testes" });
    });

    test("fim_algoritmo anexado indica bloco aberto", () => {
        assert.deepEqual(mapearLinhaErro(11, infoInserido), { origem: "bloco-aberto" });
    });
});

describe("formatarMensagemErro", () => {
    const erro = {
        tipo: "léxico",
        linha: 6,
        coluna: 8,
        descricao: 'caractere inesperado: "$"',
        texto: 'Erro léxico na linha 6, coluna 8: caractere inesperado: "$"'
    };

    test("troca a linha pela do editor", () => {
        assert.equal(
            formatarMensagemErro(erro, { origem: "editor", linha: 5 }),
            'Erro léxico na linha 5, coluna 8: caractere inesperado: "$"'
        );
    });

    test("origem testes", () => {
        assert.equal(
            formatarMensagemErro(erro, { origem: "testes" }),
            'Erro nos testes automáticos do desafio: caractere inesperado: "$"'
        );
    });

    test("origem bloco-aberto não mostra linha", () => {
        const mensagem = formatarMensagemErro(erro, { origem: "bloco-aberto" });
        assert.equal(mensagem, MENSAGEM_BLOCO_ABERTO);
        assert.doesNotMatch(mensagem, /linha \d/);
    });

    test("fallback devolve o texto sem alteração", () => {
        const fallback = { tipo: null, linha: null, coluna: null, descricao: null, texto: "Arquivo não encontrado" };
        assert.equal(formatarMensagemErro(fallback, null), "Arquivo não encontrado");
    });
});
