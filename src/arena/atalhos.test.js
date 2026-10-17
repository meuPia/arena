import { test } from "node:test";
import assert from "node:assert/strict";
import { atalhoDoEvento, podeAgir, ehMac, textoAtalho, setupAtalhos } from "./atalhos.js";

const tecla = (extra = {}) => ({ key: "Enter", ctrlKey: false, metaKey: false, shiftKey: false, altKey: false, ...extra });

test("Ctrl/⌘+Enter roda; com Shift, submete", () => {
  assert.equal(atalhoDoEvento(tecla({ ctrlKey: true })), "rodar");
  assert.equal(atalhoDoEvento(tecla({ metaKey: true })), "rodar");
  assert.equal(atalhoDoEvento(tecla({ ctrlKey: true, shiftKey: true })), "submeter");
  assert.equal(atalhoDoEvento(tecla({ metaKey: true, shiftKey: true })), "submeter");
});

test("outras combinações não são atalho", () => {
  assert.equal(atalhoDoEvento(tecla()), null);
  assert.equal(atalhoDoEvento(tecla({ shiftKey: true })), null);
  assert.equal(atalhoDoEvento(tecla({ ctrlKey: true, altKey: true })), null);
  assert.equal(atalhoDoEvento(tecla({ key: "a", ctrlKey: true })), null);
  assert.equal(atalhoDoEvento(undefined), null);
});

test("podeAgir: botão habilitado, sem modal e sem repetição", () => {
  const botao = { disabled: false };
  assert.equal(podeAgir({ botao, modalAberto: false, repeticao: false }), true);
  assert.equal(podeAgir({ botao: null, modalAberto: false, repeticao: false }), false);
  assert.equal(podeAgir({ botao: { disabled: true }, modalAberto: false, repeticao: false }), false);
  assert.equal(podeAgir({ botao, modalAberto: true, repeticao: false }), false);
  assert.equal(podeAgir({ botao, modalAberto: false, repeticao: true }), false);
});

test("ehMac e texto do atalho", () => {
  assert.equal(ehMac({ userAgentData: { platform: "macOS" } }), true);
  assert.equal(ehMac({ platform: "MacIntel" }), true);
  assert.equal(ehMac({ platform: "Win32" }), false);
  assert.equal(ehMac({ platform: "Linux x86_64" }), false);
  assert.equal(ehMac({}), false);
  assert.equal(textoAtalho("rodar", false), "Ctrl+Enter");
  assert.equal(textoAtalho("submeter", false), "Ctrl+Shift+Enter");
  assert.equal(textoAtalho("rodar", true), "⌘+Enter");
  assert.equal(textoAtalho("submeter", true), "⌘+Shift+Enter");
});

// --- setupAtalhos com documento e janela falsos ---

function ambiente({ rodarDesabilitado = false, submeterDesabilitado = false, modal = false } = {}) {
  const cliques = [];
  const botao = (id, disabled) => ({
    id, disabled, title: "", attrs: {},
    setAttribute(k, v) { this.attrs[k] = v; },
    click() { cliques.push(id); },
  });
  const botoes = { "run-btn": botao("run-btn", rodarDesabilitado), "submit-btn": botao("submit-btn", submeterDesabilitado) };
  const modais = [{ classList: { contains: (c) => c === "hidden" && !modal } }];
  const doc = { getElementById: (id) => botoes[id] || null, querySelectorAll: () => modais };
  let ouvinte = null, opcoes = null;
  const janela = { addEventListener: (tipo, fn, o) => { if (tipo === "keydown") { ouvinte = fn; opcoes = o; } } };
  const disparar = (extra) => {
    const ev = { ...tecla(extra), consumido: false, parado: false };
    ev.preventDefault = () => { ev.consumido = true; };
    ev.stopPropagation = () => { ev.parado = true; };
    ouvinte(ev);
    return ev;
  };
  return { doc, janela, botoes, cliques, disparar, opcoes: () => opcoes };
}

test("setupAtalhos: captura, consome e clica no botão", () => {
  const a = ambiente();
  setupAtalhos({ doc: a.doc, janela: a.janela, navegador: { platform: "Win32" } });
  assert.equal(a.opcoes().capture, true);
  const ev = a.disparar({ ctrlKey: true });
  assert.ok(ev.consumido && ev.parado);
  a.disparar({ ctrlKey: true, shiftKey: true });
  assert.deepEqual(a.cliques, ["run-btn", "submit-btn"]);
  const outro = a.disparar({ key: "a", ctrlKey: true });
  assert.equal(outro.consumido, false, "outras teclas seguem normalmente");
});

test("setupAtalhos: botão desabilitado consome sem clicar", () => {
  const a = ambiente({ rodarDesabilitado: true, submeterDesabilitado: true });
  setupAtalhos({ doc: a.doc, janela: a.janela, navegador: {} });
  const ev = a.disparar({ ctrlKey: true });
  a.disparar({ ctrlKey: true, shiftKey: true });
  assert.ok(ev.consumido, "o editor não insere linha");
  assert.deepEqual(a.cliques, []);
});

test("setupAtalhos: modal aberto ou repetição não clicam", () => {
  const a = ambiente({ modal: true });
  setupAtalhos({ doc: a.doc, janela: a.janela, navegador: {} });
  a.disparar({ ctrlKey: true });
  const b = ambiente();
  setupAtalhos({ doc: b.doc, janela: b.janela, navegador: {} });
  b.disparar({ ctrlKey: true, repeat: true });
  assert.deepEqual([...a.cliques, ...b.cliques], []);
});

test("setupAtalhos: dica e aria-keyshortcuts nos botões", () => {
  const a = ambiente();
  setupAtalhos({ doc: a.doc, janela: a.janela, navegador: { platform: "Linux x86_64" } });
  assert.equal(a.botoes["run-btn"].title, "Rodar os testes de exemplo (Ctrl+Enter)");
  assert.equal(a.botoes["submit-btn"].title, "Envia para o juiz (testes de exemplo + testes extras) (Ctrl+Shift+Enter)");
  assert.equal(a.botoes["run-btn"].attrs["aria-keyshortcuts"], "Control+Enter Meta+Enter");
  assert.equal(a.botoes["submit-btn"].attrs["aria-keyshortcuts"], "Control+Shift+Enter Meta+Shift+Enter");
  const m = ambiente();
  setupAtalhos({ doc: m.doc, janela: m.janela, navegador: { userAgentData: { platform: "macOS" } } });
  assert.equal(m.botoes["run-btn"].title, "Rodar os testes de exemplo (⌘+Enter)");
  assert.equal(m.botoes["submit-btn"].title, "Envia para o juiz (testes de exemplo + testes extras) (⌘+Shift+Enter)");
});
