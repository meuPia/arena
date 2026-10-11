// Placar para o telão. Sem código/solução de ninguém: só o estado de cada módulo
// (● completo, ◐ aceito parcial, ○ sem submissão aceita), pontos, completos e caracteres.
// Sempre o placar público (congela no freeze). O placar real e o log ficam em /admin.html.
import { api, escapar, formatarRelogio } from "./api.js";
import { linhasPlacar } from "./placar-tabela.js";

const $ = (id) => document.getElementById(id);
let janela = null;
let deslocamento = 0;

async function atualizar() {
  let p;
  try { p = await api.placar(); } catch { return; }
  janela = p.janela;
  deslocamento = p.janela.agora - Date.now() / 1000;
  // "CODE CHALLENGE — SYSTEM RECOVERY": a parte depois do travessão ganha a cor de destaque.
  const [antes, depois] = String(p.evento).split(/\s+[—-]\s+/, 2);
  $("evento").innerHTML = depois ? `${escapar(antes)} — <span class="destaque">${escapar(depois)}</span>` : escapar(p.evento);
  $("faixa-freeze").classList.toggle("hidden", !p.congelado);
  $("linhas").innerHTML = linhasPlacar(p.linhas);
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
