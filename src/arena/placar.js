// Placar para o telão. Sem código/solução de ninguém: só o estado de cada módulo
// (● completo, ◐ aceito parcial, ○ sem submissão aceita), pontos, completos e caracteres.
// Admin: /placar.html?admin=TOKEN mostra o placar real (sem freeze) e as submissões.
import { api, escapar, formatarRelogio } from "./api.js";

const $ = (id) => document.getElementById(id);
const admin = new URLSearchParams(location.search).get("admin");
let janela = null;
let deslocamento = 0;

const SIMBOLO = { completo: '<span class="bolas">●</span>', parcial: '<span class="meias">◐</span>' };

function bolinhas(estados) {
  if (!estados || !estados.length) return "–";
  return estados.map((e) => SIMBOLO[e] || '<span class="vazias">○</span>').join("");
}

const fracao = (b) => (b && b.total ? `${b.aprovados}/${b.total}` : "–");

async function atualizar() {
  let p;
  try { p = await api.placar(admin); } catch { return; }
  janela = p.janela;
  deslocamento = p.janela.agora - Date.now() / 1000;
  $("evento").textContent = p.evento;
  $("faixa-freeze").classList.toggle("hidden", !p.congelado);
  $("linhas").innerHTML = p.linhas.map((l) => `
    <tr>
      <td class="pos">${l.posicao}</td>
      <td class="nome">${escapar(l.nome)}</td>
      ${["Bronze", "Silver", "Gold", "Extra"].map((n) => `<td class="modulos">${bolinhas(l.modulos[n])}</td>`).join("")}
      <td class="pts">${l.pontos}</td>
      <td class="num">${l.completos}</td>
      <td class="num">${l.completos ? l.caracteres : "–"}</td>
    </tr>`).join("");

  if (p.submissoes) {
    $("admin").classList.remove("hidden");
    $("subs").innerHTML = p.submissoes.map((s) => `
      <tr class="${s.status === "aceito" && s.completo ? "ok" : ""}">
        <td>${new Date(s.t * 1000).toLocaleTimeString("pt-BR")}</td>
        <td>${escapar(s.nome)}</td><td>${escapar(s.codigo)}</td><td>${s.tentativa}</td>
        <td>${escapar(s.status)}${s.completo ? " ✅" : ""}</td>
        <td>${fracao(s.exemplos)}</td><td>${fracao(s.extras)}</td>
        <td>${s.pontos ?? "–"}</td><td>${s.caracteres ?? "–"}</td>
        <td>${escapar((s.participantes || []).join(", "))}</td>
      </tr>`).join("");
  }
}

function relogio() {
  if (!janela) return;
  const agora = Date.now() / 1000 + deslocamento;
  let v, r = "restante";
  if (janela.ensaio) { v = "ENSAIO"; r = ""; }
  else if (agora < janela.inicio) { v = formatarRelogio(janela.inicio - agora); r = "para abrir"; }
  else if (agora <= janela.fim) v = formatarRelogio(janela.fim - agora);
  else { v = "FIM"; r = "submissões encerradas"; }
  $("relogio").textContent = v;
  $("relogio-rotulo").textContent = r;
}

atualizar();
setInterval(atualizar, 15000);
setInterval(relogio, 1000);
