# ============================================
# Concurrencia y Sincronizacion
# Simulacion Visual con Trafico Urbano
# Processing (Python Mode) + threading
# ============================================
# Teclas: 1-7 modos, SPACE reiniciar
# UP/DOWN permisos (semaforo)
# ENTER toggle proteccion (seccion critica)
# ============================================

import threading
import time
import random as py_random

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
        noStroke()
        fill(0, 0, 0, 55)
        rect(-19, -10, 42, 24, 5)
        if self.hl:
            stroke(255, 255, 0)
            strokeWeight(3)
        else:
            stroke(25)
            strokeWeight(1)
        fill(self.col[0], self.col[1], self.col[2])
        rect(-21, -12, 42, 24, 5)
        noStroke()
        r2 = max(self.col[0] - 40, 0)
        g2 = max(self.col[1] - 40, 0)
        b2 = max(self.col[2] - 40, 0)
        fill(r2, g2, b2)
        rect(-8, -8, 20, 16, 3)
        fill(180, 220, 255, 200)
        rect(10, -8, 7, 16, 2)
        fill(160, 200, 240, 150)
        rect(-17, -7, 6, 14, 2)
        fill(35)
        noStroke()
        rect(-17, -15, 10, 4, 2)
        rect(-17, 11, 10, 4, 2)
        rect(8, -15, 10, 4, 2)
        rect(8, 11, 10, 4, 2)
        fill(255, 255, 200, 220)
        rect(19, -9, 3, 5, 1)
        rect(19, 4, 3, 5, 1)
        fill(255, 50, 50, 200)
        rect(-21, -9, 3, 4, 1)
        rect(-21, 5, 3, 4, 1)
        fill(255)
        textSize(9)
        textAlign(CENTER, CENTER)
        text(self.label, 0, 0)
        textAlign(LEFT)
        popMatrix()
        if self.hl:
            noStroke()
            fill(255, 255, 0, 25 + sin(frameCount * 0.15) * 15)
            ellipse(self.x, self.y, 50, 50)


# ========== THREADING INFRASTRUCTURE ==========
stop_event = threading.Event()
car_threads = []

def stop_threads():
    stop_event.set()
    time.sleep(0.2)
    stop_event.clear()
    car_threads[:] = []

class CarThread(threading.Thread):
    def __init__(self, car):
        threading.Thread.__init__(self)
        self.car = car
        self.daemon = True

    def stopped(self):
        return stop_event.is_set()

    def wait_arrive(self):
        while not self.car.at() and not self.stopped():
            time.sleep(0.02)
        return not self.stopped()

    def safe_acquire(self, prim):
        while not self.stopped():
            if prim.acquire(False):
                return True
            time.sleep(0.04)
        return False

    def pause(self, secs):
        stop_event.wait(secs)
        return not self.stopped()

def start_thread(t):
    car_threads.append(t)
    t.start()


# ========== THREAD CLASSES PER MODE ==========

# --- Semaforo: threading.Semaphore ---
class SemThread(CarThread):
    def __init__(self, car, semaphore, delay):
        CarThread.__init__(self, car)
        self.sem = semaphore
        self.delay = delay

    def run(self):
        if not self.pause(self.delay):
            return
        while not self.stopped():
            self.car.state = "drive"
            self.car.go(sx(0.28), self.car.lane_y)
            if not self.wait_arrive():
                return
            self.car.state = "wait"
            if not self.safe_acquire(self.sem):
                return
            self.car.state = "cross"
            self.car.hl = True
            self.car.go(sx(0.72), self.car.lane_y)
            if not self.wait_arrive():
                self.sem.release()
                return
            self.sem.release()
            self.car.hl = False
            self.car.state = "exit"
            self.car.go(sx(1.08), self.car.lane_y)
            if not self.wait_arrive():
                return
            self.car.x = sx(-0.08)
            self.car.y = self.car.lane_y
            if not self.pause(py_random.uniform(0.1, 0.4)):
                return


# --- Mutex: threading.Lock ---
class MutThread(CarThread):
    def __init__(self, car, lock, delay):
        CarThread.__init__(self, car)
        self.lock = lock
        self.delay = delay

    def run(self):
        if not self.pause(self.delay):
            return
        while not self.stopped():
            self.car.state = "approach"
            self.car.go(self.car.wait_x, self.car.y)
            if not self.wait_arrive():
                return
            self.car.state = "wait"
            if not self.safe_acquire(self.lock):
                return
            self.car.state = "bridge"
            self.car.hl = True
            self.car.go(sx(0.50), sy(0.50))
            if not self.wait_arrive():
                self.lock.release()
                return
            self.lock.release()
            self.car.hl = False
            self.car.state = "exit"
            self.car.go(self.car.exit_x, self.car.y)
            if not self.wait_arrive():
                return
            if self.car.side == "L":
                self.car.x = sx(-0.08)
            else:
                self.car.x = sx(1.08)
            if not self.pause(py_random.uniform(0.1, 0.3)):
                return


# --- Monitor: threading.Condition ---
class MonThread(CarThread):
    def __init__(self, car, condition, busy_flag, delay):
        CarThread.__init__(self, car)
        self.cond = condition
        self.busy = busy_flag
        self.delay = delay

    def run(self):
        if not self.pause(self.delay):
            return
        while not self.stopped():
            self.car.state = "drive"
            self.car.go(sx(0.32), self.car.lane_y)
            if not self.wait_arrive():
                return
            self.car.state = "wait"
            # Monitor: acquire condition and wait
            self.cond.acquire()
            while self.busy[0] and not self.stopped():
                self.cond.wait(0.1)
            if self.stopped():
                self.cond.release()
                return
            self.busy[0] = True
            self.cond.release()
            self.car.state = "process"
            self.car.hl = True
            self.car.go(sx(0.50), sy(0.50))
            if not self.wait_arrive():
                self.cond.acquire()
                self.busy[0] = False
                self.cond.notify()
                self.cond.release()
                return
            # Release monitor
            self.cond.acquire()
            self.busy[0] = False
            self.cond.notify()
            self.cond.release()
            self.car.hl = False
            self.car.state = "done"
            self.car.go(sx(1.08), self.car.lane_y)
            if not self.wait_arrive():
                return
            self.car.x = sx(-0.08)
            self.car.y = self.car.lane_y
            if not self.pause(py_random.uniform(0.1, 0.3)):
                return


# --- Seccion Critica: threading.Lock (togglable) ---
class SecThread(CarThread):
    def __init__(self, car, lock, protected_flag, delay):
        CarThread.__init__(self, car)
        self.lock = lock
        self.prot = protected_flag
        self.delay = delay

    def run(self):
        if not self.pause(self.delay):
            return
        while not self.stopped():
            self.car.state = "drive"
            self.car.go(sx(0.20), self.car.lane_y)
            if not self.wait_arrive():
                return
            self.car.state = "wait"
            if self.prot[0]:
                if not self.safe_acquire(self.lock):
                    return
            self.car.state = "zone"
            self.car.hl = True
            self.car.go(sx(0.50), sy(0.50))
            if not self.wait_arrive():
                if self.prot[0]:
                    try:
                        self.lock.release()
                    except:
                        pass
                return
            if self.prot[0]:
                self.lock.release()
            self.car.hl = False
            self.car.state = "exit"
            self.car.go(sx(1.08), self.car.lane_y)
            if not self.wait_arrive():
                return
            self.car.x = sx(-0.08)
            self.car.y = self.car.lane_y
            if not self.pause(py_random.uniform(0.05, 0.2)):
                return


# --- Condicion de Carrera: SIN sincronizacion ---
class RaceThread(CarThread):
    def __init__(self, car, target_x, target_y):
        CarThread.__init__(self, car)
        self.target_x = target_x
        self.target_y = target_y

    def run(self):
        self.car.state = "race"
        self.car.go(self.target_x, self.target_y)
        self.wait_arrive()


# --- Deadlock: 2 Locks adquiridos en orden inverso ---
class DeadThread(CarThread):
    def __init__(self, car, first_lock, second_lock, tx, ty):
        CarThread.__init__(self, car)
        self.first = first_lock
        self.second = second_lock
        self.tx = tx
        self.ty = ty

    def run(self):
        # Acquire first lock immediately
        self.first.acquire()
        self.car.state = "go"
        self.car.go(self.tx, self.ty)
        if not self.wait_arrive():
            self.first.release()
            return
        # Try to acquire second lock -> DEADLOCK
        self.car.hl = True
        self.car.state = "stuck"
        while not self.stopped():
            if self.second.acquire(False):
                self.second.release()
                break
            time.sleep(0.05)
        self.first.release()


# --- Concurrencia: hilos independientes ---
class ConcThread(CarThread):
    def run(self):
        while not self.stopped():
            self.car.state = "run"
            self.car.go(sx(1.08), self.car.lane_y)
            if not self.wait_arrive():
                return
            self.car.x = sx(-0.05)
            self.car.y = self.car.lane_y
            if not self.pause(py_random.uniform(0.05, 0.2)):
                return


# ========== GLOBAL STATE ==========
current_mode = 0
images = [None] * 7
mode_info = ""

# Semaforo
sem_cars = []
sem_max = 2
sem_prim = None

# Mutex
mut_cars = []
mut_prim = None

# Monitor
mon_cars = []
mon_cond = None
mon_busy = [False]

# Seccion Critica
sec_cars = []
sec_prim = None
sec_protected = [True]
sec_flash = 0

# Condicion de Carrera
race_cars = []
race_phase = "run"
race_timer = 0
race_crash_x = 0
race_crash_y = 0

# Deadlock
dead_cars = []
dead_lock_h = None
dead_lock_v = None

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

    noStroke()
    fill(30, 33, 42)
    rect(0, 0, width, 40)
    fill(255, 220, 100)
    textSize(16)
    textAlign(LEFT)
    text("Concurrencia y Sincronizacion - Trafico Urbano", 15, 27)

    img = images[current_mode]
    if img:
        image(img, SCENE_X, SCENE_Y, SCENE_W, SCENE_H)
    else:
        fill(50)
        noStroke()
        rect(SCENE_X, SCENE_Y, SCENE_W, SCENE_H)

    noFill()
    stroke(70, 90, 120)
    strokeWeight(1)
    rect(SCENE_X, SCENE_Y, SCENE_W, SCENE_H)

    if current_mode == 0:
        render_semaforo()
    elif current_mode == 1:
        render_mutex()
    elif current_mode == 2:
        render_monitor()
    elif current_mode == 3:
        render_seccion_critica()
    elif current_mode == 4:
        render_condicion_carrera()
    elif current_mode == 5:
        render_deadlock()
    elif current_mode == 6:
        render_concurrencia()

    draw_panel()

# ========== PANEL ==========
def draw_panel():
    noStroke()
    fill(40, 44, 55)
    rect(PANEL_X, 0, PANEL_W, height)

    px = PANEL_X + 15
    py = 15

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

    fill(255, 220, 100)
    textSize(15)
    text(MODE_NAMES[current_mode], px, py)
    py += 22

    fill(170, 190, 210)
    textSize(11)
    for ln in MODE_DESCS[current_mode].split('\n'):
        text(ln, px, py)
        py += 15
    py += 10

    stroke(70, 80, 100)
    line(px, py, px + PANEL_W - 30, py)
    noStroke()
    py += 12

    # Threading primitive label
    prim_names = [
        "threading.Semaphore({})",
        "threading.Lock()",
        "threading.Condition()",
        "threading.Lock()",
        "SIN threading (error!)",
        "2x threading.Lock()",
        "threading.Thread x6"
    ]
    fill(100, 220, 255)
    textSize(11)
    if current_mode == 0:
        text(prim_names[0].format(sem_max), px, py)
    else:
        text(prim_names[current_mode], px, py)
    py += 20

    fill(200, 220, 240)
    textSize(12)
    for ln in mode_info.split('\n'):
        text(ln, px, py)
        py += 16
    py += 10

    stroke(70, 80, 100)
    line(px, py, px + PANEL_W - 30, py)
    noStroke()
    py += 12

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

    # Thread count
    alive = sum(1 for t in car_threads if t.is_alive())
    fill(80, 200, 180)
    textSize(10)
    text("Hilos activos: {}".format(alive), px, height - 30)
    fill(80, 90, 110)
    text("Hilos=Carros | Recursos=Intersecciones", px, height - 15)


# ==============================================
# RENDER MODE 0: SEMAFORO
# ==============================================
def init_semaforo():
    global sem_cars, sem_prim
    stop_threads()
    sem_prim = threading.Semaphore(sem_max)
    sem_cars = []
    lanes = [sy(0.38), sy(0.47), sy(0.56)]
    for i in range(5):
        ly = lanes[i % 3]
        c = Car(sx(-0.06 - i * 0.13), ly, ALL_COLORS[i], "H" + str(i + 1))
        c.spd = 2.2
        c.lane_y = ly
        sem_cars.append(c)
        t = SemThread(c, sem_prim, i * 0.3)
        start_thread(t)

def render_semaforo():
    global mode_info
    for c in sem_cars:
        c.step()

    # Queue positioning (visual only)
    for lane_y_val in [sy(0.38), sy(0.47), sy(0.56)]:
        waiting = [c for c in sem_cars if c.state == "wait" and abs(c.lane_y - lane_y_val) < 5]
        for i, c in enumerate(waiting):
            c.go(sx(0.28) - i * 52, c.lane_y)

    in_cross = sum(1 for c in sem_cars if c.state == "cross")
    avail = sem_max - in_cross

    noStroke()
    fill(0, 0, 0, 180)
    rect(sx(0.42), sy(0.08), 70, 36, 8)
    textSize(22)
    textAlign(CENTER, CENTER)
    if avail > 0:
        fill(80, 255, 120)
    else:
        fill(255, 80, 80)
    text(str(avail) + "/" + str(sem_max), sx(0.42) + 35, sy(0.08) + 18)
    textAlign(LEFT)

    noStroke()
    fill(0, 0, 0, 150)
    rect(sx(0.30), sy(0.15), 18, 42, 4)
    if avail > 0:
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

    waiting_n = sum(1 for c in sem_cars if c.state == "wait")
    mode_info = "Permisos: {}/{}\nEn interseccion: {}\nEsperando: {}".format(
        avail, sem_max, in_cross, waiting_n)


# ==============================================
# RENDER MODE 1: MUTEX
# ==============================================
def init_mutex():
    global mut_cars, mut_prim
    stop_threads()
    mut_prim = threading.Lock()
    mut_cars = []
    configs = [
        (sx(0.05), sy(0.44), RED, "H1", "L"),
        (sx(-0.08), sy(0.58), BLUE, "H2", "L"),
        (sx(0.95), sy(0.44), GREEN, "H3", "R"),
        (sx(1.08), sy(0.58), YELLOW, "H4", "R"),
    ]
    for i, cfg in enumerate(configs):
        c = Car(cfg[0], cfg[1], cfg[2], cfg[3])
        c.spd = 2.0
        c.side = cfg[4]
        c.wait_x = sx(0.26) if c.side == "L" else sx(0.74)
        c.exit_x = sx(1.08) if c.side == "L" else sx(-0.08)
        mut_cars.append(c)
        t = MutThread(c, mut_prim, i * 0.4)
        start_thread(t)

def render_mutex():
    global mode_info
    for c in mut_cars:
        c.step()

    for side in ["L", "R"]:
        waiting = [c for c in mut_cars if c.state == "wait" and c.side == side]
        for i, c in enumerate(waiting):
            if side == "L":
                c.go(c.wait_x - i * 52, c.y)
            else:
                c.go(c.wait_x + i * 52, c.y)

    is_locked = any(c.state == "bridge" for c in mut_cars)
    owner = next((c for c in mut_cars if c.state == "bridge"), None)

    noStroke()
    fill(0, 0, 0, 180)
    rect(sx(0.45), sy(0.18), 80, 30, 6)
    textSize(14)
    textAlign(CENTER, CENTER)
    if is_locked:
        fill(255, 80, 80)
        text("LOCKED", sx(0.45) + 40, sy(0.18) + 15)
    else:
        fill(80, 255, 120)
        text("UNLOCKED", sx(0.45) + 40, sy(0.18) + 15)
    textAlign(LEFT)

    strokeWeight(3)
    if is_locked:
        stroke(255, 100, 50)
        line(sx(0.32), sy(0.38), sx(0.32), sy(0.62))
        line(sx(0.68), sy(0.38), sx(0.68), sy(0.62))
    else:
        stroke(80, 255, 80, 150)
        line(sx(0.32), sy(0.38), sx(0.32), sy(0.42))
        line(sx(0.68), sy(0.38), sx(0.68), sy(0.42))

    for c in mut_cars:
        c.show()

    owner_str = owner.label if owner else "Ninguno"
    waiting_n = sum(1 for c in mut_cars if c.state == "wait")
    mode_info = "Estado: {}\nDueno del lock: {}\nEsperando: {}".format(
        "LOCKED" if is_locked else "UNLOCKED", owner_str, waiting_n)


# ==============================================
# RENDER MODE 2: MONITOR
# ==============================================
def init_monitor():
    global mon_cars, mon_cond, mon_busy
    stop_threads()
    mon_lock = threading.Lock()
    mon_cond = threading.Condition(mon_lock)
    mon_busy = [False]
    mon_cars = []
    cols = [RED, BLUE, GREEN, PURPLE]
    for i in range(4):
        ly = sy(0.42) if i % 2 == 0 else sy(0.58)
        c = Car(sx(-0.05 - i * 0.12), ly, cols[i], "H" + str(i + 1))
        c.spd = 2.0
        c.lane_y = ly
        mon_cars.append(c)
        t = MonThread(c, mon_cond, mon_busy, i * 0.35)
        start_thread(t)

def render_monitor():
    global mode_info
    for c in mon_cars:
        c.step()

    waiting = [c for c in mon_cars if c.state == "wait"]
    for i, c in enumerate(waiting):
        c.go(sx(0.32) - i * 52, c.lane_y)

    is_busy = mon_busy[0]
    active = next((c for c in mon_cars if c.state == "process"), None)

    if is_busy:
        noStroke()
        fill(50, 220, 220, 40 + sin(frameCount * 0.1) * 30)
        ellipse(sx(0.50), sy(0.50), 80, 80)

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

    act_str = active.label if active else "Libre"
    q_n = len(waiting)
    mode_info = "Caseta: {}\nProcesando: {}\nEn cola: {}".format(
        "OCUPADA" if is_busy else "LIBRE", act_str, q_n)


# ==============================================
# RENDER MODE 3: SECCION CRITICA
# ==============================================
def init_seccion_critica():
    global sec_cars, sec_prim, sec_flash
    stop_threads()
    sec_prim = threading.Lock()
    sec_flash = 0
    sec_cars = []
    cols = [RED, BLUE, GREEN]
    lanes = [sy(0.40), sy(0.50), sy(0.60)]
    for i in range(3):
        c = Car(sx(-0.05 - i * 0.14), lanes[i], cols[i], "H" + str(i + 1))
        c.spd = 2.0
        c.lane_y = lanes[i]
        sec_cars.append(c)
        t = SecThread(c, sec_prim, sec_protected, i * 0.25)
        start_thread(t)

def render_seccion_critica():
    global sec_flash, mode_info
    for c in sec_cars:
        c.step()

    waiting = [c for c in sec_cars if c.state == "wait"]
    for i, c in enumerate(waiting):
        c.go(sx(0.20) - i * 52, c.lane_y)

    in_zone = [c for c in sec_cars if c.state == "zone"]

    if not sec_protected[0] and len(in_zone) > 1:
        sec_flash = 20
    if sec_flash > 0:
        sec_flash -= 1
        noStroke()
        fill(255, 0, 0, sec_flash * 10)
        rect(sx(0.25), sy(0.25), sx(0.75) - sx(0.25), sy(0.75) - sy(0.25), 5)

    noStroke()
    fill(0, 0, 0, 180)
    rect(sx(0.38), sy(0.08), 110, 30, 6)
    textSize(13)
    textAlign(CENTER, CENTER)
    if sec_protected[0]:
        fill(80, 255, 120)
        text("PROTEGIDO", sx(0.38) + 55, sy(0.08) + 15)
    else:
        fill(255, 80, 80)
        text("SIN PROTECCION", sx(0.38) + 55, sy(0.08) + 15)
    textAlign(LEFT)

    for c in sec_cars:
        c.show()

    mode_info = "Modo: {}\nEn zona critica: {}\nEsperando: {}".format(
        "PROTEGIDO" if sec_protected[0] else "SIN PROTECCION",
        len(in_zone), len(waiting))


# ==============================================
# RENDER MODE 4: CONDICION DE CARRERA
# ==============================================
def init_condicion_carrera():
    global race_cars, race_phase, race_timer, race_crash_x, race_crash_y
    stop_threads()
    race_phase = "run"
    race_timer = 0
    race_crash_x = sx(0.50)
    race_crash_y = sy(0.65)
    race_cars = []
    c1 = Car(sx(0.13), sy(0.10), RED, "H1")
    c1.spd = 2.3
    race_cars.append(c1)
    c2 = Car(sx(0.87), sy(0.10), BLUE, "H2")
    c2.spd = 2.5
    race_cars.append(c2)
    # Two threads WITHOUT synchronization
    start_thread(RaceThread(c1, race_crash_x, race_crash_y))
    start_thread(RaceThread(c2, race_crash_x, race_crash_y))

def render_condicion_carrera():
    global race_phase, race_timer, mode_info

    if race_phase == "run":
        for c in race_cars:
            c.step()
        d1 = dist(race_cars[0].x, race_cars[0].y, race_crash_x, race_crash_y)
        d2 = dist(race_cars[1].x, race_cars[1].y, race_crash_x, race_crash_y)
        if d1 < 20 and d2 < 20:
            race_phase = "crash"
            race_timer = 120
            for c in race_cars:
                c.vis = False
    elif race_phase == "crash":
        race_timer -= 1
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
        mode_info = "Fase: CORRIENDO\nAmbos hilos sin sync\nSin semaforo ni lock"
    elif race_phase == "crash":
        mode_info = "COLISION!\nAcceso simultaneo sin\nsincronizacion = error"
    else:
        mode_info = "Reiniciando demo..."


# ==============================================
# RENDER MODE 5: DEADLOCK
# ==============================================
def init_deadlock():
    global dead_cars, dead_lock_h, dead_lock_v
    stop_threads()
    dead_lock_h = threading.Lock()
    dead_lock_v = threading.Lock()
    dead_cars = []
    ch = Car(sx(0.08), sy(0.50), RED, "H1")
    ch.spd = 1.8
    dead_cars.append(ch)
    cv = Car(sx(0.50), sy(0.08), BLUE, "H2")
    cv.spd = 1.8
    dead_cars.append(cv)
    # H1: acquires lock_h first, then tries lock_v
    start_thread(DeadThread(ch, dead_lock_h, dead_lock_v, sx(0.46), sy(0.50)))
    # H2: acquires lock_v first, then tries lock_h -> DEADLOCK
    start_thread(DeadThread(cv, dead_lock_v, dead_lock_h, sx(0.50), sy(0.46)))

def render_deadlock():
    global mode_info
    for c in dead_cars:
        c.step()

    both_stuck = all(c.state == "stuck" for c in dead_cars)

    if both_stuck:
        pulse = abs(sin(frameCount * 0.05)) * 100
        noStroke()
        fill(255, 0, 0, 30 + pulse)
        ellipse(sx(0.48), sy(0.48), 90, 90)

        fill(0, 0, 0, 200)
        noStroke()
        rect(sx(0.20), sy(0.28), 130, 36, 5)
        rect(sx(0.56), sy(0.18), 130, 36, 5)
        textSize(10)
        fill(255, 100, 100)
        textAlign(CENTER, CENTER)
        text("H1: lock_h.acquire() OK\nlock_v.acquire() BLOCKED", sx(0.20) + 65, sy(0.28) + 18)
        fill(100, 150, 255)
        text("H2: lock_v.acquire() OK\nlock_h.acquire() BLOCKED", sx(0.56) + 65, sy(0.18) + 18)

        fill(255, 60, 60)
        textSize(20)
        text("DEADLOCK", sx(0.48), sy(0.75))
        textAlign(LEFT)

    for c in dead_cars:
        c.show()

    if both_stuck:
        mode_info = "DEADLOCK DETECTADO!\nH1: tiene lock_h, espera lock_v\nH2: tiene lock_v, espera lock_h\nNinguno puede avanzar"
    else:
        mode_info = "Adquiriendo recursos...\nH1 -> lock_h (Puente H)\nH2 -> lock_v (Puente V)"


# ==============================================
# RENDER MODE 6: CONCURRENCIA
# ==============================================
def init_concurrencia():
    global conc_cars
    stop_threads()
    conc_cars = []
    lanes_y = [sy(0.10), sy(0.27), sy(0.44), sy(0.58), sy(0.73), sy(0.90)]
    speeds = [1.8, 2.5, 1.5, 3.0, 2.2, 1.2]
    for i in range(6):
        c = Car(sx(-0.05 - py_random.uniform(0, 0.3)), lanes_y[i], ALL_COLORS[i], "H" + str(i + 1))
        c.spd = speeds[i]
        c.lane_y = lanes_y[i]
        conc_cars.append(c)
        start_thread(ConcThread(c))

def render_concurrencia():
    global mode_info
    for c in conc_cars:
        c.step()

    textSize(10)
    fill(255, 255, 255, 120)
    textAlign(LEFT)
    for i, c in enumerate(conc_cars):
        text("Carril " + str(i + 1), sx(0.01), c.lane_y - 20)

    for c in conc_cars:
        c.show()

    mode_info = "Hilos activos: 6\nCada Thread en su carril\nVelocidades independientes\nSin recursos compartidos"


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
    global current_mode, sem_max, sec_protected

    if key in '1234567':
        new_mode = int(key) - 1
        init_mode(new_mode)
        return

    if key == ' ':
        init_mode(current_mode)
        return

    if current_mode == 0:
        if keyCode == UP:
            sem_max = min(5, sem_max + 1)
            init_semaforo()
        elif keyCode == DOWN:
            sem_max = max(1, sem_max - 1)
            init_semaforo()

    if current_mode == 3:
        if key == ENTER or key == RETURN:
            sec_protected[0] = not sec_protected[0]
            init_seccion_critica()
