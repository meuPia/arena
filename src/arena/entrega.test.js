import { test } from "node:test";
import assert from "node:assert/strict";
import { comCabecalho, nomeArquivo } from "./entrega.js";

test("o arquivo entregue começa com o código do desafio", () => {
  assert.equal(comCabecalho("algoritmo x\n", "B01"), "// arena: B01\nalgoritmo x\n");
  assert.equal(nomeArquivo("G02"), "G02.por");
});

test("salvar de novo (ou abrir um .por já salvo) não duplica nem mistura cabeçalhos", () => {
  const uma = comCabecalho("inicio\n", "B01");
  assert.equal(comCabecalho(uma, "B01"), uma);
  assert.equal(comCabecalho(uma, "S02"), "// arena: S02\ninicio\n");
  assert.equal(comCabecalho("// meu comentário\ninicio", "B01"), "// arena: B01\n// meu comentário\ninicio");
});
