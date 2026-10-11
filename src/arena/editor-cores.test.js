import { test } from "node:test";
import assert from "node:assert/strict";
import { CORES_EDITOR, CORES_TERMINAL, TOKENS_REALCE, contraste } from "./editor-cores.js";

for (const tema of ["dark", "light"]) {
  const c = CORES_EDITOR[tema];

  test(`realce do editor (${tema}) tem contraste ≥ 4,5:1`, () => {
    for (const token of TOKENS_REALCE) {
      const r = contraste(c[token], c.fundo);
      assert.ok(r >= 4.5, `${token} ${c[token]} sobre ${c.fundo}: ${r.toFixed(2)}`);
      assert.ok(contraste(c[token], c.linhaAtiva) >= 4.5, `${token} na linha ativa`);
    }
  });

  test(`números de linha (${tema}) têm contraste ≥ 4,5:1`, () => {
    assert.ok(contraste(c.numeros, c.gutter) >= 4.5);
    assert.ok(contraste(c.numeros, c.linhaAtiva) >= 4.5);
  });

  test(`comentário do editor (${tema}) tem contraste ≥ 3:1`, () => {
    assert.ok(contraste(c.comment, c.fundo) >= 3);
  });

  test(`classes de token (${tema}) têm cores distintas`, () => {
    const cores = ["keyword", "typeName", "string", "number", "operator", "atom"].map((t) => c[t]);
    assert.equal(new Set(cores).size, cores.length);
  });

  test(`terminal (${tema}): texto e cores ANSI usadas legíveis`, () => {
    const t = CORES_TERMINAL[tema];
    for (const cor of ["foreground", "red", "green", "yellow", "blue", "cyan"]) {
      const r = contraste(t[cor], t.background);
      assert.ok(r >= 4.5, `${cor} ${t[cor]}: ${r.toFixed(2)}`);
    }
  });
}
