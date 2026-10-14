import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { htmlAjuda, indiceAjuda, buscar, destaques, normalizar, termosDaConsulta } from "./ajuda.js";

// O cartão real: se ele mudar de estrutura, estes testes mostram o que a Ajuda da IDE passa a exibir.
const CARTAO = readFileSync(new URL("../../docs/cartao-dialeto.md", import.meta.url), "utf8");
const indice = indiceAjuda(CARTAO);
const textos = (r) => r.map((t) => t.texto);
const algum = (r, trecho) => r.some((t) => t.texto.includes(trecho));

const SECOES = ["Estrutura", "Variáveis", "Operadores", "Decisão", "Repetição", "Texto", "Lista", "Dicionário",
  "Matemática", "Na Arena"];

test("cartão renderizado com seções, tabelas e código", () => {
  const html = htmlAjuda(CARTAO);
  for (const s of SECOES) assert.ok(html.includes(`<h2>${s}</h2>`), s);
  assert.ok(html.includes("<table>"));
  assert.ok(html.includes("<h3>Mensagens comuns</h3>"));
  assert.ok(html.includes("a variável &quot;k&quot; não foi declarada no bloco var"));
  assert.match(html, /<pre><code>[^]*\n {4}var r : inteiro {9}\/\/ variável local[^]*fim_algoritmo/);
});

test("normalizar tira acentos e maiúsculas", () => {
  assert.equal(normalizar("Função ÍNDICE não"), "funcao indice nao");
  assert.deepEqual(termosDaConsulta("  Divisão   inteira "), ["divisao", "inteira"]);
});

test("consulta vazia mostra o cartão inteiro", () => {
  assert.equal(buscar(indice, ""), null);
  assert.equal(buscar(indice, "   "), null);
});

test("dic acha dicionário, índice e adicionar", () => {
  const r = buscar(indice, "dic");
  assert.ok(r.some((t) => t.tipo === "titulo" && t.texto === "Dicionário"));
  assert.ok(algum(r, "var conta : dicionario"));
  assert.ok(algum(r, "índices começam em 0") && algum(r, "v.adicionar(8)"));
  assert.ok(algum(r, "índice fora da lista"));
  assert.ok(!algum(r, "sempre dá real"));
});

test("busca ignora acento", () => {
  assert.ok(algum(buscar(indice, "funcao"), "Os testes chamam a sua função"));
});

test("letras na ordem dentro da palavra", () => {
  const r = buscar(indice, "dcnr");
  assert.ok(algum(r, "var conta : dicionario") && algum(r, "v.adicionar(8)"));
  assert.ok(!algum(r, "índice fora da lista"));
});

test("termo não casa juntando letras de duas palavras", () => {
  const mini = indiceAjuda("## A\n\nvar conta\n\nvaconta\n");
  assert.deepEqual(textos(buscar(mini, "vaco")), ["vaconta"]);
});

test("vários termos: todos precisam casar", () => {
  const r = buscar(indice, "divisao inteira");
  assert.deepEqual(r.map((t) => t.tipo), ["item"]);
  assert.ok(r[0].texto.includes("piso(7 / 2)"));
});

test("nada encontrado", () => {
  assert.deepEqual(buscar(indice, "xyzw"), []);
});

test("linha de tabela vem com o cabeçalho", () => {
  const [linha] = buscar(indice, "dicionario").filter((t) => t.tipo === "linha");
  assert.equal(linha.secao, "Variáveis");
  assert.match(linha.markdown, /^\| Tipo \| Começa com \| Exemplo \|\n\|---\|---\|---\|\n\| `dicionario` /);
  assert.ok(htmlAjuda(linha.markdown).includes("<th>Tipo</th>"));
});

test("título que casa traz a seção inteira", () => {
  const r = buscar(indice, "Dicionário");
  assert.ok(algum(r, 'x <- conta.pegar("a", 0)'));
  const naArena = buscar(indice, "arena");
  assert.ok(naArena.some((t) => t.secao === "Na Arena › Mensagens comuns" && t.texto.includes("já foi declarada")));
});

test("destaques apontam para o texto original, com acento", () => {
  const texto = "índices e v.adicionar";
  assert.deepEqual(destaques(texto, ["dic"]).map(([a, b]) => texto.slice(a, b)), ["dic", "dic"]);
  assert.deepEqual(destaques("Dicionário", ["dcnr"]).map(([a, b]) => "Dicionário".slice(a, b)), ["D", "c", "n", "r"]);
  assert.deepEqual(destaques("nada aqui", ["xyz"]), []);
});
