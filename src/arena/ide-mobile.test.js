import { test } from "node:test";
import assert from "node:assert/strict";
import { ABAS, normalizarAba, aplicarAba, mostrarAba, deveIrParaTerminal, criarMenu } from "./ide-mobile.js";

function aba(alvo) {
  const attrs = {};
  return { dataset: { abaAlvo: alvo }, tabIndex: 0, attrs, setAttribute: (k, v) => { attrs[k] = v; } };
}
function docFalso() {
  const abas = ABAS.map(aba);
  const ouvintes = {};
  return {
    abas, ouvintes,
    body: { dataset: {} },
    querySelectorAll: () => abas,
    addEventListener: (tipo, fn) => { ouvintes[tipo] = fn; },
  };
}
function elemento() {
  const classes = new Set(), attrs = {}, ouvintes = {}, filhos = new Set();
  return {
    classes, attrs, ouvintes, filhos,
    classList: { add: (c) => classes.add(c), remove: (c) => classes.delete(c), contains: (c) => classes.has(c) },
    setAttribute: (k, v) => { attrs[k] = v; },
    addEventListener: (tipo, fn) => { ouvintes[tipo] = fn; },
    contains: (n) => n === this || filhos.has(n),
    focus() { this.focado = true; },
  };
}

test("aba inválida cai em Código", () => {
  assert.equal(normalizarAba("editor"), "codigo");
  assert.equal(normalizarAba(undefined), "codigo");
  assert.equal(normalizarAba("terminal"), "terminal");
});

test("só a aba ativa fica selecionada", () => {
  const doc = docFalso();
  assert.equal(aplicarAba(doc, "missao"), "missao");
  assert.equal(doc.body.dataset.aba, "missao");
  const selecionadas = doc.abas.filter((a) => a.attrs["aria-selected"] === "true");
  assert.deepEqual(selecionadas.map((a) => a.dataset.abaAlvo), ["missao"]);
  assert.deepEqual(doc.abas.map((a) => a.tabIndex), [-1, 0, -1]);
});

test("mostrar a aba limpa o marcador de novidade", () => {
  const doc = docFalso();
  doc.abas[1].dataset.novo = "1";
  aplicarAba(doc, "missao");
  assert.equal(doc.abas[1].dataset.novo, undefined);
});

test("Rodar só troca para o Terminal no celular", () => {
  assert.equal(deveIrParaTerminal(true), true);
  assert.equal(deveIrParaTerminal(false), false);
  assert.equal(deveIrParaTerminal(undefined), false);
});

test("mostrar o Terminal dispara resize depois do quadro", () => {
  const doc = docFalso();
  const eventos = [];
  let agendado = null;
  const janela = { dispatchEvent: (e) => eventos.push(e.type) };
  mostrarAba(doc, "terminal", { agendar: (fn) => { agendado = fn; }, janela });
  assert.deepEqual(eventos, []);
  agendado();
  assert.deepEqual(eventos, ["resize"]);
});

test("outras abas não disparam resize", () => {
  const doc = docFalso();
  let agendou = false;
  mostrarAba(doc, "missao", { agendar: () => { agendou = true; }, janela: {} });
  assert.equal(agendou, false);
});

function montarMenu() {
  const doc = docFalso(), botao = elemento(), painel = elemento();
  botao.contains = (n) => n === botao;
  const opcao = { closest: () => opcao };
  painel.filhos.add(opcao);
  painel.contains = (n) => painel.filhos.has(n);
  const menu = criarMenu({ botao, painel, doc });
  return { doc, botao, painel, menu, opcao };
}

test("botão Mais abre e fecha o menu com aria-expanded", () => {
  const { botao, menu } = montarMenu();
  botao.ouvintes.click();
  assert.equal(menu.aberto(), true);
  assert.equal(botao.attrs["aria-expanded"], "true");
  botao.ouvintes.click();
  assert.equal(menu.aberto(), false);
  assert.equal(botao.attrs["aria-expanded"], "false");
});

test("Esc fecha o menu e devolve o foco ao botão", () => {
  const { doc, botao, menu } = montarMenu();
  menu.abrir();
  doc.ouvintes.keydown({ key: "Escape" });
  assert.equal(menu.aberto(), false);
  assert.equal(botao.focado, true);
});

test("toque fora fecha o menu; toque dentro não", () => {
  const { doc, menu, opcao } = montarMenu();
  menu.abrir();
  doc.ouvintes.pointerdown({ target: opcao });
  assert.equal(menu.aberto(), true);
  doc.ouvintes.pointerdown({ target: {} });
  assert.equal(menu.aberto(), false);
});

test("escolher uma opção fecha o menu", () => {
  const { painel, menu, opcao } = montarMenu();
  menu.abrir();
  painel.ouvintes.click({ target: opcao });
  assert.equal(menu.aberto(), false);
});
