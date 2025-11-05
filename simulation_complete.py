import simpy
import random
import pandas as pd
import pygame
import sys
import ttkbootstrap as tb
from tkinter import ttk
from tkinter import messagebox
import math
import os


# --- PARA PYINSTALLER ---
def resource_path(relative_path):

    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:

        base_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    return os.path.join(base_path, relative_path)




# --- MODULE 1: SIMULATION LOGIC  ---

global_event_log = []


def generate_arrivals(env, arrival_rate_per_hour, total_clients, cashiers, service_time_in_hours):
    for client_id in range(1, total_clients + 1):
        time_between_arrivals = random.expovariate(arrival_rate_per_hour)
        yield env.timeout(time_between_arrivals)
        global_event_log.append({
            "Time": env.now,
            "Client_ID": client_id,
            "Event": "Arrival",
            "Clients_in_Queue": len(cashiers.queue)
        })
        env.process(serve_client(env, f"Cliente {client_id}", cashiers, service_time_in_hours))


def serve_client(env, client_name, cashiers, service_time_in_hours):
    with cashiers.request() as req:
        yield req
        global_event_log.append({
            "Time": env.now,
            "Client_ID": int(client_name.split(' ')[1]),
            "Event": "Service_Start"
        })
        actual_service_time = random.expovariate(1.0 / service_time_in_hours)
        yield env.timeout(actual_service_time)
        global_event_log.append({
            "Time": env.now,
            "Client_ID": int(client_name.split(' ')[1]),
            "Event": "Exit"
        })


def run_simulation(num_cashiers, total_clients, lambda_val, mu_val):
    global global_event_log
    global_event_log = []
    print(f"\n[SIMPY] Corriendo simulación M/M/{num_cashiers}...")
    env = simpy.Environment()
    cashiers = simpy.Resource(env, capacity=num_cashiers)
    service_time_in_hours = 1.0 / mu_val
    env.process(generate_arrivals(env, lambda_val, total_clients, cashiers, service_time_in_hours))
    env.run()
    print("[SIMPY] Simulación completada.")
    if not global_event_log:
        return None
    return pd.DataFrame(global_event_log)


# --- MODULE 2: VISUALIZATION LOGIC  ---

NATIVE_WIDTH, NATIVE_HEIGHT = 1536, 1024
SCALE_FACTOR = 0.75
SCREEN_WIDTH = int(NATIVE_WIDTH * SCALE_FACTOR)
SCREEN_HEIGHT = int(NATIVE_HEIGHT * SCALE_FACTOR)

TITLE = "Visualizador de Colas - Tienda Ara"
FPS = 60
BLACK = (0, 0, 0)
GREEN_STATUS = (0, 255, 0, 150)
RED_STATUS = (255, 0, 0, 150)

IMAGE_PATH = "Imagenes"
BG_IMAGE_FILE = resource_path(os.path.join(IMAGE_PATH, "Fondo.png"))
CASHIER_IMAGE_FILE = resource_path(os.path.join(IMAGE_PATH, "Empleado con sombrero rojo pixelado.png"))
CUSTOMER_M_IMAGE_FILE = resource_path(os.path.join(IMAGE_PATH, "Captura de pantalla 2025-10-31 083808.png"))
CUSTOMER_F_IMAGE_FILE = resource_path(os.path.join(IMAGE_PATH, "Cliente mujer.png"))



CASHIER_POSITIONS = [
    (1130, 750),
    (1280, 750),
    (1130, 580),
    (1280, 580)
]
CUSTOMER_AT_CASHIER_POS = [
    (1130, 820),
    (1280, 820),
    (1130, 650),
    (1280, 650)
]
QUEUE_START_POS = (750, 850)
EXIT_POS = (1450, 200)
QUEUE_SPACING_Y = -80
STATUS_INDICATOR_POS = [
    (1130, 730),
    (1280, 730),
    (1130, 560),
    (1280, 560)
]

def run_visualizer(events_df, num_active_cashiers):
    if events_df is None or events_df.empty:
        messagebox.showinfo("Sin datos", "No hay eventos para visualizar.")
        return

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    drawing_surface = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    try:
        BACKGROUND_IMG = pygame.image.load(BG_IMAGE_FILE).convert()
        BACKGROUND_IMG = pygame.transform.scale(BACKGROUND_IMG, (NATIVE_WIDTH, NATIVE_HEIGHT))

        CASHIER_IMG = pygame.image.load(CASHIER_IMAGE_FILE).convert_alpha()
        CASHIER_IMG = pygame.transform.scale(CASHIER_IMG, (70, 110))


        CUSTOMER_M_IMG = pygame.image.load(CUSTOMER_M_IMAGE_FILE).convert_alpha()
        CUSTOMER_M_IMG = pygame.transform.scale(CUSTOMER_M_IMG, (50, 80))

        CUSTOMER_F_IMG = pygame.image.load(CUSTOMER_F_IMAGE_FILE).convert_alpha()
        CUSTOMER_F_IMG = pygame.transform.scale(CUSTOMER_F_IMG, (50, 80))

        CUSTOMER_IMAGES = [CUSTOMER_M_IMG, CUSTOMER_F_IMG]
    except Exception as e:
        messagebox.showerror("Error de carga", f"No se pudo cargar alguna imagen: {e}")
        return

    cashier_states = {i: "free" for i in range(num_active_cashiers)}
    clients = {}
    simulation_time = 0.0
    simulation_speed_factor = 1.0
    current_event_index, num_events = 0, len(events_df)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        dt_seconds = clock.get_time() / 1000.0
        sim_minutes_passed = dt_seconds * simulation_speed_factor
        simulation_time += sim_minutes_passed / 60.0

        while current_event_index < num_events:
            event = events_df.iloc[current_event_index]
            if event['Time'] <= simulation_time:
                client_id, event_type = event['Client_ID'], event['Event']

                if event_type == "Arrival":
                    clients_in_queue = event['Clients_in_Queue']
                    pos_x = QUEUE_START_POS[0]
                    pos_y = QUEUE_START_POS[1] + (clients_in_queue * QUEUE_SPACING_Y)
                    client_image = random.choice(CUSTOMER_IMAGES)
                    clients[client_id] = {
                        "pos": (pos_x, pos_y),
                        "target": None,
                        "cashier_id": -1,
                        "image": client_image,
                        "leaving": False
                    }

                elif event_type == "Service_Start":
                    assigned_cashier = -1
                    for i in range(num_active_cashiers):
                        if cashier_states[i] == "free":
                            cashier_states[i] = client_id
                            assigned_cashier = i
                            break
                    if assigned_cashier != -1:
                        clients[client_id]["target"] = CUSTOMER_AT_CASHIER_POS[assigned_cashier]
                        clients[client_id]["cashier_id"] = assigned_cashier

                elif event_type == "Exit":
                    cashier_id = clients[client_id]["cashier_id"]
                    if cashier_id != -1:
                        cashier_states[cashier_id] = "free"
                    clients[client_id]["target"] = EXIT_POS
                    clients[client_id]["leaving"] = True

                current_event_index += 1
            else:
                break

        # Movimiento suave
        for client_id, info in list(clients.items()):
            if info["target"] is not None:
                current_x, current_y = info["pos"]
                target_x, target_y = info["target"]
                dx, dy = target_x - current_x, target_y - current_y
                distance = math.hypot(dx, dy)
                if distance > 2:
                    step = 5
                    info["pos"] = (
                        current_x + dx / distance * step,
                        current_y + dy / distance * step
                    )
                else:
                    info["pos"] = info["target"]
                    if info["leaving"]:
                        del clients[client_id]

        drawing_surface.blit(BACKGROUND_IMG, (0, 0))

        for i in range(num_active_cashiers):
            drawing_surface.blit(CASHIER_IMG, CASHIER_POSITIONS[i])
            color = GREEN_STATUS if cashier_states[i] == "free" else RED_STATUS
            pygame.draw.circle(drawing_surface, color, STATUS_INDICATOR_POS[i], 10)

        for client_id, info in clients.items():
            drawing_surface.blit(info["image"], info["pos"])

        total_sim_minutes = simulation_time * 60
        sim_minutes_display = int(total_sim_minutes)
        sim_seconds_display = int((total_sim_minutes * 60) % 60)
        clock_text_str = f"Tiempo: {sim_minutes_display:02d}:{sim_seconds_display:02d}"
        clock_image = font.render(clock_text_str, True, BLACK)
        drawing_surface.blit(clock_image, (30, 30))

        screen.fill(BLACK)
        scaled_surface = pygame.transform.scale(drawing_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


def calculate_metrics(lambda_val, mu_val, s_val):
    rho = lambda_val / (s_val * mu_val)
    if s_val == 1:
        if rho >= 1:
            return None
        Ls = rho / (1 - rho)
        Lq = (lambda_val ** 2) / (mu_val * (mu_val - lambda_val))
        Ws = 1 / (mu_val - lambda_val)
        Wq = lambda_val / (mu_val * (mu_val - lambda_val))
        Po = 1 - rho
    else:
        if rho >= 1:
            return None
        sum_part = 0
        for n in range(s_val):
            sum_part += (math.pow(lambda_val / mu_val, n)) / math.factorial(n)
        last_part = (math.pow(lambda_val / mu_val, s_val) / math.factorial(s_val)) * (1 / (1 - rho))
        Po = 1 / (sum_part + last_part)
        Lq = (Po * math.pow(lambda_val / mu_val, s_val) * rho) / (math.factorial(s_val) * math.pow(1 - rho, 2))
        Wq = Lq / lambda_val
        Ws = Wq + (1 / mu_val)
        Ls = lambda_val * Ws
    return {"rho": rho, "Lq": Lq, "Wq": Wq, "Ls": Ls, "Ws": Ws, "Po": Po}


def format_time(decimal_hours):
    if decimal_hours <= 0:
        return "0 segundos"
    total_seconds = int(decimal_hours * 3600)
    # Corrección: Uso de 'divmod' (sin guion bajo)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


# --- INTERFAZ PRINCIPAL (TTKBOOTSTRAP) ---

class App(tb.Window):
    def __init__(self):
        super().__init__(themename="solar")
        self.title("Simulación del Servicio de Cajas - Tienda Ara")
        self.geometry("600x550")

        ttk.Label(self, text="Sistema de Simulación del Servicio de Cajas en Tienda Ara",
                  font=("Georgia", 16, "bold"), wraplength=550, justify="center").pack(pady=20)

        config_frame = ttk.Labelframe(self, text="Parámetros del Sistema", bootstyle="warning", padding=20)
        config_frame.pack(fill="x", pady=10, padx=20)

        ttk.Label(config_frame, text="Número de cajeros (s):").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.cashiers_combo = ttk.Combobox(config_frame, values=["1", "2", "3", "4"], state="readonly", width=10)
        self.cashiers_combo.set("2")
        self.cashiers_combo.grid(row=0, column=1, padx=5, pady=10)

        ttk.Label(config_frame, text="Clientes a simular:").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.clients_combo = ttk.Combobox(config_frame, values=[str(i) for i in range(5, 31)], state="readonly",
                                          width=10)
        self.clients_combo.set("15")
        # Corrección: El valor de pady debe ser un número (10), no una letra (1O)
        self.clients_combo.grid(row=1, column=1, padx=5, pady=10)  # <-- Línea 328 corregida

        ttk.Label(config_frame, text="Tiempo entre llegadas:").grid(row=2, column=0, padx=5, pady=10, sticky="w")
        self.arrival_spin = ttk.Spinbox(config_frame, from_=0.1, to=1000, increment=0.1, width=10)
        self.arrival_spin.set("5")
        self.arrival_spin.grid(row=2, column=1)
        self.arrival_unit = ttk.Combobox(config_frame, values=["Segundos", "Minutos", "Horas"], state="readonly",
                                         width=10)
        self.arrival_unit.set("Minutos")
        self.arrival_unit.grid(row=2, column=2)

        ttk.Label(config_frame, text="Tiempo de servicio:").grid(row=3, column=0, padx=5, pady=10, sticky="w")
        self.service_spin = ttk.Spinbox(config_frame, from_=0.1, to=1000, increment=0.1, width=10)
        self.service_spin.set("3")
        self.service_spin.grid(row=3, column=1)
        self.service_unit = ttk.Combobox(config_frame, values=["Segundos", "Minutos", "Horas"], state="readonly",
                                         width=10)
        self.service_unit.set("Minutos")
        self.service_unit.grid(row=3, column=2)

        ttk.Button(self, text="Iniciar Simulación", command=self.start_simulation,
                   bootstyle="warning-outline", width=25).pack(pady=30)

    def start_simulation(self):
        try:
            s_val = int(self.cashiers_combo.get())
            total_clients = int(self.clients_combo.get())
            arrival_val = float(self.arrival_spin.get())
            service_val = float(self.service_spin.get())
            arrival_unit = self.arrival_unit.get()
            service_unit = self.service_unit.get()

            arrival_hours = arrival_val / (
                3600 if arrival_unit == "Segundos" else 60 if arrival_unit == "Minutos" else 1)
            service_hours = service_val / (
                3600 if service_unit == "Segundos" else 60 if service_unit == "Minutos" else 1)
            lambda_val = 1 / arrival_hours
            mu_val = 1 / service_hours

            if lambda_val >= (s_val * mu_val):
                messagebox.showerror("Sistema Inestable", "ρ ≥ 1. Aumenta cajeros o reduce llegadas.")
                return

            metrics = calculate_metrics(lambda_val, mu_val, s_val)
            if not metrics:
                messagebox.showerror("Error", "No se pudieron calcular las métricas.")
                return

            results = (
                f"--- Resultados Teóricos ---\n\n"
                f"ρ = {metrics['rho'] * 100:.2f}%\n"
                f"Po = {metrics['Po'] * 100:.2f}%\n"
                f"Lq = {metrics['Lq']:.2f}\nLs = {metrics['Ls']:.2f}\n"
                f"Wq = {format_time(metrics['Wq'])}\nWs = {format_time(metrics['Ws'])}"
            )
            messagebox.showinfo("Resultados", results)

            self.destroy()
            df = run_simulation(s_val, total_clients, lambda_val, mu_val)
            run_visualizer(df, s_val)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()