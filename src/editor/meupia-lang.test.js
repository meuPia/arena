import { describe, test } from "node:test";
import assert from "node:assert/strict";
import { StringStream } from "@codemirror/language";
import { classificarPalavra, meuPiaTokenizer } from "./meupia-lang.js";

const PALAVRAS_RESERVADAS = [
    "algoritmo", "var", "inicio", "fim_algoritmo", "usar", "se", "entao", "então", "senao", "senão",
    "fim_se", "enquanto", "faca", "faça", "fim_enquanto", "para", "de", "ate", "até", "passo",
    "fim_para", "escreva", "leia", "retorne", "funcao", "fim_funcao", "classe", "metodo", "novo",
    "fim_classe", "interrompa", "continue", "e", "ou", "nao", "não", "mod"
];

const TIPOS_FIXOS = ["inteiro", "real", "float", "string", "cadeia", "dicionario", "filaPrioridade"];

/**
 * Tokeniza várias linhas com um único estado, como o CodeMirror faz.
 * Devolve, por linha, a lista de [texto, estilo] dos tokens não vazios.
 */
function tokenizar(texto) {
    const estado = meuPiaTokenizer.startState();
    return texto.split("\n").map(linha => {
        const stream = new StringStream(linha, 4, 4);
        const tokens = [];
        while (!stream.eol()) {
            stream.start = stream.pos;
            const estilo = meuPiaTokenizer.token(stream, estado);
            assert.ok(stream.pos > stream.start, `tokenizer não avançou em "${linha}"`);
            if (stream.current().trim()) tokens.push([stream.current(), estilo]);
        }
        return tokens;
    });
}

const estiloDe = (linhas, numeroLinha, texto) => {
    const token = linhas[numeroLinha].find(([t]) => t === texto);
    assert.ok(token, `token "${texto}" não encontrado na linha ${numeroLinha}`);
    return token[1];
};

describe("classificarPalavra", () => {
    test("todas as palavras reservadas do core são palavra-chave", () => {
        for (const palavra of PALAVRAS_RESERVADAS) {
            assert.equal(classificarPalavra(palavra, null), "keyword", palavra);
            assert.equal(classificarPalavra(palavra.toUpperCase(), null), "keyword", palavra.toUpperCase());
        }
    });

    test("função e fim_função não são palavra-chave", () => {
        assert.equal(classificarPalavra("função", null), "variableName");
        assert.equal(classificarPalavra("fim_função", null), "variableName");
    });

    test("tipos fixos são tipo em qualquer posição", () => {
        for (const tipo of TIPOS_FIXOS) {
            assert.equal(classificarPalavra(tipo, ":"), "typeName", tipo);
            assert.equal(classificarPalavra(tipo, null), "typeName", tipo);
            assert.equal(classificarPalavra(tipo, "<-"), "typeName", tipo);
        }
    });

    test("fila, pilha e heap não são tipo", () => {
        for (const palavra of ["fila", "pilha", "heap"]) {
            assert.equal(classificarPalavra(palavra, ":"), "variableName", palavra);
        }
    });

    test("lista e logico são tipo depois de ':' e de 'novo'", () => {
        for (const palavra of ["lista", "logico", "Lista"]) {
            assert.equal(classificarPalavra(palavra, ":"), "typeName", palavra);
            assert.equal(classificarPalavra(palavra, "novo"), "typeName", palavra);
            assert.equal(classificarPalavra(palavra, "NOVO"), "typeName", palavra);
        }
    });

    test("lista e logico são variável nas outras posições", () => {
        for (const palavra of ["lista", "logico"]) {
            for (const anterior of [null, "<-", "se", "literal", "(", ","]) {
                assert.equal(classificarPalavra(palavra, anterior), "variableName", `${palavra} depois de ${anterior}`);
            }
        }
    });

    test("atoms", () => {
        for (const atom of ["verdadeiro", "falso", "pi"]) {
            assert.equal(classificarPalavra(atom, null), "atom", atom);
        }
    });
});

describe("tokenizer com contexto", () => {
    test("lista como variável", () => {
        assert.equal(estiloDe(tokenizar("lista <- [1, 2]"), 0, "lista"), "variableName");
    });

    test("lista como tipo depois de ':' e de 'novo'", () => {
        const linhas = tokenizar("var l: lista\nx <- novo lista()");
        assert.equal(estiloDe(linhas, 0, ":"), "punctuation");
        assert.equal(estiloDe(linhas, 0, "lista"), "typeName");
        assert.equal(estiloDe(linhas, 1, "lista"), "typeName");
    });

    test("logico como variável", () => {
        assert.equal(estiloDe(tokenizar("se logico entao"), 0, "logico"), "variableName");
    });

    test("':' no fim da linha anterior vale para a linha seguinte", () => {
        assert.equal(estiloDe(tokenizar("var l:\n    lista"), 1, "lista"), "typeName");
    });

    test("linha anterior com ':' mas terminada em tipo não afeta a seguinte", () => {
        assert.equal(estiloDe(tokenizar("var x: inteiro\nlista <- [1]"), 1, "lista"), "variableName");
    });

    test("comentários não contam como token significativo", () => {
        assert.equal(estiloDe(tokenizar("var l: // comentario\n    lista"), 1, "lista"), "typeName");
    });

    test("realce existente continua igual", () => {
        const linhas = tokenizar([
            "se x != 1 entao",
            "y <- a >= b",
            "r <- a mod b",
            "r <- a % b",
            "r <- 3.14",
            'escreva("diga \\"oi\\"")',
            's <- "a\\\\"',
            "area <- pi * r * r",
            "var q: filaPrioridade",
            "var p: pilha"
        ].join("\n"));
        assert.equal(estiloDe(linhas, 0, "!="), "operator");
        assert.equal(estiloDe(linhas, 1, ">="), "operator");
        assert.equal(estiloDe(linhas, 2, "mod"), "keyword");
        assert.equal(estiloDe(linhas, 3, "%"), "operator");
        assert.equal(estiloDe(linhas, 4, "3.14"), "number");
        assert.equal(estiloDe(linhas, 5, '"diga \\"oi\\""'), "string");
        assert.equal(estiloDe(linhas, 6, '"a\\\\"'), "string");
        assert.equal(estiloDe(linhas, 7, "pi"), "atom");
        assert.equal(estiloDe(linhas, 8, "filaPrioridade"), "typeName");
        assert.equal(estiloDe(linhas, 9, "pilha"), "variableName");
    });
});
