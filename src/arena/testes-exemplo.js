// Resultado dos testes de exemplo no Rodar: esperado × obtido, com tipo, destaque da diferença e dica.
// Os valores chegam já formatados pelo plugin_testes_arena.py (Pyodide); aqui ficam as funções puras
// (testadas com node --test) e o painel da aba Missão. Ver design.md da change esperado-obtido-nos-exemplos.

const LARGURA_VALOR = 300; // caracteres visíveis de um valor (o Python já corta em 2.000)

// Linhas de teste do desafio, com a mesma regra do juiz (juiz._linhas_de_teste).
export function linhasDeTeste(testes) {
  return (testes || "").split("\n").map((l) => l.trim()).filter((l) => l.startsWith("esperar_"));
}

const PAR = { "(": ")", "[": "]", "{": "}" };

// Separa os argumentos de `esperar_xxx(a, b, "msg")` pelas vírgulas de nível zero. null se não der.
export function argumentosDaLinha(linha) {
  const m = /^\s*(esperar_\w+)\s*\(/.exec(linha || "");
  if (!m) return null;
  const argumentos = [];
  const abertos = [];
  let aspas = null;
  let atual = "";
  for (let i = m[0].length; i < linha.length; i++) {
    const c = linha[i];
    if (aspas) {
      atual += c;
      if (c === "\\" && i + 1 < linha.length) atual += linha[++i];
      else if (c === aspas) aspas = null;
      continue;
    }
    if (c === '"' || c === "'") aspas = c;
    else if ("([{".includes(c)) abertos.push(PAR[c]);
    else if (")]}".includes(c)) {
      if (abertos.length === 0) {
        if (c !== ")") return null;
        argumentos.push(atual.trim());
        return { funcao: m[1], argumentos: argumentos.length === 1 && !argumentos[0] ? [] : argumentos };
      }
      if (abertos.pop() !== c) return null;
    } else if (c === "," && abertos.length === 0) {
      argumentos.push(atual.trim());
      atual = "";
      continue;
    }
    atual += c;
  }
  return null;
}

export function entradaDaLinha(linha) {
  const r = argumentosDaLinha(linha);
  return r && r.argumentos[0] ? r.argumentos[0] : (linha || "").trim();
}

// Trecho diferente entre dois textos: maior prefixo e maior sufixo comuns, sem sobreposição.
// Índices em código de caractere (Array.from), para não partir emoji.
export function trechoDiferente(a, b) {
  const A = Array.from(a);
  const B = Array.from(b);
  const menor = Math.min(A.length, B.length);
  let p = 0;
  while (p < menor && A[p] === B[p]) p++;
  let s = 0;
  while (s < menor - p && A[A.length - 1 - s] === B[B.length - 1 - s]) s++;
  return { a: { inicio: p, fim: A.length - s }, b: { inicio: p, fim: B.length - s } };
}

// Janela visível de um valor longo, centrada no início do trecho diferente.
export function janela(texto, inicio = 0, largura = LARGURA_VALOR) {
  const total = Array.from(texto).length;
  if (total <= largura) return { inicio: 0, fim: total };
  const ini = Math.max(0, Math.min(inicio - Math.floor(largura / 2), total - largura));
  return { inicio: ini, fim: ini + largura };
}

const semAcento = (s) => s.normalize("NFD").replace(/\p{M}/gu, "");
const reaisProximos = (a, b) => Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b));

// No máximo uma dica, na ordem do requisito "Destaque das diferenças e dicas".
export function dica(r) {
  if (!r || r.ok || r.erro || r.funcao !== "igual" || !r.esperado || !r.obtido) return null;
  const { esperado: e, obtido: o } = r;
  if (o.tipo === "sem valor") return "A função terminou sem retorne: o obtido ficou sem valor.";
  if (e.tipo === "inteiro" && o.tipo === "real") return "Em Portugol, / sempre dá real. Para divisão inteira, use piso(a / b).";
  if (e.tipo !== o.tipo) return `O esperado é ${e.tipo} e o obtido é ${o.tipo}.`;
  if (e.tipo === "cadeia" && typeof e.bruto === "string" && typeof o.bruto === "string") {
    const [x, y] = [e.bruto, o.bruto];
    if (x.trim() === y.trim()) return "Sobra ou falta espaço no início ou no fim.";
    if (x.replace(/\s/g, "") === y.replace(/\s/g, "")) return "Diferença só em espaços ou quebras de linha.";
    if (x.toLowerCase() === y.toLowerCase()) return "Diferença só em maiúsculas e minúsculas.";
    if (semAcento(x) === semAcento(y)) return "Diferença só em acentos.";
  }
  if (e.tipo === "real" && typeof e.bruto === "number" && typeof o.bruto === "number" && reaisProximos(e.bruto, o.bruto)) {
    return "Os números diferem só nas últimas casas decimais (arredondamento de real).";
  }
  return null;
}

// --- painel da aba Missão (Rodar) ---

const ESPERADO = { diferente: "diferente de ", maior: "maior que ", menor: "menor que ", contem: "conter " };
const ESPACOS = /([·→↵])/;

let ativo = false;
let iniciarPython = null;
let rodada = null;

export const testesArenaAtivos = () => ativo;

// Troca as funções do plugin `testes` no Pyodide (plugin_testes_arena.py). false = segue o painel do Lab.
export function ativarTestesArena(pyodide, codigoPython, doc = globalThis.document) {
  if (!pyodide || !codigoPython) return false;
  try {
    pyodide.registerJsModule("arena_testes", { registrar: (json) => registrar(json) });
    const globais = pyodide.toPy({ __name__: "arena_plugin_testes" });
    pyodide.runPython(codigoPython, { globals: globais });
    iniciarPython = globais.get("iniciar_rodada");
    rodada = { doc };
    ativo = typeof iniciarPython === "function";
  } catch (erro) {
    console.warn("[arena] plugin de testes da Arena indisponível; usando o painel do Lab", erro);
    ativo = false;
  }
  return ativo;
}

export function iniciarRodada(pyodide, testes, doc = globalThis.document) {
  if (!ativo) return;
  const linhas = linhasDeTeste(testes);
  rodada = { doc, linhas, entradas: linhas.map(entradaDaLinha), resultados: linhas.map(() => null), concluida: false };
  iniciarPython(linhas.length);
  for (const nome of ["codigo_retorno", "gerou_py"]) {
    try { if (pyodide.globals.has(nome)) pyodide.globals.delete(nome); } catch { /* globais do Lab ausentes */ }
  }
  container(doc)?.replaceChildren();
}

export function registrar(json) {
  if (!rodada?.linhas) return;
  const r = JSON.parse(json);
  if (!(r.k >= 0 && r.k < rodada.linhas.length)) return;
  rodada.resultados[r.k] = r;
  desenhar();
}

// Depois do runWasmCode: erro de compilação deixa a área vazia; senão, o que não rodou vira "não executado".
export function concluirRodada(pyodide) {
  if (!ativo || !rodada?.linhas) return;
  const compilou = pyodide.globals.get("codigo_retorno") === 0 && pyodide.globals.get("gerou_py") === true;
  if (!compilou) {
    container(rodada.doc)?.replaceChildren();
    return;
  }
  rodada.concluida = true;
  desenhar();
}

const container = (doc) => doc?.getElementById("test-results");

function el(doc, tag, classe, texto) {
  const e = doc.createElement(tag);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

function desenhar() {
  const { doc, linhas, resultados, concluida } = rodada;
  const alvo = container(doc);
  if (!alvo || linhas.length === 0) return;
  let resumo = alvo.querySelector(".arena-testes-resumo");
  let lista = alvo.querySelector(".arena-testes-lista");
  if (!resumo || !lista) {
    resumo = el(doc, "p", "arena-testes-resumo");
    resumo.setAttribute("aria-live", "polite");
    lista = el(doc, "div", "arena-testes-lista");
    alvo.replaceChildren(resumo, lista);
  }
  const aprovados = resultados.filter((r) => r?.ok).length;
  resumo.textContent = `${aprovados} de ${linhas.length} exemplos aprovados`;
  const cartoes = [];
  resultados.forEach((r, k) => {
    if (r) cartoes.push(cartao(doc, k, r));
    else if (concluida) cartoes.push(cartaoPendente(doc, k));
  });
  lista.replaceChildren(...cartoes);
}

function cabecalho(doc, rotulo, estado, entrada) {
  const c = el(doc, "div", "arena-teste-cabecalho");
  c.append(el(doc, "span", "arena-teste-estado", estado), el(doc, "strong", "arena-teste-rotulo", rotulo));
  const e = el(doc, "span", "arena-teste-entrada", "entrada: ");
  e.append(el(doc, "code", null, entrada));
  c.append(e);
  return c;
}

function cartaoPendente(doc, k) {
  const div = el(doc, "div", "test-item arena-teste pendente");
  div.append(cabecalho(doc, `Exemplo ${k + 1}`, "⏸ não executado", rodada.entradas[k]),
    el(doc, "p", "arena-teste-nota", "O programa parou antes de concluir este teste (veja o terminal)."));
  return div;
}

function cartao(doc, k, r) {
  const div = el(doc, "div", `test-item arena-teste ${r.ok ? "success" : "fail"}`);
  div.append(cabecalho(doc, r.mensagem || `Exemplo ${k + 1}`, r.ok ? "✅ aprovado" : "❌ reprovado", rodada.entradas[k]));
  if (r.ok) return div;

  if (r.erro === "comparar") {
    div.append(el(doc, "p", "arena-teste-dica", `Não dá para comparar ${r.obtido.tipo} com ${r.esperado.tipo}.`));
  }
  const comDestaque = r.funcao === "igual" && !r.erro;
  const tiposDiferentes = comDestaque && r.esperado.tipo !== r.obtido.tipo;
  let d = comDestaque && !tiposDiferentes ? trechoDiferente(r.esperado.texto, r.obtido.texto) : null;
  if (d && d.a.inicio === d.a.fim && d.b.inicio === d.b.fim) d = null; // mesmo texto (ex.: "·" literal × espaço)
  const lados = el(doc, "div", "arena-teste-lados");
  lados.append(
    lado(doc, "Esperado", ESPERADO[r.funcao] || "", r.esperado, d?.a, tiposDiferentes),
    lado(doc, "Obtido", "", r.obtido, d?.b, tiposDiferentes),
  );
  div.append(lados);
  const texto = dica(r);
  if (texto) div.append(el(doc, "p", "arena-teste-dica", texto));
  return div;
}

function lado(doc, titulo, prefixo, v, faixa, destacarTipo) {
  const div = el(doc, "div", "arena-teste-lado");
  const topo = el(doc, "div", "arena-teste-titulo", titulo + " ");
  if (v.tipo !== "sem valor") {
    const t = el(doc, destacarTipo ? "mark" : "span", "arena-teste-tipo", v.tipo);
    topo.append(t);
  }
  const valor = el(doc, "code", "arena-teste-valor");
  if (prefixo) valor.append(el(doc, "span", "arena-teste-prefixo", prefixo));
  const chars = Array.from(v.texto);
  const j = janela(v.texto, faixa ? faixa.inicio : 0);
  const pedaco = (a, b) => chars.slice(Math.max(a, j.inicio), Math.min(b, j.fim)).join("");
  if (j.inicio > 0) valor.append("…");
  if (faixa) {
    comEspacos(doc, valor, pedaco(j.inicio, faixa.inicio));
    const m = el(doc, "mark", faixa.inicio === faixa.fim ? "arena-teste-falta" : null, pedaco(faixa.inicio, faixa.fim));
    if (faixa.inicio === faixa.fim) m.title = "falta algo aqui";
    valor.append(m);
    comEspacos(doc, valor, pedaco(faixa.fim, j.fim));
  } else {
    comEspacos(doc, valor, pedaco(j.inicio, j.fim));
  }
  if (j.fim < chars.length) valor.append("…");
  div.append(topo, valor);
  return div;
}

// Marcadores de espaço (· → ↵) discretos fora do destaque.
function comEspacos(doc, pai, texto) {
  for (const parte of texto.split(ESPACOS)) {
    if (!parte) continue;
    pai.append(ESPACOS.test(parte) ? el(doc, "span", "arena-teste-espaco", parte) : parte);
  }
}
