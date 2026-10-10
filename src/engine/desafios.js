import { api, sessao, lerRascunho } from "../arena/api.js";

export let desafioAtual = null;

/**
 * Code Arena: lê ?desafio=B01 e busca a missão na API (só vem se o nível estiver liberado).
 * O formato devolvido é o mesmo que o motor do Lab espera (codigoTeste = testes PÚBLICOS).
 * Sem sessão ou sem desafio, volta para o painel.
 */
export async function carregarDesafioDaURL() {
    const codigo = (new URLSearchParams(window.location.search).get("desafio") || "").toUpperCase();

    if (!sessao() || !codigo) {
        window.location.replace("/");
        return false;
    }

    try {
        const m = await api.missao(codigo);
        desafioAtual = {
            ...m,
            id: m.codigo,
            codigoTeste: m.testesPublicos,
            codigoInicial: lerRascunho(m.codigo) || m.codigoInicial,
        };
        return true;
    } catch (erro) {
        alert(erro.message);
        window.location.replace("/");
        return false;
    }
}
