# ============================================
# Concurrencia y Sincronizacion
# Simulacion Visual con Trafico Urbano
# Processing (Python Mode)
# ============================================
# Teclas: 1-7 modos, SPACE reiniciar
# UP/DOWN permisos (semaforo)
# ENTER toggle proteccion (seccion critica)
# ============================================

SCENE_X = 5
SCENE_Y = 45
SCENE_W = 840
SCENE_H = 550
PANEL_X = 855
PANEL_W = 340

MODE_NAMES = ["SEMAFORO", "MUTEX", "MONITOR", "SECCION CRITICA",
              "CONDICION DE CARRERA", "DEADLOCK", "CONCURRENCIA"]
MODE_FILES = ["semaforo.png", "mutex.png", "monitor.png", "seccion_critica.png",
              "condicion_carrera.png", "deadlock.png", "concurrencia.png"]
MODE_DESCS = [
    "Contador que permite o bloquea\nel paso de hilos (carros).\nN permisos = N carros cruzan.",
    "Solo UN hilo puede acceder\nal recurso (puente) a la vez.\nLock/Unlock controlan acceso.",
    "Recurso con sincronizacion\nautomatica interna. La caseta\ngestiona sin coordinacion externa.",
    "Zona donde solo entra un hilo.\nENTER: toggle proteccion.\nSin proteccion = error.",
    "Dos hilos acceden sin control\nal mismo recurso. Resultado\nimpredecible: colision!",
    "Dos hilos bloqueados esperando\nrecursos mutuamente.\nBloqueo eterno.",
    "Multiples hilos ejecutandose\nen paralelo, cada uno en su\npropio carril."
]
MODE_CONTROLS = [
    "UP/DOWN: Cambiar permisos",
    "",
    "",
    "ENTER: Toggle proteccion",
    "",
    "",
    ""
]

RED = (220, 50, 50)
BLUE = (50, 120, 220)
GREEN = (50, 200, 80)
YELLOW = (240, 180, 30)
PURPLE = (180, 50, 220)
ORANGE = (255, 130, 50)
CYAN = (50, 210, 210)
PINK = (220, 80, 160)
ALL_COLORS = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, PINK]

def sx(p):
    return int(SCENE_X + SCENE_W * p)

def sy(p):
    return int(SCENE_Y + SCENE_H * p)

# ========== CAR CLASS ==========
class Car:
    def __init__(self, x, y, col, label):
        self.x = float(x)
        self.y = float(y)
        self.tx = float(x)
        self.ty = float(y)
        self.col = col
        self.label = label
        self.spd = 2.5
        self.vis = True
        self.hl = False
        self.state = ""
        self.ang = 0.0

    def go(self, tx, ty):
        self.tx = float(tx)
        self.ty = float(ty)

    def step(self):
        dx = self.tx - self.x
        dy = self.ty - self.y
        d = sqrt(dx * dx + dy * dy)
        if d < self.spd:
            self.x = self.tx
            self.y = self.ty
            return True
        # Update angle based on movement direction
        self.ang = atan2(dy, dx)
        self.x += dx / d * self.spd
        self.y += dy / d * self.spd
        return False

    def at(self):
        return abs(self.x - self.tx) < 2 and abs(self.y - self.ty) < 2

    def show(self):
        if not self.vis:
            return

        pushMatrix()
        translate(self.x, self.y)
        rotate(self.ang)

        # --- Shadow ---
        noStroke()
        fill(0, 0, 0, 55)
        rect(-19, -10, 42, 24, 5)

        # --- Main body ---
        if self.hl:
            stroke(255, 255, 0)
            strokeWeight(3)
        else:
            stroke(25)
            strokeWeight(1)
        fill(self.col[0], self.col[1], self.col[2])
        rect(-21, -12, 42, 24, 5)

        # --- Roof / cabin (darker shade) ---
        noStroke()
        r2 = max(self.col[0] - 40, 0)
        g2 = max(self.col[1] - 40, 0)
        b2 = max(self.col[2] - 40, 0)
        fill(r2, g2, b2)
        rect(-8, -8, 20, 16, 3)

        # --- Windshield (front) ---
        fill(180, 220, 255, 200)
        rect(10, -8, 7, 16, 2)

        # --- Rear window ---
        fill(160, 200, 240, 150)
        rect(-17, -7, 6, 14, 2)

        # --- Wheels ---
        fill(35)
        noStroke()
        rect(-17, -15, 10, 4, 2)
        rect(-17, 11, 10, 4, 2)
        rect(8, -15, 10, 4, 2)
        rect(8, 11, 10, 4, 2)

        # --- Headlights (front) ---
        fill(255, 255, 200, 220)
        rect(19, -9, 3, 5, 1)
        rect(19, 4, 3, 5, 1)

        # --- Taillights (rear) ---
        fill(255, 50, 50, 200)
        rect(-21, -9, 3, 4, 1)
        rect(-21, 5, 3, 4, 1)

        # --- Label ---
        fill(255)
        textSize(9)
        textAlign(CENTER, CENTER)
        text(self.label, 0, 0)
        textAlign(LEFT)

        popMatrix()

        # --- Highlight glow ---
        if self.hl:
            noStroke()
            fill(255, 255, 0, 25 + sin(frameCount * 0.15) * 15)
            ellipse(self.x, self.y, 50, 50)

# ========== GLOBAL STATE ==========
current_mode = 0
images = [None] * 7
mode_info = ""

# Semaforo
sem_cars = []
sem_max = 3
sem_avail = 3

# Mutex
mut_cars = []
mut_locked = False
mut_owner = None

# Monitor
mon_cars = []
mon_busy = False
mon_active = None

# Seccion Critica
sec_cars = []
sec_protected = True
sec_flash = 0

# Condicion de Carrera
race_cars = []
race_phase = "run"
race_timer = 0
race_crash_x = 0
race_crash_y = 0

# Deadlock
dead_cars = []
dead_phase = "move"
dead_timer = 0

# Concurrencia
conc_cars = []

# ========== SETUP ==========
def setup():
    global images
    size(1200, 700)
    for i, f in enumerate(MODE_FILES):
        images[i] = loadImage(f)
    init_mode(0)

# ========== MAIN DRAW ==========
def draw():
    background(35, 40, 50)

    # Title bar
    noStroke()
    fill(30, 33, 42)
    rect(0, 0, width, 40)
    fill(255, 220, 100)
    textSize(16)
    textAlign(LEFT)
    text("Concurrencia y Sincronizacion - Trafico Urbano", 15, 27)

    # Scene background
    img = images[current_mode]
    if img:
        image(img, SCENE_X, SCENE_Y, SCENE_W, SCENE_H)
    else:
        fill(50)
        noStroke()
        rect(SCENE_X, SCENE_Y, SCENE_W, SCENE_H)

    # Scene border
    noFill()
    stroke(70, 90, 120)
    strokeWeight(1)
    rect(SCENE_X, SCENE_Y, SCENE_W, SCENE_H)

    # Mode-specific update + draw
    if current_mode == 0:
        update_semaforo()
    elif current_mode == 1:
        update_mutex()
    elif current_mode == 2:
        update_monitor()
    elif current_mode == 3:
        update_seccion_critica()
    elif current_mode == 4:
        update_condicion_carrera()
    elif current_mode == 5:
        update_deadlock()
    elif current_mode == 6:
        update_concurrencia()

    # Panel
    draw_panel()

# ========== PANEL ==========
def draw_panel():
    noStroke()
    fill(40, 44, 55)
    rect(PANEL_X, 0, PANEL_W, height)

    px = PANEL_X + 15
    py = 15

    # Mode tabs
    for i in range(7):
        bx = px + i * 46
        if i == current_mode:
            fill(255, 220, 100)
        else:
            fill(60, 65, 80)
        noStroke()
        rect(bx, py, 42, 22, 4)
        if i == current_mode:
            fill(30)
        else:
            fill(140)
        textSize(11)
        textAlign(CENTER, CENTER)
        text(str(i + 1), bx + 21, py + 11)
    textAlign(LEFT)
    py += 35

    # Mode name
    fill(255, 220, 100)
    textSize(15)
    text(MODE_NAMES[current_mode], px, py)
    py += 22

    # Description
    fill(170, 190, 210)
    textSize(11)
    for ln in MODE_DESCS[current_mode].split('\n'):
        text(ln, px, py)
        py += 15
    py += 10

    # Separator
    stroke(70, 80, 100)
    line(px, py, px + PANEL_W - 30, py)
    noStroke()
    py += 12

    # Mode info
    fill(200, 220, 240)
    textSize(12)
    for ln in mode_info.split('\n'):
        text(ln, px, py)
        py += 16
    py += 15

    # Separator
    stroke(70, 80, 100)
    line(px, py, px + PANEL_W - 30, py)
    noStroke()
    py += 12

    # Analogia
    fill(255, 200, 100)
    textSize(12)
    text("Analogia:", px, py)
    py += 18
    fill(160, 180, 200)
    textSize(11)
    analogias = [
        "Semaforo de transito con contador.\nN permisos = N carros pasan.\nEl resto espera luz verde.",
        "Puente de un solo carril.\nUn carro cruza, barrera baja.\nAl salir, barrera sube.",
        "Caseta de peaje automatica.\nLa caseta decide quien pasa.\nCarros no se coordinan entre si.",
        "Zona de peligro (rayas amarillas).\nCon proteccion: 1 carro a la vez.\nSin proteccion: chocan.",
        "Dos carros al mismo cruce\nsin semaforo. Ambos aceleran.\nResultado: colision.",
        "Carro A tiene puente H, necesita V.\nCarro B tiene puente V, necesita H.\nNinguno cede: bloqueo eterno.",
        "Autopista de 6 carriles.\nCada carro avanza independiente.\nEjecucion simultanea."
    ]
    for ln in analogias[current_mode].split('\n'):
        text(ln, px, py)
        py += 14
    py += 15

    # Controls
    stroke(70, 80, 100)
    line(px, py, px + PANEL_W - 30, py)
    noStroke()
    py += 12
    fill(120, 140, 170)
    textSize(11)
    text("Controles:", px, py)
    py += 16
    text("1-7: Cambiar modo", px, py)
    py += 14
    text("SPACE: Reiniciar demo", px, py)
    py += 14
    if MODE_CONTROLS[current_mode]:
        fill(255, 200, 100)
        text(MODE_CONTROLS[current_mode], px, py)
    py += 20

    # Bottom label
    fill(80, 90, 110)
    textSize(10)
    text("Hilos=Carros | Recursos=Intersecciones/Puentes", px, height - 15)


# ==============================================
# MODE 0: SEMAFORO
# ==============================================
def init_semaforo():
    global sem_cars, sem_avail
    sem_avail = sem_max
    sem_cars = []
    lanes = [sy(0.38), sy(0.47), sy(0.56)]
    for i in range(5):
        ly = lanes[i % 3]
        c = Car(sx(-0.06 - i * 0.13), ly, ALL_COLORS[i], "H" + str(i + 1))
        c.state = "drive"
        c.spd = 2.2
        c.lane_y = ly
        c.go(sx(0.28), ly)
        sem_cars.append(c)

def update_semaforo():
    global sem_avail, mode_info

    for c in sem_cars:
        c.step()

    for c in sem_cars:
        if c.state == "drive" and c.at():
            c.state = "wait"
        elif c.state == "wait":
            if sem_avail > 0:
                sem_avail -= 1
                c.state = "cross"
                c.hl = True
                c.go(sx(0.72), c.lane_y)
        elif c.state == "cross" and c.at():
            sem_avail += 1
            c.hl = False
            c.state = "exit"
            c.go(sx(1.08), c.lane_y)
        elif c.state == "exit" and c.at():
            c.x = sx(-0.08 - random(0.02, 0.15))
            c.y = c.lane_y
            c.state = "drive"
            c.go(sx(0.28), c.lane_y)

    # Reposition waiting cars in queue
    for lane_y_val in [sy(0.38), sy(0.47), sy(0.56)]:
        waiting = [c for c in sem_cars if c.state == "wait" and abs(c.lane_y - lane_y_val) < 5]
        for i, c in enumerate(waiting):
            qx = sx(0.28) - i * 52
            c.go(qx, c.lane_y)

    # Draw counter overlay
    noStroke()
    fill(0, 0, 0, 180)
    rect(sx(0.42), sy(0.08), 70, 36, 8)
    textSize(22)
    textAlign(CENTER, CENTER)
    if sem_avail > 0:
        fill(80, 255, 120)
    else:
        fill(255, 80, 80)
    text(str(sem_avail) + "/" + str(sem_max), sx(0.42) + 35, sy(0.08) + 18)
    textAlign(LEFT)

    # Traffic light indicator
    noStroke()
    fill(0, 0, 0, 150)
    rect(sx(0.30), sy(0.15), 18, 42, 4)
    if sem_avail > 0:
        fill(50, 80, 50)
        ellipse(sx(0.30) + 9, sy(0.15) + 9, 12, 12)
        fill(80, 255, 80)
        ellipse(sx(0.30) + 9, sy(0.15) + 33, 12, 12)
    else:
        fill(255, 80, 80)
        ellipse(sx(0.30) + 9, sy(0.15) + 9, 12, 12)
        fill(50, 50, 50)
        ellipse(sx(0.30) + 9, sy(0.15) + 33, 12, 12)

    for c in sem_cars:
        c.show()

    in_cross = sum(1 for c in sem_cars if c.state == "cross")
    waiting_n = sum(1 for c in sem_cars if c.state == "wait")
    mode_info = "Permisos: {}/{}\nEn interseccion: {}\nEsperando: {}".format(
        sem_avail, sem_max, in_cross, waiting_n)


# ==============================================
# MODE 1: MUTEX
# ==============================================
def init_mutex():
    global mut_cars, mut_locked, mut_owner
    mut_locked = False
    mut_owner = None
    mut_cars = []
    # 2 from left, 2 from right
    mut_cars.append(Car(sx(0.05), sy(0.44), RED, "H1"))
    mut_cars.append(Car(sx(-0.08), sy(0.58), BLUE, "H2"))
    mut_cars.append(Car(sx(0.95), sy(0.44), GREEN, "H3"))
    mut_cars.append(Car(sx(1.08), sy(0.58), YELLOW, "H4"))
    for i, c in enumerate(mut_cars):
        c.state = "approach"
        c.spd = 2.0
        c.side = "L" if i < 2 else "R"
        if c.side == "L":
            c.wait_x = sx(0.26)
            c.exit_x = sx(1.08)
        else:
            c.wait_x = sx(0.74)
            c.exit_x = sx(-0.08)
        c.go(c.wait_x, c.y)

def update_mutex():
    global mut_locked, mut_owner, mode_info

    for c in mut_cars:
        c.step()

    for c in mut_cars:
        if c.state == "approach" and c.at():
            c.state = "wait"
        elif c.state == "wait" and not mut_locked:
            mut_locked = True
            mut_owner = c
            c.state = "bridge"
            c.hl = True
            c.go(sx(0.50), sy(0.50))
        elif c.state == "bridge" and c.at():
            c.state = "exit"
            c.go(c.exit_x, c.y)
            c.hl = False
            mut_locked = False
            mut_owner = None
        elif c.state == "exit" and c.at():
            # Reset
            if c.side == "L":
                c.x = sx(-0.08 - random(0, 0.1))
            else:
                c.x = sx(1.08 + random(0, 0.1))
            c.state = "approach"
            c.go(c.wait_x, c.y)

    # Queue waiting cars
    for side in ["L", "R"]:
        waiting = [c for c in mut_cars if c.state == "wait" and c.side == side]
        for i, c in enumerate(waiting):
            if side == "L":
                c.go(c.wait_x - i * 52, c.y)
            else:
                c.go(c.wait_x + i * 52, c.y)

    # Draw lock indicator
    noStroke()
    fill(0, 0, 0, 180)
    rect(sx(0.45), sy(0.18), 80, 30, 6)
    textSize(14)
    textAlign(CENTER, CENTER)
    if mut_locked:
        fill(255, 80, 80)
        text("LOCKED", sx(0.45) + 40, sy(0.18) + 15)
    else:
        fill(80, 255, 120)
        text("UNLOCKED", sx(0.45) + 40, sy(0.18) + 15)
    textAlign(LEFT)

    # Barrier lines
    strokeWeight(3)
    if mut_locked:
        stroke(255, 100, 50)
        line(sx(0.32), sy(0.38), sx(0.32), sy(0.62))
        line(sx(0.68), sy(0.38), sx(0.68), sy(0.62))
    else:
        stroke(80, 255, 80, 150)
        line(sx(0.32), sy(0.38), sx(0.32), sy(0.42))
        line(sx(0.68), sy(0.38), sx(0.68), sy(0.42))

    for c in mut_cars:
        c.show()

    owner_str = mut_owner.label if mut_owner else "Ninguno"
    waiting_n = sum(1 for c in mut_cars if c.state == "wait")
    mode_info = "Estado: {}\nDueno: {}\nEsperando: {}".format(
        "LOCKED" if mut_locked else "UNLOCKED", owner_str, waiting_n)


# ==============================================
# MODE 2: MONITOR
# ==============================================
def init_monitor():
    global mon_cars, mon_busy, mon_active
    mon_busy = False
    mon_active = None
    mon_cars = []
    cols = [RED, BLUE, GREEN, PURPLE]
    for i in range(4):
        ly = sy(0.42) if i % 2 == 0 else sy(0.58)
        c = Car(sx(-0.05 - i * 0.12), ly, cols[i], "H" + str(i + 1))
        c.state = "drive"
        c.spd = 2.0
        c.lane_y = ly
        c.go(sx(0.32), ly)
        mon_cars.append(c)

def update_monitor():
    global mon_busy, mon_active, mode_info

    for c in mon_cars:
        c.step()

    for c in mon_cars:
        if c.state == "drive" and c.at():
            c.state = "wait"
        elif c.state == "wait" and not mon_busy:
            mon_busy = True
            mon_active = c
            c.state = "process"
            c.hl = True
            c.go(sx(0.50), sy(0.50))
        elif c.state == "process" and c.at():
            c.state = "done"
            c.go(sx(1.08), c.lane_y)
            c.hl = False
            mon_busy = False
            mon_active = None
        elif c.state == "done" and c.at():
            c.x = sx(-0.08 - random(0, 0.15))
            c.y = c.lane_y
            c.state = "drive"
            c.go(sx(0.32), c.lane_y)

    # Queue
    waiting = [c for c in mon_cars if c.state == "wait"]
    for i, c in enumerate(waiting):
        c.go(sx(0.32) - i * 52, c.lane_y)

    # Auto-managed glow
    if mon_busy:
        noStroke()
        fill(50, 220, 220, 40 + sin(frameCount * 0.1) * 30)
        ellipse(sx(0.50), sy(0.50), 80, 80)

    # Label
    noStroke()
    fill(0, 0, 0, 180)
    rect(sx(0.38), sy(0.12), 100, 30, 6)
    textSize(12)
    textAlign(CENTER, CENTER)
    fill(80, 230, 230)
    text("AUTO-GESTION", sx(0.38) + 50, sy(0.12) + 15)
    textAlign(LEFT)

    for c in mon_cars:
        c.show()

    act_str = mon_active.label if mon_active else "Libre"
    q_n = sum(1 for c in mon_cars if c.state == "wait")
    mode_info = "Caseta: {}\nProcesando: {}\nEn cola: {}".format(
        "OCUPADA" if mon_busy else "LIBRE", act_str, q_n)


# ==============================================
# MODE 3: SECCION CRITICA
# ==============================================
def init_seccion_critica():
    global sec_cars, sec_flash
    sec_flash = 0
    sec_cars = []
    cols = [RED, BLUE, GREEN]
    lanes = [sy(0.40), sy(0.50), sy(0.60)]
    for i in range(3):
        c = Car(sx(-0.05 - i * 0.14), lanes[i], cols[i], "H" + str(i + 1))
        c.state = "drive"
        c.spd = 2.0
        c.lane_y = lanes[i]
        c.go(sx(0.20), lanes[i])
        sec_cars.append(c)

def update_seccion_critica():
    global sec_flash, mode_info

    for c in sec_cars:
        c.step()

    in_zone = [c for c in sec_cars if c.state == "zone"]

    for c in sec_cars:
        if c.state == "drive" and c.at():
            c.state = "wait"
        elif c.state == "wait":
            if sec_protected:
                if len(in_zone) == 0:
                    c.state = "zone"
                    c.hl = True
                    c.go(sx(0.50), sy(0.50))
                    in_zone.append(c)
            else:
                c.state = "zone"
                c.hl = True
                c.go(sx(0.50), sy(0.50))
                in_zone.append(c)
        elif c.state == "zone" and c.at():
            c.state = "exit"
            c.hl = False
            c.go(sx(1.08), c.lane_y)
        elif c.state == "exit" and c.at():
            c.x = sx(-0.08 - random(0, 0.12))
            c.y = c.lane_y
            c.state = "drive"
            c.go(sx(0.20), c.lane_y)

    # Queue
    waiting = [c for c in sec_cars if c.state == "wait"]
    for i, c in enumerate(waiting):
        c.go(sx(0.20) - i * 52, c.lane_y)

    # Error flash if unprotected and multiple in zone
    if not sec_protected and len(in_zone) > 1:
        sec_flash = 20
    if sec_flash > 0:
        sec_flash -= 1
        noStroke()
        fill(255, 0, 0, sec_flash * 10)
        rect(sx(0.25), sy(0.25), sx(0.75) - sx(0.25), sy(0.75) - sy(0.25), 5)

    # Protection indicator
    noStroke()
    fill(0, 0, 0, 180)
    rect(sx(0.38), sy(0.08), 110, 30, 6)
    textSize(13)
    textAlign(CENTER, CENTER)
    if sec_protected:
        fill(80, 255, 120)
        text("PROTEGIDO", sx(0.38) + 55, sy(0.08) + 15)
    else:
        fill(255, 80, 80)
        text("SIN PROTECCION", sx(0.38) + 55, sy(0.08) + 15)
    textAlign(LEFT)

    for c in sec_cars:
        c.show()

    mode_info = "Modo: {}\nEn zona critica: {}\nEsperando: {}".format(
        "PROTEGIDO" if sec_protected else "SIN PROTECCION",
        len(in_zone),
        sum(1 for c in sec_cars if c.state == "wait"))


# ==============================================
# MODE 4: CONDICION DE CARRERA
# ==============================================
def init_condicion_carrera():
    global race_cars, race_phase, race_timer, race_crash_x, race_crash_y
    race_phase = "run"
    race_timer = 0
    race_crash_x = sx(0.50)
    race_crash_y = sy(0.65)
    race_cars = []
    c1 = Car(sx(0.13), sy(0.10), RED, "H1")
    c1.state = "race"
    c1.spd = 2.3
    c1.go(race_crash_x, race_crash_y)
    race_cars.append(c1)
    c2 = Car(sx(0.87), sy(0.10), BLUE, "H2")
    c2.state = "race"
    c2.spd = 2.5
    c2.go(race_crash_x, race_crash_y)
    race_cars.append(c2)

def update_condicion_carrera():
    global race_phase, race_timer, mode_info

    if race_phase == "run":
        for c in race_cars:
            c.step()
        # Check if both near merge
        d1 = dist(race_cars[0].x, race_cars[0].y, race_crash_x, race_crash_y)
        d2 = dist(race_cars[1].x, race_cars[1].y, race_crash_x, race_crash_y)
        if d1 < 20 and d2 < 20:
            race_phase = "crash"
            race_timer = 120
            for c in race_cars:
                c.vis = False

    elif race_phase == "crash":
        race_timer -= 1
        # Explosion effect
        noStroke()
        intensity = race_timer * 2
        fill(255, 50, 0, min(200, intensity))
        ellipse(race_crash_x, race_crash_y, 80 + (120 - race_timer) * 0.5, 80 + (120 - race_timer) * 0.5)
        fill(255, 200, 0, min(180, intensity))
        ellipse(race_crash_x, race_crash_y, 50, 50)
        fill(255)
        textSize(18)
        textAlign(CENTER, CENTER)
        text("COLISION!", race_crash_x, race_crash_y - 55)
        textAlign(LEFT)

        if race_timer <= 0:
            race_phase = "reset"
            race_timer = 60

    elif race_phase == "reset":
        race_timer -= 1
        fill(255, 200, 100)
        textSize(14)
        textAlign(CENTER, CENTER)
        text("Reiniciando...", race_crash_x, race_crash_y)
        textAlign(LEFT)
        if race_timer <= 0:
            init_condicion_carrera()

    # Draw "NO CONTROL" label
    if race_phase == "run":
        noStroke()
        fill(0, 0, 0, 180)
        rect(sx(0.38), sy(0.03), 100, 26, 6)
        fill(255, 80, 80)
        textSize(12)
        textAlign(CENTER, CENTER)
        text("SIN CONTROL", sx(0.38) + 50, sy(0.03) + 13)
        textAlign(LEFT)

    for c in race_cars:
        c.show()

    if race_phase == "run":
        mode_info = "Fase: CORRIENDO\nAmbos aceleran al cruce\nSin semaforo ni control"
    elif race_phase == "crash":
        mode_info = "Fase: COLISION!\nAcceso simultaneo sin\nsincronizacion = error"
    else:
        mode_info = "Reiniciando demo..."


# ==============================================
# MODE 5: DEADLOCK
# ==============================================
def init_deadlock():
    global dead_cars, dead_phase, dead_timer
    dead_phase = "move"
    dead_timer = 0
    dead_cars = []
    ch = Car(sx(0.08), sy(0.50), RED, "H1")
    ch.state = "go"
    ch.spd = 1.8
    ch.go(sx(0.46), sy(0.50))
    dead_cars.append(ch)
    cv = Car(sx(0.50), sy(0.08), BLUE, "H2")
    cv.state = "go"
    cv.spd = 1.8
    cv.go(sx(0.50), sy(0.46))
    dead_cars.append(cv)

def update_deadlock():
    global dead_phase, dead_timer, mode_info

    if dead_phase == "move":
        all_arrived = True
        for c in dead_cars:
            c.step()
            if not c.at():
                all_arrived = False
        if all_arrived:
            dead_phase = "stuck"
            dead_timer = 0
            for c in dead_cars:
                c.hl = True

    elif dead_phase == "stuck":
        dead_timer += 1
        # Pulsing red glow
        pulse = abs(sin(dead_timer * 0.05)) * 100
        noStroke()
        fill(255, 0, 0, 30 + pulse)
        ellipse(sx(0.48), sy(0.48), 90, 90)

        # Labels showing what each holds/needs
        fill(0, 0, 0, 200)
        noStroke()
        rect(sx(0.20), sy(0.28), 120, 36, 5)
        rect(sx(0.56), sy(0.18), 120, 36, 5)

        textSize(10)
        fill(255, 100, 100)
        textAlign(CENTER, CENTER)
        text("H1: Tiene Puente-H\nNecesita Puente-V", sx(0.20) + 60, sy(0.28) + 18)
        fill(100, 150, 255)
        text("H2: Tiene Puente-V\nNecesita Puente-H", sx(0.56) + 60, sy(0.18) + 18)
        textAlign(LEFT)

        # DEADLOCK text
        fill(255, 60, 60)
        textSize(20)
        textAlign(CENTER, CENTER)
        text("DEADLOCK", sx(0.48), sy(0.75))
        textAlign(LEFT)

        # Auto-reset
        if dead_timer > 300:
            init_deadlock()

    for c in dead_cars:
        c.show()

    if dead_phase == "move":
        mode_info = "Fase: Adquiriendo recursos\nH1 -> Puente Horizontal\nH2 -> Puente Vertical"
    else:
        mode_info = "DEADLOCK DETECTADO!\nH1 tiene H, necesita V\nH2 tiene V, necesita H\nNinguno puede avanzar"


# ==============================================
# MODE 6: CONCURRENCIA
# ==============================================
def init_concurrencia():
    global conc_cars
    conc_cars = []
    lanes_y = [sy(0.10), sy(0.27), sy(0.44), sy(0.58), sy(0.73), sy(0.90)]
    speeds = [1.8, 2.5, 1.5, 3.0, 2.2, 1.2]
    for i in range(6):
        c = Car(sx(-0.05 - random(0, 0.3)), lanes_y[i], ALL_COLORS[i], "H" + str(i + 1))
        c.state = "run"
        c.spd = speeds[i]
        c.lane_y = lanes_y[i]
        c.go(sx(1.08), lanes_y[i])
        conc_cars.append(c)

def update_concurrencia():
    global mode_info

    for c in conc_cars:
        c.step()
        if c.at():
            c.x = sx(-0.05 - random(0, 0.2))
            c.y = c.lane_y
            c.go(sx(1.08), c.lane_y)

    # Lane labels
    textSize(10)
    fill(255, 255, 255, 120)
    textAlign(LEFT)
    for i, c in enumerate(conc_cars):
        text("Carril " + str(i + 1), sx(0.01), c.lane_y - 20)

    for c in conc_cars:
        c.show()

    mode_info = "Hilos activos: 6\nCada uno en su carril\nVelocidades independientes\nSin recursos compartidos"


# ==============================================
# MODE INIT DISPATCHER
# ==============================================
def init_mode(m):
    global current_mode, mode_info
    current_mode = m
    mode_info = ""
    if m == 0:
        init_semaforo()
    elif m == 1:
        init_mutex()
    elif m == 2:
        init_monitor()
    elif m == 3:
        init_seccion_critica()
    elif m == 4:
        init_condicion_carrera()
    elif m == 5:
        init_deadlock()
    elif m == 6:
        init_concurrencia()


# ==============================================
# INPUT
# ==============================================
def keyPressed():
    global current_mode, sem_max, sem_avail, sec_protected

    # Mode switching
    if key in '1234567':
        new_mode = int(key) - 1
        init_mode(new_mode)
        return

    # Reset current demo
    if key == ' ':
        init_mode(current_mode)
        return

    # Semaforo: adjust permits
    if current_mode == 0:
        if keyCode == UP:
            sem_max = min(5, sem_max + 1)
            sem_avail = sem_max
            init_semaforo()
        elif keyCode == DOWN:
            sem_max = max(1, sem_max - 1)
            sem_avail = sem_max
            init_semaforo()

    # Seccion critica: toggle protection
    if current_mode == 3:
        if key == ENTER or key == RETURN:
            sec_protected = not sec_protected
            init_seccion_critica()
