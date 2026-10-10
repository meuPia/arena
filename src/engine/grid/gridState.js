export class GridState {
    constructor(width, height) {
        this.width = width;
        this.height = height;
        
        this.cells = [];
        for (let y = 0; y < height; y++) {
            let row = [];
            for (let x = 0; x < width; x++) {
                row.push({ 
                    x: x, 
                    y: y, 
                    type: 'free',  
                    visitedAt: null 
                });
            }
            this.cells.push(row);
        }

        this.startPos = { x: 0, y: 0 };
        this.goalPos = { x: width - 1, y: height - 1 };
        this.timeline = [];
        this.currentStepIndex = 0;
    }

    getCell(x, y) {
        if (x < 0 || x >= this.width || y < 0 || y >= this.height) {
            return null;
        }
        return this.cells[y][x];
    }

    setCellType(x, y, type) {
        const cell = this.getCell(x, y);
        if (cell) {
            cell.type = type;
        }
    }

    addFrame(frame) {
        this.timeline.push(frame);
    }

    getCurrentFrame() {
        if (this.timeline.length === 0) return null;
        return this.timeline[this.currentStepIndex];
    }

    stepForward() {
        if (this.currentStepIndex < this.timeline.length - 1) {
            this.currentStepIndex++;
        }
    }

    stepBackward() {
        if (this.currentStepIndex > 0) {
            this.currentStepIndex--;
        }
    }
}