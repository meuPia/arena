import { test } from "node:test";
import assert from "node:assert/strict";
import { CHAVE_TEMA, lerTemaSalvo, gravarTema, definirTema, alternarTema, temaAtual } from "./tema.js";

function memoria(inicial = {}) {
  const dados = { ...inicial };
  return { getItem: (k) => dados[k] ?? null, setItem: (k, v) => { dados[k] = String(v); }, dados };
}
const quebrado = { getItem() { throw new Error("bloqueado"); }, setItem() { throw new Error("bloqueado"); } };
const docFalso = (tema) => ({ documentElement: { dataset: tema ? { theme: tema } : {} } });

test("padrão é o escuro sem escolha salva", () => {
  assert.equal(lerTemaSalvo(memoria()), "dark");
  assert.equal(lerTemaSalvo(null), "dark");
});

test("valor inválido salvo volta ao padrão", () => {
  assert.equal(lerTemaSalvo(memoria({ [CHAVE_TEMA]: "roxo" })), "dark");
});

test("escolha é gravada e lida de volta", () => {
  const s = memoria();
  assert.equal(gravarTema("light", s), true);
  assert.equal(lerTemaSalvo(s), "light");
});

test("armazenamento bloqueado não lança erro", () => {
  assert.equal(lerTemaSalvo(quebrado), "dark");
  assert.equal(gravarTema("light", quebrado), false);
  const doc = docFalso("dark");
  assert.equal(definirTema("light", { doc, storage: quebrado }), "light");
  assert.equal(doc.documentElement.dataset.theme, "light");
});

test("alternar troca o data-theme e persiste", () => {
  const s = memoria();
  const doc = docFalso("dark");
  assert.equal(alternarTema({ doc, storage: s }), "light");
  assert.equal(temaAtual(doc), "light");
  assert.equal(s.dados[CHAVE_TEMA], "light");
  assert.equal(alternarTema({ doc, storage: s }), "dark");
  assert.equal(s.dados[CHAVE_TEMA], "dark");
});

test("tema desconhecido vira o padrão", () => {
  const doc = docFalso();
  assert.equal(definirTema("neon", { doc, storage: memoria() }), "dark");
});
