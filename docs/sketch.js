// ============================================
// Concurrencia y Sincronizacion
// Simulacion Visual con Trafico Urbano
// p5.js (Web Version)
// ============================================
// Teclas: 1-7 modos, SPACE reiniciar
// UP/DOWN permisos (semaforo)
// ENTER toggle proteccion (seccion critica)
// ============================================

const SCENE_X = 5;
const SCENE_Y = 45;
const SCENE_W = 840;
const SCENE_H = 550;
const PANEL_X = 855;
const PANEL_W = 340;

const MODE_NAMES = [
    "SEMAFORO", "MUTEX", "MONITOR", "SECCION CRITICA",
    "CONDICION DE CARRERA", "DEADLOCK", "CONCURRENCIA"
];
const MODE_FILES = [
    "semaforo.png", "mutex.png", "monitor.png", "seccion_critica.png",
    "condicion_carrera.png", "deadlock.png", "concurrencia.png"
];
const MODE_DESCS = [
    "Contador que permite o bloquea\nel paso de hilos (carros).\nN permisos = N carros cruzan.",
    "Solo UN hilo puede acceder\nal recurso (puente) a la vez.\nLock/Unlock controlan acceso.",
    "Recurso con sincronizacion\nautomatica interna. La caseta\ngestiona sin coordinacion externa.",
    "Zona donde solo entra un hilo.\nENTER: toggle proteccion.\nSin proteccion = error.",
    "Dos hilos acceden sin control\nal mismo recurso. Resultado\nimpredecible: colision!",
    "Dos hilos bloqueados esperando\nrecursos mutuamente.\nBloqueo eterno.",
    "Multiples hilos ejecutandose\nen paralelo, cada uno en su\npropio carril."
];
const MODE_CONTROLS = [
    "UP/DOWN: Cambiar permisos",
    "",
    "",
    "ENTER: Toggle proteccion",
    "",
    "",
    ""
];
const ANALOGIAS = [
    "Semaforo de transito con contador.\nN permisos = N carros pasan.\nEl resto espera luz verde.",
    "Puente de un solo carril.\nUn carro cruza, barrera baja.\nAl salir, barrera sube.",
    "Caseta de peaje automatica.\nLa caseta decide quien pasa.\nCarros no se coordinan entre si.",
    "Zona de peligro (rayas amarillas).\nCon proteccion: 1 carro a la vez.\nSin proteccion: chocan.",
    "Dos carros al mismo cruce\nsin semaforo. Ambos aceleran.\nResultado: colision.",
    "Carro A tiene puente H, necesita V.\nCarro B tiene puente V, necesita H.\nNinguno cede: bloqueo eterno.",
    "Autopista de 6 carriles.\nCada carro avanza independiente.\nEjecucion simultanea."
];

const RED = [220, 50, 50];
const BLUE = [50, 120, 220];
const GREEN = [50, 200, 80];
const YELLOW = [240, 180, 30];
const PURPLE = [180, 50, 220];
const ORANGE = [255, 130, 50];
const CYAN = [50, 210, 210];
const PINK = [220, 80, 160];
const ALL_COLORS = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, PINK];

function sx(p) { return Math.round(SCENE_X + SCENE_W * p); }
function sy(p) { return Math.round(SCENE_Y + SCENE_H * p); }

// ========== CAR CLASS ==========
class Car {
    constructor(x, y, col, label) {
        this.x = x;
        this.y = y;
        this.tx = x;
        this.ty = y;
        this.col = col;
        this.label = label;
        this.spd = 2.5;
        this.vis = true;
        this.hl = false;
        this.state = "";
        this.ang = 0;
        // Extra properties set by modes
        this.laneY = y;
        this.side = "L";
        this.waitX = 0;
        this.exitX = 0;
    }

    go(tx, ty) {
        this.tx = tx;
        this.ty = ty;
    }

    step() {
        let dx = this.tx - this.x;
        let dy = this.ty - this.y;
        let d = Math.sqrt(dx * dx + dy * dy);
        if (d < this.spd) {
            this.x = this.tx;
            this.y = this.ty;
            return true;
        }
        this.ang = atan2(dy, dx);
        this.x += dx / d * this.spd;
        this.y += dy / d * this.spd;
        return false;
    }

    at() {
        return Math.abs(this.x - this.tx) < 2 && Math.abs(this.y - this.ty) < 2;
    }

    show() {
        if (!this.vis) return;

        push();
        translate(this.x, this.y);
        rotate(this.ang);

        // Shadow
        noStroke();
        fill(0, 0, 0, 55);
        rect(-19, -10, 42, 24, 5);

        // Main body
        if (this.hl) {
            stroke(255, 255, 0);
            strokeWeight(3);
        } else {
            stroke(25);
            strokeWeight(1);
        }
        fill(this.col[0], this.col[1], this.col[2]);
        rect(-21, -12, 42, 24, 5);

        // Roof / cabin
        noStroke();
        let r2 = max(this.col[0] - 40, 0);
        let g2 = max(this.col[1] - 40, 0);
        let b2 = max(this.col[2] - 40, 0);
        fill(r2, g2, b2);
        rect(-8, -8, 20, 16, 3);

        // Windshield
        fill(180, 220, 255, 200);
        rect(10, -8, 7, 16, 2);

        // Rear window
        fill(160, 200, 240, 150);
        rect(-17, -7, 6, 14, 2);

        // Wheels
        fill(35);
        noStroke();
        rect(-17, -15, 10, 4, 2);
        rect(-17, 11, 10, 4, 2);
        rect(8, -15, 10, 4, 2);
        rect(8, 11, 10, 4, 2);

        // Headlights
        fill(255, 255, 200, 220);
        rect(19, -9, 3, 5, 1);
        rect(19, 4, 3, 5, 1);

        // Taillights
        fill(255, 50, 50, 200);
        rect(-21, -9, 3, 4, 1);
        rect(-21, 5, 3, 4, 1);

        // Label
        fill(255);
        textSize(9);
        textAlign(CENTER, CENTER);
        text(this.label, 0, 0);
        textAlign(LEFT, BASELINE);

        pop();

        // Highlight glow
        if (this.hl) {
            noStroke();
            fill(255, 255, 0, 25 + sin(frameCount * 0.15) * 15);
            ellipse(this.x, this.y, 50, 50);
        }
    }
}

// ========== GLOBAL STATE ==========
let currentMode = 0;
let images = [];
let modeInfo = "";

// Semaforo
let semCars = [];
let semMax = 3;
let semAvail = 3;

// Mutex
let mutCars = [];
let mutLocked = false;
let mutOwner = null;

// Monitor
let monCars = [];
let monBusy = false;
let monActive = null;

// Seccion Critica
let secCars = [];
let secProtected = true;
let secFlash = 0;

// Condicion de Carrera
let raceCars = [];
let racePhase = "run";
let raceTimer = 0;
let raceCrashX = 0;
let raceCrashY = 0;

// Deadlock
let deadCars = [];
let deadPhase = "move";
let deadTimer = 0;

// Concurrencia
let concCars = [];

// ========== PRELOAD ==========
function preload() {
    for (let i = 0; i < MODE_FILES.length; i++) {
        images[i] = loadImage("data/" + MODE_FILES[i]);
    }
}

// ========== SETUP ==========
function setup() {
    createCanvas(1200, 700);
    textFont("monospace");
    initMode(0);
}

// ========== MAIN DRAW ==========
function draw() {
    background(35, 40, 50);

    // Title bar
    noStroke();
    fill(30, 33, 42);
    rect(0, 0, width, 40);
    fill(255, 220, 100);
    textSize(16);
    textAlign(LEFT, BASELINE);
    text("Concurrencia y Sincronizacion - Trafico Urbano", 15, 27);

    // Scene background
    if (images[currentMode]) {
        image(images[currentMode], SCENE_X, SCENE_Y, SCENE_W, SCENE_H);
    } else {
        fill(50);
        noStroke();
        rect(SCENE_X, SCENE_Y, SCENE_W, SCENE_H);
    }

    // Scene border
    noFill();
    stroke(70, 90, 120);
    strokeWeight(1);
    rect(SCENE_X, SCENE_Y, SCENE_W, SCENE_H);

    // Mode-specific update + draw
    if (currentMode === 0) updateSemaforo();
    else if (currentMode === 1) updateMutex();
    else if (currentMode === 2) updateMonitor();
    else if (currentMode === 3) updateSeccionCritica();
    else if (currentMode === 4) updateCondicionCarrera();
    else if (currentMode === 5) updateDeadlock();
    else if (currentMode === 6) updateConcurrencia();

    // Panel
    drawPanel();
}

// ========== PANEL ==========
function drawPanel() {
    noStroke();
    fill(40, 44, 55);
    rect(PANEL_X, 0, PANEL_W, height);

    let px = PANEL_X + 15;
    let py = 15;

    // Mode tabs
    for (let i = 0; i < 7; i++) {
        let bx = px + i * 46;
        fill(i === currentMode ? color(255, 220, 100) : color(60, 65, 80));
        noStroke();
        rect(bx, py, 42, 22, 4);
        fill(i === currentMode ? 30 : 140);
        textSize(11);
        textAlign(CENTER, CENTER);
        text(String(i + 1), bx + 21, py + 11);
    }
    textAlign(LEFT, BASELINE);
    py += 35;

    // Mode name
    fill(255, 220, 100);
    textSize(15);
    text(MODE_NAMES[currentMode], px, py);
    py += 22;

    // Description
    fill(170, 190, 210);
    textSize(11);
    let descLines = MODE_DESCS[currentMode].split("\n");
    for (let ln of descLines) {
        text(ln, px, py);
        py += 15;
    }
    py += 10;

    // Separator
    stroke(70, 80, 100);
    line(px, py, px + PANEL_W - 30, py);
    noStroke();
    py += 12;

    // Mode info
    fill(200, 220, 240);
    textSize(12);
    let infoLines = modeInfo.split("\n");
    for (let ln of infoLines) {
        text(ln, px, py);
        py += 16;
    }
    py += 15;

    // Separator
    stroke(70, 80, 100);
    line(px, py, px + PANEL_W - 30, py);
    noStroke();
    py += 12;

    // Analogia
    fill(255, 200, 100);
    textSize(12);
    text("Analogia:", px, py);
    py += 18;
    fill(160, 180, 200);
    textSize(11);
    let analogLines = ANALOGIAS[currentMode].split("\n");
    for (let ln of analogLines) {
        text(ln, px, py);
        py += 14;
    }
    py += 15;

    // Controls
    stroke(70, 80, 100);
    line(px, py, px + PANEL_W - 30, py);
    noStroke();
    py += 12;
    fill(120, 140, 170);
    textSize(11);
    text("Controles:", px, py);
    py += 16;
    text("1-7: Cambiar modo", px, py);
    py += 14;
    text("SPACE: Reiniciar demo", px, py);
    py += 14;
    if (MODE_CONTROLS[currentMode]) {
        fill(255, 200, 100);
        text(MODE_CONTROLS[currentMode], px, py);
    }
    py += 20;

    // Bottom label
    fill(80, 90, 110);
    textSize(10);
    text("Hilos=Carros | Recursos=Intersecciones/Puentes", px, height - 15);
}

// ==============================================
// MODE 0: SEMAFORO
// ==============================================
function initSemaforo() {
    semAvail = semMax;
    semCars = [];
    let lanes = [sy(0.38), sy(0.47), sy(0.56)];
    for (let i = 0; i < 5; i++) {
        let ly = lanes[i % 3];
        let c = new Car(sx(-0.06 - i * 0.13), ly, ALL_COLORS[i], "H" + (i + 1));
        c.state = "drive";
        c.spd = 2.2;
        c.laneY = ly;
        c.go(sx(0.28), ly);
        semCars.push(c);
    }
}

function updateSemaforo() {
    for (let c of semCars) c.step();

    for (let c of semCars) {
        if (c.state === "drive" && c.at()) {
            c.state = "wait";
        } else if (c.state === "wait") {
            if (semAvail > 0) {
                semAvail--;
                c.state = "cross";
                c.hl = true;
                c.go(sx(0.72), c.laneY);
            }
        } else if (c.state === "cross" && c.at()) {
            semAvail++;
            c.hl = false;
            c.state = "exit";
            c.go(sx(1.08), c.laneY);
        } else if (c.state === "exit" && c.at()) {
            c.x = sx(-0.08 - random(0.02, 0.15));
            c.y = c.laneY;
            c.state = "drive";
            c.go(sx(0.28), c.laneY);
        }
    }

    // Reposition waiting cars in queue
    let laneYs = [sy(0.38), sy(0.47), sy(0.56)];
    for (let lyVal of laneYs) {
        let waiting = semCars.filter(c => c.state === "wait" && Math.abs(c.laneY - lyVal) < 5);
        waiting.forEach((c, i) => {
            let qx = sx(0.28) - i * 52;
            c.go(qx, c.laneY);
        });
    }

    // Draw counter overlay
    noStroke();
    fill(0, 0, 0, 180);
    rect(sx(0.42), sy(0.08), 70, 36, 8);
    textSize(22);
    textAlign(CENTER, CENTER);
    fill(semAvail > 0 ? color(80, 255, 120) : color(255, 80, 80));
    text(semAvail + "/" + semMax, sx(0.42) + 35, sy(0.08) + 18);
    textAlign(LEFT, BASELINE);

    // Traffic light indicator
    noStroke();
    fill(0, 0, 0, 150);
    rect(sx(0.30), sy(0.15), 18, 42, 4);
    if (semAvail > 0) {
        fill(50, 80, 50);
        ellipse(sx(0.30) + 9, sy(0.15) + 9, 12, 12);
        fill(80, 255, 80);
        ellipse(sx(0.30) + 9, sy(0.15) + 33, 12, 12);
    } else {
        fill(255, 80, 80);
        ellipse(sx(0.30) + 9, sy(0.15) + 9, 12, 12);
        fill(50, 50, 50);
        ellipse(sx(0.30) + 9, sy(0.15) + 33, 12, 12);
    }

    for (let c of semCars) c.show();

    let inCross = semCars.filter(c => c.state === "cross").length;
    let waitingN = semCars.filter(c => c.state === "wait").length;
    modeInfo = `Permisos: ${semAvail}/${semMax}\nEn interseccion: ${inCross}\nEsperando: ${waitingN}`;
}

// ==============================================
// MODE 1: MUTEX
// ==============================================
function initMutex() {
    mutLocked = false;
    mutOwner = null;
    mutCars = [];

    let configs = [
        { x: sx(0.05), y: sy(0.44), col: RED, lbl: "H1", side: "L" },
        { x: sx(-0.08), y: sy(0.58), col: BLUE, lbl: "H2", side: "L" },
        { x: sx(0.95), y: sy(0.44), col: GREEN, lbl: "H3", side: "R" },
        { x: sx(1.08), y: sy(0.58), col: YELLOW, lbl: "H4", side: "R" }
    ];

    for (let cfg of configs) {
        let c = new Car(cfg.x, cfg.y, cfg.col, cfg.lbl);
        c.state = "approach";
        c.spd = 2.0;
        c.side = cfg.side;
        c.waitX = cfg.side === "L" ? sx(0.26) : sx(0.74);
        c.exitX = cfg.side === "L" ? sx(1.08) : sx(-0.08);
        c.go(c.waitX, c.y);
        mutCars.push(c);
    }
}

function updateMutex() {
    for (let c of mutCars) c.step();

    for (let c of mutCars) {
        if (c.state === "approach" && c.at()) {
            c.state = "wait";
        } else if (c.state === "wait" && !mutLocked) {
            mutLocked = true;
            mutOwner = c;
            c.state = "bridge";
            c.hl = true;
            c.go(sx(0.50), sy(0.50));
        } else if (c.state === "bridge" && c.at()) {
            c.state = "exit";
            c.go(c.exitX, c.y);
            c.hl = false;
            mutLocked = false;
            mutOwner = null;
        } else if (c.state === "exit" && c.at()) {
            if (c.side === "L") {
                c.x = sx(-0.08 - random(0, 0.1));
            } else {
                c.x = sx(1.08 + random(0, 0.1));
            }
            c.state = "approach";
            c.go(c.waitX, c.y);
        }
    }

    // Queue waiting cars
    for (let side of ["L", "R"]) {
        let waiting = mutCars.filter(c => c.state === "wait" && c.side === side);
        waiting.forEach((c, i) => {
            if (side === "L") {
                c.go(c.waitX - i * 52, c.y);
            } else {
                c.go(c.waitX + i * 52, c.y);
            }
        });
    }

    // Lock indicator
    noStroke();
    fill(0, 0, 0, 180);
    rect(sx(0.45), sy(0.18), 80, 30, 6);
    textSize(14);
    textAlign(CENTER, CENTER);
    fill(mutLocked ? color(255, 80, 80) : color(80, 255, 120));
    text(mutLocked ? "LOCKED" : "UNLOCKED", sx(0.45) + 40, sy(0.18) + 15);
    textAlign(LEFT, BASELINE);

    // Barrier lines
    strokeWeight(3);
    if (mutLocked) {
        stroke(255, 100, 50);
        line(sx(0.32), sy(0.38), sx(0.32), sy(0.62));
        line(sx(0.68), sy(0.38), sx(0.68), sy(0.62));
    } else {
        stroke(80, 255, 80, 150);
        line(sx(0.32), sy(0.38), sx(0.32), sy(0.42));
        line(sx(0.68), sy(0.38), sx(0.68), sy(0.42));
    }

    for (let c of mutCars) c.show();

    let ownerStr = mutOwner ? mutOwner.label : "Ninguno";
    let waitN = mutCars.filter(c => c.state === "wait").length;
    modeInfo = `Estado: ${mutLocked ? "LOCKED" : "UNLOCKED"}\nDueno: ${ownerStr}\nEsperando: ${waitN}`;
}

// ==============================================
// MODE 2: MONITOR
// ==============================================
function initMonitor() {
    monBusy = false;
    monActive = null;
    monCars = [];
    let cols = [RED, BLUE, GREEN, PURPLE];
    for (let i = 0; i < 4; i++) {
        let ly = i % 2 === 0 ? sy(0.42) : sy(0.58);
        let c = new Car(sx(-0.05 - i * 0.12), ly, cols[i], "H" + (i + 1));
        c.state = "drive";
        c.spd = 2.0;
        c.laneY = ly;
        c.go(sx(0.32), ly);
        monCars.push(c);
    }
}

function updateMonitor() {
    for (let c of monCars) c.step();

    for (let c of monCars) {
        if (c.state === "drive" && c.at()) {
            c.state = "wait";
        } else if (c.state === "wait" && !monBusy) {
            monBusy = true;
            monActive = c;
            c.state = "process";
            c.hl = true;
            c.go(sx(0.50), sy(0.50));
        } else if (c.state === "process" && c.at()) {
            c.state = "done";
            c.go(sx(1.08), c.laneY);
            c.hl = false;
            monBusy = false;
            monActive = null;
        } else if (c.state === "done" && c.at()) {
            c.x = sx(-0.08 - random(0, 0.15));
            c.y = c.laneY;
            c.state = "drive";
            c.go(sx(0.32), c.laneY);
        }
    }

    // Queue
    let waiting = monCars.filter(c => c.state === "wait");
    waiting.forEach((c, i) => {
        c.go(sx(0.32) - i * 52, c.laneY);
    });

    // Auto-managed glow
    if (monBusy) {
        noStroke();
        fill(50, 220, 220, 40 + sin(frameCount * 0.1) * 30);
        ellipse(sx(0.50), sy(0.50), 80, 80);
    }

    // Label
    noStroke();
    fill(0, 0, 0, 180);
    rect(sx(0.38), sy(0.12), 100, 30, 6);
    textSize(12);
    textAlign(CENTER, CENTER);
    fill(80, 230, 230);
    text("AUTO-GESTION", sx(0.38) + 50, sy(0.12) + 15);
    textAlign(LEFT, BASELINE);

    for (let c of monCars) c.show();

    let actStr = monActive ? monActive.label : "Libre";
    let qN = monCars.filter(c => c.state === "wait").length;
    modeInfo = `Caseta: ${monBusy ? "OCUPADA" : "LIBRE"}\nProcesando: ${actStr}\nEn cola: ${qN}`;
}

// ==============================================
// MODE 3: SECCION CRITICA
// ==============================================
function initSeccionCritica() {
    secFlash = 0;
    secCars = [];
    let cols = [RED, BLUE, GREEN];
    let lanes = [sy(0.40), sy(0.50), sy(0.60)];
    for (let i = 0; i < 3; i++) {
        let c = new Car(sx(-0.05 - i * 0.14), lanes[i], cols[i], "H" + (i + 1));
        c.state = "drive";
        c.spd = 2.0;
        c.laneY = lanes[i];
        c.go(sx(0.20), lanes[i]);
        secCars.push(c);
    }
}

function updateSeccionCritica() {
    for (let c of secCars) c.step();

    let inZone = secCars.filter(c => c.state === "zone");

    for (let c of secCars) {
        if (c.state === "drive" && c.at()) {
            c.state = "wait";
        } else if (c.state === "wait") {
            if (secProtected) {
                if (inZone.length === 0) {
                    c.state = "zone";
                    c.hl = true;
                    c.go(sx(0.50), sy(0.50));
                    inZone.push(c);
                }
            } else {
                c.state = "zone";
                c.hl = true;
                c.go(sx(0.50), sy(0.50));
                inZone.push(c);
            }
        } else if (c.state === "zone" && c.at()) {
            c.state = "exit";
            c.hl = false;
            c.go(sx(1.08), c.laneY);
        } else if (c.state === "exit" && c.at()) {
            c.x = sx(-0.08 - random(0, 0.12));
            c.y = c.laneY;
            c.state = "drive";
            c.go(sx(0.20), c.laneY);
        }
    }

    // Queue
    let waiting = secCars.filter(c => c.state === "wait");
    waiting.forEach((c, i) => {
        c.go(sx(0.20) - i * 52, c.laneY);
    });

    // Error flash
    if (!secProtected && inZone.length > 1) {
        secFlash = 20;
    }
    if (secFlash > 0) {
        secFlash--;
        noStroke();
        fill(255, 0, 0, secFlash * 10);
        rect(sx(0.25), sy(0.25), sx(0.75) - sx(0.25), sy(0.75) - sy(0.25), 5);
    }

    // Protection indicator
    noStroke();
    fill(0, 0, 0, 180);
    rect(sx(0.38), sy(0.08), 110, 30, 6);
    textSize(13);
    textAlign(CENTER, CENTER);
    fill(secProtected ? color(80, 255, 120) : color(255, 80, 80));
    text(secProtected ? "PROTEGIDO" : "SIN PROTECCION", sx(0.38) + 55, sy(0.08) + 15);
    textAlign(LEFT, BASELINE);

    for (let c of secCars) c.show();

    modeInfo = `Modo: ${secProtected ? "PROTEGIDO" : "SIN PROTECCION"}\nEn zona critica: ${inZone.length}\nEsperando: ${secCars.filter(c => c.state === "wait").length}`;
}

// ==============================================
// MODE 4: CONDICION DE CARRERA
// ==============================================
function initCondicionCarrera() {
    racePhase = "run";
    raceTimer = 0;
    raceCrashX = sx(0.50);
    raceCrashY = sy(0.65);
    raceCars = [];

    let c1 = new Car(sx(0.13), sy(0.10), RED, "H1");
    c1.state = "race";
    c1.spd = 2.3;
    c1.go(raceCrashX, raceCrashY);
    raceCars.push(c1);

    let c2 = new Car(sx(0.87), sy(0.10), BLUE, "H2");
    c2.state = "race";
    c2.spd = 2.5;
    c2.go(raceCrashX, raceCrashY);
    raceCars.push(c2);
}

function updateCondicionCarrera() {
    if (racePhase === "run") {
        for (let c of raceCars) c.step();

        let d1 = dist(raceCars[0].x, raceCars[0].y, raceCrashX, raceCrashY);
        let d2 = dist(raceCars[1].x, raceCars[1].y, raceCrashX, raceCrashY);
        if (d1 < 20 && d2 < 20) {
            racePhase = "crash";
            raceTimer = 120;
            for (let c of raceCars) c.vis = false;
        }
    } else if (racePhase === "crash") {
        raceTimer--;
        noStroke();
        let intensity = raceTimer * 2;
        fill(255, 50, 0, min(200, intensity));
        ellipse(raceCrashX, raceCrashY, 80 + (120 - raceTimer) * 0.5, 80 + (120 - raceTimer) * 0.5);
        fill(255, 200, 0, min(180, intensity));
        ellipse(raceCrashX, raceCrashY, 50, 50);
        fill(255);
        textSize(18);
        textAlign(CENTER, CENTER);
        text("COLISION!", raceCrashX, raceCrashY - 55);
        textAlign(LEFT, BASELINE);

        if (raceTimer <= 0) {
            racePhase = "reset";
            raceTimer = 60;
        }
    } else if (racePhase === "reset") {
        raceTimer--;
        fill(255, 200, 100);
        textSize(14);
        textAlign(CENTER, CENTER);
        text("Reiniciando...", raceCrashX, raceCrashY);
        textAlign(LEFT, BASELINE);
        if (raceTimer <= 0) {
            initCondicionCarrera();
        }
    }

    // NO CONTROL label
    if (racePhase === "run") {
        noStroke();
        fill(0, 0, 0, 180);
        rect(sx(0.38), sy(0.03), 100, 26, 6);
        fill(255, 80, 80);
        textSize(12);
        textAlign(CENTER, CENTER);
        text("SIN CONTROL", sx(0.38) + 50, sy(0.03) + 13);
        textAlign(LEFT, BASELINE);
    }

    for (let c of raceCars) c.show();

    if (racePhase === "run") {
        modeInfo = "Fase: CORRIENDO\nAmbos aceleran al cruce\nSin semaforo ni control";
    } else if (racePhase === "crash") {
        modeInfo = "Fase: COLISION!\nAcceso simultaneo sin\nsincronizacion = error";
    } else {
        modeInfo = "Reiniciando demo...";
    }
}

// ==============================================
// MODE 5: DEADLOCK
// ==============================================
function initDeadlock() {
    deadPhase = "move";
    deadTimer = 0;
    deadCars = [];

    let ch = new Car(sx(0.08), sy(0.50), RED, "H1");
    ch.state = "go";
    ch.spd = 1.8;
    ch.go(sx(0.46), sy(0.50));
    deadCars.push(ch);

    let cv = new Car(sx(0.50), sy(0.08), BLUE, "H2");
    cv.state = "go";
    cv.spd = 1.8;
    cv.go(sx(0.50), sy(0.46));
    deadCars.push(cv);
}

function updateDeadlock() {
    if (deadPhase === "move") {
        let allArrived = true;
        for (let c of deadCars) {
            c.step();
            if (!c.at()) allArrived = false;
        }
        if (allArrived) {
            deadPhase = "stuck";
            deadTimer = 0;
            for (let c of deadCars) c.hl = true;
        }
    } else if (deadPhase === "stuck") {
        deadTimer++;
        let pulse = Math.abs(sin(deadTimer * 0.05)) * 100;
        noStroke();
        fill(255, 0, 0, 30 + pulse);
        ellipse(sx(0.48), sy(0.48), 90, 90);

        // Labels
        fill(0, 0, 0, 200);
        noStroke();
        rect(sx(0.20), sy(0.28), 120, 36, 5);
        rect(sx(0.56), sy(0.18), 120, 36, 5);

        textSize(10);
        textAlign(CENTER, CENTER);
        fill(255, 100, 100);
        text("H1: Tiene Puente-H\nNecesita Puente-V", sx(0.20) + 60, sy(0.28) + 18);
        fill(100, 150, 255);
        text("H2: Tiene Puente-V\nNecesita Puente-H", sx(0.56) + 60, sy(0.18) + 18);

        // DEADLOCK text
        fill(255, 60, 60);
        textSize(20);
        text("DEADLOCK", sx(0.48), sy(0.75));
        textAlign(LEFT, BASELINE);

        if (deadTimer > 300) {
            initDeadlock();
        }
    }

    for (let c of deadCars) c.show();

    if (deadPhase === "move") {
        modeInfo = "Fase: Adquiriendo recursos\nH1 -> Puente Horizontal\nH2 -> Puente Vertical";
    } else {
        modeInfo = "DEADLOCK DETECTADO!\nH1 tiene H, necesita V\nH2 tiene V, necesita H\nNinguno puede avanzar";
    }
}

// ==============================================
// MODE 6: CONCURRENCIA
// ==============================================
function initConcurrencia() {
    concCars = [];
    let lanesY = [sy(0.10), sy(0.27), sy(0.44), sy(0.58), sy(0.73), sy(0.90)];
    let speeds = [1.8, 2.5, 1.5, 3.0, 2.2, 1.2];
    for (let i = 0; i < 6; i++) {
        let c = new Car(sx(-0.05 - random(0, 0.3)), lanesY[i], ALL_COLORS[i], "H" + (i + 1));
        c.state = "run";
        c.spd = speeds[i];
        c.laneY = lanesY[i];
        c.go(sx(1.08), lanesY[i]);
        concCars.push(c);
    }
}

function updateConcurrencia() {
    for (let c of concCars) {
        c.step();
        if (c.at()) {
            c.x = sx(-0.05 - random(0, 0.2));
            c.y = c.laneY;
            c.go(sx(1.08), c.laneY);
        }
    }

    // Lane labels
    textSize(10);
    fill(255, 255, 255, 120);
    textAlign(LEFT, BASELINE);
    for (let i = 0; i < concCars.length; i++) {
        text("Carril " + (i + 1), sx(0.01), concCars[i].laneY - 20);
    }

    for (let c of concCars) c.show();

    modeInfo = "Hilos activos: 6\nCada uno en su carril\nVelocidades independientes\nSin recursos compartidos";
}

// ==============================================
// MODE INIT DISPATCHER
// ==============================================
function initMode(m) {
    currentMode = m;
    modeInfo = "";
    if (m === 0) initSemaforo();
    else if (m === 1) initMutex();
    else if (m === 2) initMonitor();
    else if (m === 3) initSeccionCritica();
    else if (m === 4) initCondicionCarrera();
    else if (m === 5) initDeadlock();
    else if (m === 6) initConcurrencia();
}

// ==============================================
// INPUT
// ==============================================
function keyPressed() {
    // Mode switching
    if ("1234567".includes(key)) {
        let newMode = parseInt(key) - 1;
        initMode(newMode);
        return false;
    }

    // Reset current demo
    if (key === " ") {
        initMode(currentMode);
        return false;
    }

    // Semaforo: adjust permits
    if (currentMode === 0) {
        if (keyCode === UP_ARROW) {
            semMax = min(5, semMax + 1);
            semAvail = semMax;
            initSemaforo();
            return false;
        } else if (keyCode === DOWN_ARROW) {
            semMax = max(1, semMax - 1);
            semAvail = semMax;
            initSemaforo();
            return false;
        }
    }

    // Seccion critica: toggle protection
    if (currentMode === 3) {
        if (keyCode === ENTER) {
            secProtected = !secProtected;
            initSeccionCritica();
            return false;
        }
    }
}
