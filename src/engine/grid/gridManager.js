import { GridState } from './gridState.js';
import { GridRenderer } from './gridRenderer.js';

export class GridManager {
    constructor() {
        this.canvas = document.getElementById('grid-canvas');
        if (!this.canvas) return;

        this.renderer = new GridRenderer(this.canvas);
        
        this.state = new GridState(10, 10); 
        this.stepDisplay = document.getElementById('grid-step-display');
        
        this.isPlaying = false;
        this.playInterval = null;
        this.tickRate = 300;

        this.setupControls();
        this.update();
    }

    setupControls() {
        document.getElementById('grid-prev').addEventListener('click', () => {
            this.pause();
            this.state.stepBackward();
            this.update();
        });
        
        document.getElementById('grid-next').addEventListener('click', () => {
            this.pause();
            this.state.stepForward();
            this.update();
        });

        const playBtn = document.getElementById('grid-play');
        if (playBtn) {
            playBtn.addEventListener('click', () => {
                this.togglePlay();
            });
        }

    }

    play() {
        if (this.isPlaying) return;
        this.isPlaying = true;
        
        const playBtn = document.getElementById('grid-play');
        if (playBtn) playBtn.innerHTML = '<i data-lucide="pause"></i>';
        if (window.lucide) window.lucide.createIcons();

        if (this.state.currentStepIndex >= this.state.timeline.length - 1) {
            this.state.currentStepIndex = 0;
            this.update();
        }

        this.playInterval = setInterval(() => {
            if (this.state.currentStepIndex < this.state.timeline.length - 1) {
                this.state.stepForward();
                this.update();
            } else {
                this.pause(); 
            }
        }, this.tickRate);
    }

    pause() {
        if (!this.isPlaying) return;
        this.isPlaying = false;
        clearInterval(this.playInterval);

        const playBtn = document.getElementById('grid-play');
        if (playBtn) playBtn.innerHTML = '<i data-lucide="play"></i>';
        if (window.lucide) window.lucide.createIcons();
    }

    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    update() {
        this.renderer.draw(this.state);
        if (this.stepDisplay) {
            const maxSteps = Math.max(0, this.state.timeline.length - 1);
            this.stepDisplay.textContent = `Passo: ${this.state.currentStepIndex} / ${maxSteps}`;
        }
    }

    iniciarGrid(width, height) {
        this.pause();
        this.state = new GridState(width, height);
        this.update();
    }

    definirParede(x, y) {
        this.state.setCellType(x, y, 'wall');
        this.update();
    }

    visitarCelula(x, y, step) {
        let acao = step >= 9000 ? 'caminho' : 'visitado';
        this.state.addFrame({ action: acao, x: x, y: y, step: step });
        this.update();
    }

    autoPlay() {
        this.state.currentStepIndex = 0; // Garante que começa do início
        this.update();
        this.play();
    }

    reset() {
        this.pause();
        this.state = new GridState(10, 10);
        this.update();
    }

    hasAnimation() {
        return this.state.timeline.length > 0;
    }

    carregarMapaDesafio(mapa) {
        this.pause();
        this.state = new GridState(mapa.largura || 10, mapa.altura || 10);

        if (mapa.inicio) {
            this.state.setCellType(mapa.inicio[0], mapa.inicio[1], 'inicio');
        }
        if (mapa.objetivo) {
            this.state.setCellType(mapa.objetivo[0], mapa.objetivo[1], 'objetivo');
        }

        if (mapa.celulas) {
            mapa.celulas.forEach(c => {
                const cell = this.state.getCell(c.x, c.y);
                if (cell) {
                    Object.assign(cell, c);
                    if (c.tipo) {
                        cell.type = c.tipo;
                    }
                }
            });
        } else if (mapa.paredes) {
            mapa.paredes.forEach(c => this.state.setCellType(c[0], c[1], 'parede'));
        }
        this.update();
    }

    sensorCelula(x, y) {
        const cell = this.state.getCell(x, y);
        if (!cell) {
            return JSON.stringify({ tipo: "fora_limites", passavel: false });
        }
        return JSON.stringify(cell);
    }
}