import { marked } from 'marked'; // Você precisará de: npm install marked

export function renderDesafio(desafio) {
    const container = document.getElementById('test-content');
    const textoMarkdown = desafio.instrucoes || desafio.descricao || "Nenhuma instrução fornecida para este desafio.";
    container.innerHTML = `
        <div class="desafio-header">
            <h2>${desafio.titulo}</h2>
        </div>
        <div class="desafio-instrucoes">
            ${marked.parse(textoMarkdown)}
        </div>
        <div id="test-results" class="test-results-container">
            </div>
    `;
}

export function parseTestLine(line) {
    const resultsContainer = document.getElementById('test-results');
    if (!resultsContainer) return;

    if (line.includes('[TESTE_OK]')) {
        const msg = line.replace('[TESTE_OK] Sucesso: ', '');
        resultsContainer.innerHTML += `<div class="test-item success">✅ ${msg}</div>`;
    } 
    else if (line.includes('[TESTE_FALHA]')) {
        const msg = line.replace('[TESTE_FALHA] Falhou: ', '');
        resultsContainer.innerHTML += `<div class="test-item fail">❌ ${msg}</div>`;
    }
}