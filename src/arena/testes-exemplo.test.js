import { test } from "node:test";
import assert from "node:assert/strict";
import {
  linhasDeTeste, argumentosDaLinha, entradaDaLinha, trechoDiferente, janela, dica,
  ativarTestesArena, testesArenaAtivos, iniciarRodada, registrar, concluirRodada,
} from "./testes-exemplo.js";

// --- linhas e argumentos ---

test("linhas de teste seguem a regra do juiz", () => {
  const testes = 'esperar_igual(dobro(2), 4, "Exemplo 1")\n\n  // esperar_igual(1, 2)\n  esperar_igual(dobro(0), 0)\nx <- 1\n';
  assert.deepEqual(linhasDeTeste(testes), ['esperar_igual(dobro(2), 4, "Exemplo 1")', "esperar_igual(dobro(0), 0)"]);
  assert.deepEqual(linhasDeTeste(""), []);
  assert.deepEqual(linhasDeTeste(undefined), []);
});

test("entrada é o primeiro argumento, como está no desafio", () => {
  assert.equal(entradaDaLinha('esperar_igual(dobro(2), 4, "Exemplo 1")'), "dobro(2)");
  assert.deepEqual(argumentosDaLinha('esperar_igual(dobro(2), 4, "Exemplo 1")'), {
    funcao: "esperar_igual", argumentos: ["dobro(2)", "4", '"Exemplo 1"'],
  });
});

test("vírgulas aninhadas ou dentro de cadeias não separam argumentos", () => {
  assert.deepEqual(argumentosDaLinha('esperar_igual(soma(1, [2, 3], {"a": 1}), 6, "x")').argumentos,
    ['soma(1, [2, 3], {"a": 1})', "6", '"x"']);
  assert.deepEqual(argumentosDaLinha('esperar_igual(juntar("a, b", "c)"), "a, bc)", "msg")').argumentos,
    ['juntar("a, b", "c)")', '"a, bc)"', '"msg"']);
  assert.deepEqual(argumentosDaLinha('esperar_igual(f("diz \\"oi, tudo\\""), 1)').argumentos,
    ['f("diz \\"oi, tudo\\"")', "1"]);
  assert.deepEqual(argumentosDaLinha("esperar_verdadeiro()").argumentos, []);
});

test("linha desbalanceada: a entrada é a linha inteira", () => {
  assert.equal(argumentosDaLinha("esperar_igual(dobro(2, 4"), null);
  assert.equal(entradaDaLinha("  esperar_igual(dobro(2, 4  "), "esperar_igual(dobro(2, 4");
  assert.equal(entradaDaLinha("esperar_igual(dobro(2]), 4)"), "esperar_igual(dobro(2]), 4)");
});

// --- trecho diferente e janela ---

const meio = (texto, r) => Array.from(texto).slice(r.inicio, r.fim).join("");

test("espaço sobrando no fim: só o · fica destacado", () => {
  const d = trechoDiferente('"ok"', '"ok·"');
  assert.equal(meio('"ok"', d.a), "");
  assert.equal(meio('"ok·"', d.b), "·");
});

test("maiúscula: o primeiro caractere fica destacado nos dois lados", () => {
  const d = trechoDiferente('"Ola"', '"ola"');
  assert.equal(meio('"Ola"', d.a), "O");
  assert.equal(meio('"ola"', d.b), "o");
});

test("caractere faltando: um lado fica sem meio", () => {
  const d = trechoDiferente('"abc"', '"ac"');
  assert.equal(meio('"abc"', d.a), "b");
  assert.deepEqual(d.b, { inicio: 2, fim: 2 });
});

test("iguais: sem destaque", () => {
  const d = trechoDiferente("4", "4");
  assert.equal(d.a.inicio, d.a.fim);
  assert.equal(d.b.inicio, d.b.fim);
});

test("emoji não é partido", () => {
  const d = trechoDiferente('"a😀"', '"a😁"');
  assert.equal(meio('"a😀"', d.a), "😀");
  assert.equal(meio('"a😁"', d.b), "😁");
});

test("valor longo mantém a diferença visível", () => {
  const a = "x".repeat(1000) + "A";
  const b = "x".repeat(1000) + "B";
  const d = trechoDiferente(a, b);
  const j = janela(a, d.a.inicio, 300);
  assert.equal(j.fim - j.inicio, 300);
  assert.ok(j.inicio > 0, "corta o começo");
  assert.ok(d.a.inicio >= j.inicio && d.a.fim <= j.fim, "a diferença fica dentro da janela");
  assert.deepEqual(janela("curto", 0, 300), { inicio: 0, fim: 5 });
  assert.deepEqual(janela("x".repeat(500), 0, 300), { inicio: 0, fim: 300 });
});

// --- dicas ---

const valor = (tipo, texto, bruto) => ({ tipo, texto, bruto });
const cadeia = (s) => valor("cadeia", JSON.stringify(s), s);
const igual = (esperado, obtido) => ({ funcao: "igual", ok: false, erro: null, esperado, obtido });

test("dica: sem valor", () => {
  assert.match(dica(igual(valor("inteiro", "4", 4), valor("sem valor", "sem valor"))), /sem retorne/);
});

test("dica: inteiro esperado, real obtido", () => {
  assert.match(dica(igual(valor("inteiro", "3", 3), valor("real", "3.5", 3.5))), /piso\(a \/ b\)/);
});

test("dica: tipos diferentes", () => {
  assert.equal(dica(igual(valor("inteiro", "5", 5), cadeia("5"))), "O esperado é inteiro e o obtido é cadeia.");
});

test("dica: espaço nas pontas", () => {
  assert.match(dica(igual(cadeia("ok"), cadeia("ok "))), /início ou no fim/);
});

test("dica: espaços ou quebras de linha", () => {
  assert.match(dica(igual(cadeia("a b"), cadeia("a\nb"))), /espaços ou quebras de linha/);
});

test("dica: maiúsculas", () => {
  assert.match(dica(igual(cadeia("Ola"), cadeia("ola"))), /maiúsculas e minúsculas/);
});

test("dica: acentos", () => {
  assert.match(dica(igual(cadeia("ação"), cadeia("acao"))), /acentos/);
});

test("dica: reais muito próximos", () => {
  assert.match(dica(igual(valor("real", "0.3", 0.3), valor("real", "0.30000000000000004", 0.1 + 0.2))), /casas decimais/);
});

test("sem dica quando nenhuma regra se aplica", () => {
  assert.equal(dica(igual(valor("inteiro", "3", 3), valor("inteiro", "7", 7))), null);
  assert.equal(dica(igual(cadeia("abc"), cadeia("xyz"))), null);
  assert.equal(dica({ ...igual(valor("inteiro", "4", 4), valor("inteiro", "4", 4)), ok: true }), null);
  assert.equal(dica({ ...igual(valor("inteiro", "4", 4), cadeia("x")), funcao: "maior" }), null);
});

test("duas regras possíveis: vale a primeira", () => {
  // "OK " × "OK" casaria também a regra 5 (espaços ou quebras de linha): vale a 4.
  assert.match(dica(igual(cadeia("OK "), cadeia("OK"))), /início ou no fim/);
  // inteiro × real com valores próximos: regra 2 vem antes da 8.
  assert.match(dica(igual(valor("inteiro", "3", 3), valor("real", "3.0000000000001", 3.0000000000001))), /piso/);
});

// --- painel (DOM falso mínimo) ---

class No {
  constructor(tag) { this.tag = tag; this.filhos = []; this.className = ""; this.attrs = {}; this._texto = null; }
  set textContent(t) { this.filhos = []; this._texto = String(t); }
  get textContent() { return this._texto ?? this.filhos.map((f) => (typeof f === "string" ? f : f.textContent)).join(""); }
  get classList() { return { contains: (c) => this.className.split(" ").includes(c) }; }
  setAttribute(k, v) { this.attrs[k] = v; }
  append(...nos) { if (this._texto !== null) { this.filhos = [this._texto]; this._texto = null; } this.filhos.push(...nos); }
  replaceChildren(...nos) { this._texto = null; this.filhos = nos; }
  todos() { return this.filhos.flatMap((f) => (typeof f === "string" ? [] : [f, ...f.todos()])); }
  querySelector(sel) { return this.todos().find((n) => n.classList.contains(sel.slice(1))) || null; }
  querySelectorAll(sel) { return this.todos().filter((n) => n.classList.contains(sel.slice(1))); }
}
const docFalso = () => {
  const resultados = new No("div");
  return { resultados, createElement: (t) => new No(t), getElementById: (id) => (id === "test-results" ? resultados : null) };
};
function pyodideFalso({ falhar = false } = {}) {
  const globais = new Map();
  let n = null;
  return {
    globals: { has: (k) => globais.has(k), delete: (k) => globais.delete(k), get: (k) => globais.get(k), set: (k, v) => globais.set(k, v) },
    registerJsModule() {},
    toPy: () => ({ get: (k) => (k === "iniciar_rodada" ? (x) => { n = x; } : undefined) }),
    runPython() { if (falhar) throw new Error("sem meupia_testes"); },
    n: () => n,
  };
}
const TESTES = 'esperar_igual(dobro(2), 4, "Exemplo 1")\nesperar_igual(dobro(0), 0, "Exemplo 2")\nesperar_igual(dobro(-3), -6, "Exemplo 3")';
const resultado = (k, ok, esperado, obtido, extra = {}) => JSON.stringify({ k, funcao: "igual", ok, erro: null, mensagem: `Exemplo ${k + 1}`, esperado, obtido, ...extra });

test("plugin indisponível: segue o painel do Lab", () => {
  assert.equal(ativarTestesArena(null, "x"), false);
  assert.equal(ativarTestesArena(pyodideFalso({ falhar: true }), "x", docFalso()), false);
  assert.equal(testesArenaAtivos(), false);
});

test("rodada: resumo, cartão reprovado com tipos e não executado", () => {
  const doc = docFalso();
  const py = pyodideFalso();
  assert.equal(ativarTestesArena(py, "codigo", doc), true);
  iniciarRodada(py, TESTES, doc);
  assert.equal(py.n(), 3);
  registrar(resultado(0, true, { tipo: "inteiro", texto: "4" }, { tipo: "inteiro", texto: "4" }));
  registrar(resultado(1, false, { tipo: "inteiro", texto: "0" }, { tipo: "cadeia", texto: '"0"', bruto: "0" }));
  assert.equal(doc.resultados.querySelectorAll(".test-item").length, 2, "desenha na hora, sem pendentes");
  py.globals.set("codigo_retorno", 0);
  py.globals.set("gerou_py", true);
  concluirRodada(py);

  const r = doc.resultados;
  assert.equal(r.querySelector(".arena-testes-resumo").textContent, "1 de 3 exemplos aprovados");
  const cartoes = r.querySelectorAll(".test-item");
  assert.equal(cartoes.length, 3);
  assert.ok(cartoes[0].classList.contains("success"));
  assert.equal(cartoes[0].querySelector(".arena-teste-lados"), null, "aprovado é compacto");
  assert.match(cartoes[0].textContent, /entrada: dobro\(2\)/);
  assert.ok(cartoes[1].classList.contains("fail"));
  assert.match(cartoes[1].textContent, /Esperado inteiro0/);
  assert.match(cartoes[1].textContent, /Obtido cadeia"0"/);
  assert.equal(cartoes[1].todos().filter((n) => n.tag === "mark").length, 2, "rótulos de tipo destacados");
  assert.match(cartoes[1].querySelector(".arena-teste-dica").textContent, /inteiro e o obtido é cadeia/);
  assert.ok(cartoes[2].classList.contains("pendente"));
  assert.match(cartoes[2].textContent, /não executado/);
});

test("valor do aluno entra como texto e o espaço sobrando fica destacado", () => {
  const doc = docFalso();
  const py = pyodideFalso();
  ativarTestesArena(py, "codigo", doc);
  iniciarRodada(py, 'esperar_igual(f(), "ok", "Exemplo 1")', doc);
  registrar(resultado(0, false, { tipo: "cadeia", texto: '"ok"', bruto: "ok" }, { tipo: "cadeia", texto: '"ok·"', bruto: "ok " }));
  const lados = doc.resultados.querySelectorAll(".arena-teste-lado");
  const marks = (n) => n.todos().filter((x) => x.tag === "mark");
  assert.equal(marks(lados[1])[0].textContent, "·");
  assert.ok(marks(lados[0])[0].classList.contains("arena-teste-falta"));
  assert.match(doc.resultados.querySelector(".arena-teste-dica").textContent, /início ou no fim/);
  registrar(resultado(0, false, { tipo: "cadeia", texto: '"x"' }, { tipo: "cadeia", texto: '"<b>oi</b>"' }));
  assert.match(doc.resultados.textContent, /"<b>oi<\/b>"/);
  assert.equal(doc.resultados.todos().some((n) => n.tag === "b"), false);
});

test("erro de compilação deixa a área vazia", () => {
  const doc = docFalso();
  const py = pyodideFalso();
  ativarTestesArena(py, "codigo", doc);
  py.globals.set("codigo_retorno", 0);
  py.globals.set("gerou_py", true);
  iniciarRodada(py, TESTES, doc); // apaga os globais da rodada anterior
  py.globals.set("codigo_retorno", 1);
  concluirRodada(py);
  assert.equal(doc.resultados.filhos.length, 0);
});
