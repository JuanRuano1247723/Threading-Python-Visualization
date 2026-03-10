# ==============================
# SRTF - Visualizador Interactivo
# Processing (Python Mode)
# ==============================
import threading


procesos = []
timeline = []
running = None
current_time = 0
last_update = 0
interval = 450
simulation_started = False
simulation_running = False

active_field = None

class Proceso:
    def __init__(self, pid, llegada, rafaga):
        self.pid = pid
        self.llegada = int(llegada)
        self.rafaga = int(rafaga)
        self.restante = int(rafaga)
        self.finalizado = False

class InputBox:
    def __init__(self, x, y, w, h, label):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = ""
        self.label = label

    def draw(self):
        fill(255)
        stroke(0)
        rect(self.x, self.y, self.w, self.h)
        fill(0)
        text(self.label, self.x, self.y - 5)
        text(self.text, self.x + 5, self.y + 20)

    def clicked(self, mx, my):
        return self.x < mx < self.x+self.w and self.y < my < self.y+self.h

pid_box = InputBox(20, 50, 100, 30, "ID")
llegada_box = InputBox(140, 50, 100, 30, "Llegada")
rafaga_box = InputBox(260, 50, 100, 30, "Rafaga")

def setup():
    size(1000, 600)
    textSize(14)

def draw():
    global last_update, current_time, running, simulation_started, simulation_running

    background(240)

    fill(0)
    text("SRTF - Short Remaining Time First", 20, 20)
    text("Velocidad: {} ms por unidad".format(interval), 20, 430)

    pid_box.draw()
    llegada_box.draw()
    rafaga_box.draw()

    draw_buttons()
    draw_process_list()
    draw_timeline()
    draw_speed_controls()

    if simulation_started and simulation_running:
        # Verificar si todos los procesos han finalizado
        if all(p.finalizado for p in procesos):
            simulation_running = False
            text("SIMULACIÓN COMPLETADA", 500, 380)
        elif millis() - last_update > interval:
            last_update = millis()
            simulate_step()

def draw_speed_controls():
    # Botón más rápido (-)
    fill(200, 200, 200)
    rect(200, 410, 40, 30)
    fill(0)
    textSize(20)
    text("-", 215, 435)
    
    # Botón más lento (+)
    rect(250, 410, 40, 30)
    text("+", 265, 435)
    textSize(14)

def draw_buttons():
    # Agregar proceso
    fill(100, 200, 100)
    rect(400, 50, 120, 30)
    fill(0)
    text("Agregar proceso", 410, 70)

    # Iniciar
    fill(100, 150, 255)
    rect(540, 50, 100, 30)
    fill(0)
    text("Iniciar", 570, 70)
    
    # Parar
    fill(255, 80, 80)
    rect(660, 50, 100, 30)
    fill(0)
    text("Parar", 695, 70)

    # Limpiar
    fill(255, 100, 100)
    rect(780, 50, 100, 30)
    fill(0)
    text("Limpiar", 810, 70)

def draw_process_list():
    fill(0)
    text("Procesos:", 20, 120)
    y = 140
    for p in procesos:
        estado = "C" if p.finalizado else "E"
        text("P{} | Llegada:{} | Rafaga:{} | Restante:{} {}".format(
            p.pid, p.llegada, p.rafaga, p.restante, estado), 20, y)
        y += 20

def draw_timeline():
    fill(0)
    text("Timeline:", 20, 300)

    x = 20
    y = 320
    max_width = width - 40
    
    for i, t in enumerate(timeline):
        if x > max_width:
            text("...", x, y+25)
            break
        fill(color_from_id(t))
        rect(x, y, 30, 40)
        fill(0)
        text("P{}".format(t), x+5, y+25)
        x += 32

    fill(0)
    text("Tiempo actual: {}".format(current_time), 20, 380)
    
    if simulation_running:
        fill(0, 150, 0)
        text("▶ SIMULANDO", 20, 400)
    elif simulation_started and all(p.finalizado for p in procesos):
        fill(150, 150, 0)
        text("■ COMPLETADA", 20, 400)

def simulate_step():
    global current_time, running

    disponibles = [p for p in procesos if p.llegada <= current_time and not p.finalizado]

    if disponibles:
        running = min(disponibles, key=lambda p: p.restante)
        running.restante -= 1
        timeline.append(running.pid)

        if running.restante == 0:
            running.finalizado = True
    else:
        timeline.append(0)

    current_time += 1

def mousePressed():
    global active_field, simulation_started, simulation_running, current_time, timeline, interval

    # Check input boxes
    if pid_box.clicked(mouseX, mouseY):
        active_field = pid_box
    elif llegada_box.clicked(mouseX, mouseY):
        active_field = llegada_box
    elif rafaga_box.clicked(mouseX, mouseY):
        active_field = rafaga_box
    else:
        active_field = None

    # Agregar proceso
    if 400 < mouseX < 520 and 50 < mouseY < 80:
        if pid_box.text and llegada_box.text and rafaga_box.text:
            procesos.append(Proceso(
                pid_box.text,
                llegada_box.text,
                rafaga_box.text
            ))
            pid_box.text = ""
            llegada_box.text = ""
            rafaga_box.text = ""

    # Iniciar
    if 540 < mouseX < 640 and 50 < mouseY < 80:
        if procesos and not simulation_running:
            # Resetear procesos si es necesario
            if simulation_started and all(p.finalizado for p in procesos):
                for p in procesos:
                    p.restante = p.rafaga
                    p.finalizado = False
                current_time = 0
                timeline = []
            
            simulation_started = True
            simulation_running = True
            last_update = millis()
    
    # Parar
    if 660 < mouseX < 760 and 50 < mouseY < 80:
        simulation_running = False

    # Limpiar
    if 780 < mouseX < 880 and 50 < mouseY < 80:
        if not simulation_running:
            procesos[:] = []
            timeline[:] = []
            current_time = 0
            simulation_started = False
            simulation_running = False
    
    # Control de velocidad - más rápido (-)
    if 200 < mouseX < 240 and 410 < mouseY < 440:
        interval = max(100, interval - 50)
    
    # Control de velocidad - más lento (+)
    if 250 < mouseX < 290 and 410 < mouseY < 440:
        interval = min(2000, interval + 50)

def keyPressed():
    if active_field:
        if key == BACKSPACE:
            active_field.text = active_field.text[:-1]
        elif key != CODED:
            active_field.text += key

def color_from_id(pid):
    try:
        pid = int(pid)
    except:
        return color(200)

    if pid == 0:
        return color(200)

    return color((pid*50)%255, (pid*80)%255, (pid*110)%255)
