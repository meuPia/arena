// Ajuda da IDE: o cartão do dialeto (docs/cartao-dialeto.md) num modal, com busca por palavra.
// A parte de cima é pura (testada em ajuda.test.js); setupAjuda liga o botão e o modal.
import { marked } from "marked";

export function htmlAjuda(markdown) {
  return marked.parse(markdown);
}

// Normaliza caractere a caractere (sem acento, minúsculo) e guarda de onde veio cada letra normalizada.
function normalizarComMapa(s) {
  let texto = "";
  const origem = [];
  for (let i = 0; i < s.length; i++) {
    const n = s[i].normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
    for (const c of n) { texto += c; origem.push(i); }
  }
  return { texto, origem };
}

export function normalizar(s) {
  return normalizarComMapa(s).texto;
}

export function termosDaConsulta(consulta) {
  return normalizar(consulta || "").split(/\s+/).filter(Boolean);
}

// Posições (na palavra normalizada) das letras do termo: o pedaço contíguo quando existe, senão a primeira
// subsequência. null quando o termo não cabe na palavra.
function casarNaPalavra(termo, palavra) {
  const i = palavra.indexOf(termo);
  if (i >= 0) return [...termo].map((_, k) => i + k);
  const pos = [];
  let j = 0;
  for (const c of termo) {
    while (j < palavra.length && palavra[j] !== c) j++;
    if (j === palavra.length) return null;
    pos.push(j++);
  }
  return pos;
}

const PALAVRA = /[\p{L}\p{N}_]+/gu;

// Trechos [início, fim) do texto original a destacar: as letras de cada palavra que casa com algum termo.
export function destaques(texto, termos) {
  if (!termos.length) return [];
  const { texto: norm, origem } = normalizarComMapa(texto);
  const marcadas = new Set();
  for (const m of norm.matchAll(PALAVRA)) {
    for (const termo of termos) {
      const pos = casarNaPalavra(termo, m[0]);
      if (pos) for (const p of pos) marcadas.add(origem[m.index + p]);
    }
  }
  const faixas = [];
  for (const i of [...marcadas].sort((a, b) => a - b)) {
    const ultima = faixas[faixas.length - 1];
    if (ultima && ultima[1] === i) ultima[1] = i + 1;
    else faixas.push([i, i + 1]);
  }
  return faixas;
}

function casaTodos(texto, termos) {
  const palavras = normalizar(texto).match(PALAVRA) || [];
  return termos.every((t) => palavras.some((p) => casarNaPalavra(t, p)));
}

function textoPuro(tokens) {
  return (tokens || []).map((t) => (t.tokens ? textoPuro(t.tokens) : t.text ?? "")).join("");
}

// Trechos do cartão, na ordem: títulos, linhas de tabela (com o cabeçalho), itens de lista, parágrafos e
// blocos de código. `nivel` só existe nos títulos e diz até onde vai a seção deles.
export function indiceAjuda(markdown) {
  const trechos = [];
  const caminho = [];
  // O # do topo só rotula a introdução; dentro das seções, o rótulo é "## › ###".
  const secao = () => (caminho.length > 1 ? caminho.slice(1) : caminho).filter(Boolean).join(" › ");
  for (const tok of marked.lexer(markdown)) {
    if (tok.type === "heading") {
      caminho.length = tok.depth - 1;
      caminho[tok.depth - 1] = tok.text;
      trechos.push({ secao: secao(), tipo: "titulo", nivel: tok.depth, texto: textoPuro(tok.tokens), markdown: tok.raw });
    } else if (tok.type === "table") {
      const [cabecalho, alinhamento, ...linhas] = tok.raw.split("\n").filter((l) => l.trim());
      tok.rows.forEach((celulas, i) => trechos.push({
        secao: secao(), tipo: "linha",
        texto: celulas.map((c) => textoPuro(c.tokens)).join(" "),
        markdown: `${cabecalho}\n${alinhamento}\n${linhas[i]}\n`,
      }));
    } else if (tok.type === "list") {
      for (const item of tok.items) {
        trechos.push({ secao: secao(), tipo: "item", texto: textoPuro(item.tokens), markdown: item.raw.trimEnd() + "\n" });
      }
    } else if (tok.type === "code") {
      trechos.push({ secao: secao(), tipo: "codigo", texto: tok.text, markdown: tok.raw });
    } else if (tok.type === "paragraph" || tok.type === "blockquote") {
      trechos.push({ secao: secao(), tipo: "paragrafo", texto: textoPuro(tok.tokens), markdown: tok.raw });
    }
  }
  return trechos;
}

// null = consulta vazia (mostrar o cartão inteiro). Senão, os trechos que casam, na ordem do cartão; um
// título que casa traz a seção inteira (até o próximo título do mesmo nível ou acima).
export function buscar(indice, consulta) {
  const termos = termosDaConsulta(consulta);
  if (!termos.length) return null;
  const escolhidos = new Set();
  for (let i = 0; i < indice.length; i++) {
    const t = indice[i];
    if (!casaTodos(t.texto, termos)) continue;
    escolhidos.add(i);
    if (t.tipo !== "titulo") continue;
    for (let j = i + 1; j < indice.length && !(indice[j].tipo === "titulo" && indice[j].nivel <= t.nivel); j++) {
      escolhidos.add(j);
    }
  }
  return [...escolhidos].sort((a, b) => a - b).map((i) => indice[i]);
}

// ---------- DOM ----------

function marcarTexto(raiz, termos) {
  const walker = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
  const nos = [];
  while (walker.nextNode()) nos.push(walker.currentNode);
  for (const no of nos) {
    const faixas = destaques(no.data, termos);
    if (!faixas.length) continue;
    const frag = document.createDocumentFragment();
    let pos = 0;
    for (const [ini, fim] of faixas) {
      if (ini > pos) frag.append(no.data.slice(pos, ini));
      const mark = document.createElement("mark");
      mark.textContent = no.data.slice(ini, fim);
      frag.append(mark);
      pos = fim;
    }
    if (pos < no.data.length) frag.append(no.data.slice(pos));
    no.replaceWith(frag);
  }
}

export function setupAjuda(view, markdown) {
  const modal = document.getElementById("ajuda-modal");
  const corpo = document.getElementById("ajuda-corpo");
  const busca = document.getElementById("ajuda-busca");
  const status = document.getElementById("ajuda-status");
  let completo = null;
  let indice = null;

  function mostrar() {
    const resultado = buscar(indice, busca.value);
    if (resultado === null) {
      corpo.innerHTML = completo;
      status.textContent = "";
      return;
    }
    corpo.replaceChildren();
    if (!resultado.length) {
      const p = document.createElement("p");
      p.className = "arena-ajuda-vazio";
      p.textContent = `Nada encontrado para "${busca.value.trim()}"`;
      corpo.append(p);
      status.textContent = p.textContent;
      return;
    }
    let secaoAtual = null;
    for (const t of resultado) {
      if (t.secao !== secaoAtual) {
        secaoAtual = t.secao;
        const h = document.createElement("h3");
        h.className = "arena-ajuda-secao";
        h.textContent = t.secao;
        corpo.append(h);
      }
      if (t.tipo === "titulo") continue; // o título já aparece no cabeçalho do grupo
      const bloco = document.createElement("div");
      bloco.innerHTML = htmlAjuda(t.markdown);
      corpo.append(...bloco.childNodes);
    }
    marcarTexto(corpo, termosDaConsulta(busca.value));
    const n = resultado.filter((t) => t.tipo !== "titulo").length;
    status.textContent = `${n} ${n === 1 ? "trecho encontrado" : "trechos encontrados"}`;
  }

  function abrir() {
    if (completo === null) {
      completo = htmlAjuda(markdown);
      indice = indiceAjuda(markdown);
    }
    busca.value = "";
    mostrar();
    corpo.scrollTop = 0;
    modal.classList.remove("hidden");
    busca.focus();
  }

  function fechar() {
    modal.classList.add("hidden");
    view.focus();
  }

  document.getElementById("ajuda-btn").addEventListener("click", abrir);
  document.getElementById("close-ajuda-btn").addEventListener("click", fechar);
  modal.addEventListener("click", (ev) => { if (ev.target === modal) fechar(); });
  busca.addEventListener("input", mostrar);
  document.addEventListener("keydown", (ev) => {
    if (ev.key !== "Escape" || modal.classList.contains("hidden")) return;
    ev.preventDefault();
    if (busca.value) {
      busca.value = "";
      mostrar();
      busca.focus();
    } else {
      fechar();
    }
  });
}
