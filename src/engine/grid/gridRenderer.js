export class GridRenderer {
    constructor(canvasElement) {
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        
        this.colors = {
            livre: '#2d2d2d',      // Fundo escuro (Dark Mode)
            parede: '#607d8b',      // Parede (Cinza Azulado)
            inicio: '#4CAF50',     // Início (Verde)
            objetivo: '#f44336',      // Fim (Vermelho)
            visitado: '#2196F3',     // Explorado (Azul)
            caminho: '#ffeb3b',      // Caminho Final (Amarelo)
            linha: '#404040',  // Linha de grade
            agente: '#ffffff',      // Agente (Bolinha Branca)
            moeda: '#ffc107',
            acido: '#9c27b0'
        };
    }

    draw(state) {
        if (!state) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const cellWidth = this.canvas.width / state.width;
        const cellHeight = this.canvas.height / state.height;

        for (let y = 0; y < state.height; y++) {
            for (let x = 0; x < state.width; x++) {
                const cell = state.getCell(x, y);
                this.drawCell(x, y, cellWidth, cellHeight, this.colors[cell.type] || this.colors.livre);
            }
        }

        for (let i = 0; i <= state.currentStepIndex; i++) {
            const frame = state.timeline[i];
            if (frame) {
                if (frame.action === 'visitado' || frame.action === 'caminho') {
                    this.drawCell(frame.x, frame.y, cellWidth, cellHeight, this.colors[frame.action]);
                }
            }
        }

        const currentFrame = state.getCurrentFrame();
        if (currentFrame && currentFrame.x !== undefined && currentFrame.y !== undefined) {
            this.drawAgent(currentFrame.x, currentFrame.y, cellWidth, cellHeight);
        }
    }

    drawCell(x, y, w, h, color) {
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x * w, y * h, w, h);
        
        this.ctx.strokeStyle = this.colors.linha;
        this.ctx.strokeRect(x * w, y * h, w, h);
    }

    drawAgent(x, y, w, h) {
        this.ctx.fillStyle = this.colors.agente;
        this.ctx.beginPath();
        this.ctx.arc((x * w) + (w / 2), (y * h) + (h / 2), Math.min(w, h) * 0.3, 0, Math.PI * 2);
        this.ctx.fill();
    }
}