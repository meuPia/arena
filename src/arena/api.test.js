import { test } from "node:test";
import assert from "node:assert/strict";
import { textoRelogio } from "./api.js";

const jan = { inicio: 1000, fim: 1000 + 160 * 60, ensaio: false };

test("antes do início mostra o tempo para abrir", () => {
  assert.deepEqual(textoRelogio(jan, 1000 - 90), { valor: "01:30", rotulo: "para abrir" });
});

test("aberto mostra o tempo restante", () => {
  assert.deepEqual(textoRelogio(jan, 1000 + 50 * 60), { valor: "1:50:00", rotulo: "restante" });
});

test("depois do fim mostra encerrado", () => {
  assert.equal(textoRelogio(jan, jan.fim + 1).rotulo, "encerrado");
});

test("modo ensaio e sem janela", () => {
  assert.equal(textoRelogio({ ...jan, ensaio: true }, 0).rotulo, "modo ensaio");
  assert.equal(textoRelogio(null, 0).valor, "--:--");
});
