import simpy
import random
import pandas as pd
import pygame
import sys
import ttkbootstrap as tb
from tkinter import ttk
from tkinter import messagebox
import math

global_event_log = []


def generate_arrivals(env, arrival_rate_per_hour, total_clients, cashiers, service_time_in_hours):
    for client_id in range(1, total_clients + 1):
        time_between_arrivals = random.expovariate(arrival_rate_per_hour)
        yield env.timeout(time_between_arrivals)

        print(f"Tiempo {env.now:.2f}: Cliente {client_id} llegó y se formó.")
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
        print(f"Time {env.now:.2f}: {client_name} está siendo atendido.")
        global_event_log.append({
            "Time": env.now,
            "Client_ID": int(client_name.split(' ')[1]),
            "Event": "Service_Start"
        })

        actual_service_time = random.expovariate(1.0 / service_time_in_hours)
        yield env.timeout(actual_service_time)

        print(f"Time {env.now:.2f}: {client_name} pagó y se fue.")
        global_event_log.append({
            "Time": env.now,
            "Client_ID": int(client_name.split(' ')[1]),
            "Event": "Exit"
        })


def run_simulation(num_cashiers, total_clients, lambda_val, mu_val):
    """Configures and runs the SimPy environment. Returns the log as a DataFrame."""
    global global_event_log
    global_event_log = []
    print(f"\n[PASO 1/2] Corriendo simulación matemática (SimPy)...")
    env = simpy.Environment()
    print(f"Modelo de colas tipo M/M/{num_cashiers} inicializado.")
    cashiers = simpy.Resource(env, capacity=num_cashiers)

    service_time_in_hours = 1.0 / mu_val

    env.process(generate_arrivals(env, lambda_val, total_clients, cashiers, service_time_in_hours))
    env.run()
    print("Simulación matemática completada.")
    if not global_event_log:
        return None
    return pd.DataFrame(global_event_log)



WIDTH, HEIGHT = 800, 600
TITLE = "Visualizador de Colas - Tienda Ara"  # <--- Texto en Español
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_ARA = (0, 105, 55)
RED_ARA = (228, 0, 43)
CLIENT_COLOR = (50, 150, 255)
QUEUE_START_POS = (400, 500)
QUEUE_SPACING_Y = -25


def run_visualizer(events_df, num_active_cashiers):
    if events_df is None or events_df.empty:
        print("No hay eventos para visualizar. Saliendo.")
        return
    print(f"[PASO 2/2] Iniciando visualización (Pygame)...")

    cashier_positions = [(200 + i * 100, 50) for i in range(num_active_cashiers)]
    cashier_states = {i: "free" for i in range(num_active_cashiers)}

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 30)
    clients, simulation_time, simulation_speed = {}, 0.0, 5.0
    current_event_index, num_events = 0, len(events_df)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        dt_seconds = clock.get_time() / 1000.0
        simulation_time += dt_seconds * simulation_speed
        while current_event_index < num_events:
            event = events_df.iloc[current_event_index]
            if event['Time'] <= simulation_time:
                client_id, event_type = event['Client_ID'], event['Event']
                if event_type == "Arrival":
                    clients_in_queue = event['Clients_in_Queue']
                    pos_x, pos_y = QUEUE_START_POS[0], QUEUE_START_POS[1] + (clients_in_queue * QUEUE_SPACING_Y)
                    clients[client_id] = {"id": client_id, "pos": (pos_x, pos_y), "state": "in_queue", "cashier_id": -1}
                elif event_type == "Service_Start":
                    assigned_cashier = -1
                    for i in range(num_active_cashiers):
                        if cashier_states[i] == "free":
                            cashier_states[i], assigned_cashier = client_id, i
                            break
                    if assigned_cashier != -1:
                        clients[client_id]["pos"] = cashier_positions[assigned_cashier]
                        clients[client_id]["state"], clients[client_id]["cashier_id"] = "at_cashier", assigned_cashier
                elif event_type == "Exit":
                    cashier_id = clients[client_id]["cashier_id"]
                    if cashier_id != -1:
                        cashier_states[cashier_id] = "free"
                    del clients[client_id]
                current_event_index += 1
            else:
                break
        screen.fill(WHITE)
        for i in range(num_active_cashiers):
            pos = cashier_positions[i]
            cashier_color = RED_ARA if cashier_states[i] != "free" else GREEN_ARA
            cashier_text = font.render(f"Caja {i + 1}", True, BLACK)  # <--- Texto en Español
            screen.blit(cashier_text, (pos[0] - 30, pos[1] + 20))
            pygame.draw.rect(screen, cashier_color, (pos[0] - 30, pos[1] - 10, 60, 20))

        for client_id, client_info in clients.items():
            pos = client_info["pos"]
            pygame.draw.circle(screen, CLIENT_COLOR, (int(pos[0]), int(pos[1])), 10)

        clock_text_str = f"Tiempo: {int(simulation_time // 60):02d}:{int(simulation_time % 60):02d}"  # <--- Texto en Español
        clock_image = font.render(clock_text_str, True, RED_ARA)
        screen.blit(clock_image, (10, 10))

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


    Lq = max(0, Lq)
    Ls = max(0, Ls)
    Wq = max(0, Wq)
    Ws = max(0, Ws)

    return {"rho": rho, "Lq": Lq, "Wq": Wq, "Ls": Ls, "Ws": Ws, "Po": Po}


def format_time(decimal_hours):
    """Converts a decimal hour value into a readable string (in Spanish)."""
    # --- NUEVA VALIDACIÓN ---
    # Si es 0 o negativo, muestra "0 segundos"
    if decimal_hours <= 0:
        return "0 segundos"

    total_seconds = int(decimal_hours * 3600)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours} horas, {minutes} minutos, {seconds} segundos"
    elif minutes > 0:
        return f"{minutes} minutos, {seconds} segundos"
    else:
        return f"{seconds} segundos"



class App(tb.Window):
    def __init__(self):
        super().__init__(themename="solar")
        self.title("Sistema de simulación del Servicio de Cajas en Tiendas Ara")  # <--- Español
        self.geometry("600x550")

        # 1. Main Title
        title_label = ttk.Label(self, text="Sistema de simulación el Servicio de Cajas en Tiendas Ara",  # <--- Español
                                font=("Georgia", 16, "bold"), wraplength=550, justify="center")
        title_label.pack(pady=20, padx=20)

        # 2. Configuration Card
        config_frame = ttk.Labelframe(self, text="Parámetros del Sistema", bootstyle="warning",
                                      padding=20)  # <--- Español
        config_frame.pack(fill="x", pady=10, padx=20)

        # --- Row 1: Server (Cashier) Configuration ---
        cashiers_label = ttk.Label(config_frame, text="Número de cajeros activos (s):")  # <--- Español
        cashiers_label.grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.cashiers_combo = ttk.Combobox(config_frame, values=["1", "2", "3", "4"], state="readonly", width=10)
        self.cashiers_combo.set("1")
        self.cashiers_combo.grid(row=0, column=1, padx=5, pady=10)

        # --- Row 2: Client (Limit) Configuration ---
        clients_label = ttk.Label(config_frame, text="Clientes totales a simular:")  # <--- Español
        clients_label.grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.clients_combo = ttk.Combobox(config_frame, values=[str(i) for i in range(1, 16)], state="readonly",
                                          width=10)
        self.clients_combo.set("15")
        self.clients_combo.grid(row=1, column=1, padx=5, pady=10)

        # --- Row 3: Arrival (Lambda) Configuration ---
        arrival_label = ttk.Label(config_frame, text="Tiempo PROMEDIO entre llegadas:")  # <--- Español
        arrival_label.grid(row=2, column=0, padx=5, pady=10, sticky="w")
        self.arrival_spinbox = ttk.Spinbox(config_frame, from_=0.01, to=1000.0, increment=0.1, width=10)
        self.arrival_spinbox.set("5")
        self.arrival_spinbox.grid(row=2, column=1, padx=5, pady=10)

        self.arrival_unit_combo = ttk.Combobox(config_frame, values=["Segundos", "Minutos", "Horas"], state="readonly",
                                               width=10)  # <--- Español
        self.arrival_unit_combo.set("Minutos")
        self.arrival_unit_combo.grid(row=2, column=2, padx=5, pady=10)

        # --- Row 4: Service (Mu) Configuration ---
        service_label = ttk.Label(config_frame, text="Tiempo PROMEDIO de servicio:")  # <--- Español
        service_label.grid(row=3, column=0, padx=5, pady=10, sticky="w")
        self.service_spinbox = ttk.Spinbox(config_frame, from_=0.01, to=1000.0, increment=0.1, width=10)
        self.service_spinbox.set("3")
        self.service_spinbox.grid(row=3, column=1, padx=5, pady=10)

        self.service_unit_combo = ttk.Combobox(config_frame, values=["Segundos", "Minutos", "Horas"], state="readonly",
                                               width=10)  # <--- Español
        self.service_unit_combo.set("Minutos")
        self.service_unit_combo.grid(row=3, column=2, padx=5, pady=10)

        # 5. Simulation Button
        self.start_button = ttk.Button(self, text="Hacer simulación", command=self.start_simulation,
                                       bootstyle="warning-outline", width=25)  # <--- Español
        self.start_button.pack(pady=30)

    def start_simulation(self):
        try:
            # 1. Get values from the GUI
            s_val = int(self.cashiers_combo.get())
            total_clients = int(self.clients_combo.get())
            arrival_val = float(self.arrival_spinbox.get())
            arrival_unit = self.arrival_unit_combo.get()
            service_val = float(self.service_spinbox.get())
            service_unit = self.service_unit_combo.get()

            if arrival_val <= 0 or service_val <= 0:
                messagebox.showerror("Error de Entrada", "Los tiempos de llegada y servicio deben ser mayores que 0.")
                return

            # 2. Convert Times to HOURLY Rates
            if arrival_unit == "Segundos":
                time_between_arrivals_hours = arrival_val / 3600
            elif arrival_unit == "Minutos":
                time_between_arrivals_hours = arrival_val / 60
            else:  # Horas
                time_between_arrivals_hours = arrival_val
            lambda_val = 1.0 / time_between_arrivals_hours

            if service_unit == "Segundos":
                service_time_hours = service_val / 3600
            elif service_unit == "Minutos":
                service_time_hours = service_val / 60
            else:  # Horas
                service_time_hours = service_val
            mu_val = 1.0 / service_time_hours

            # 3. Validate System Stability
            if lambda_val >= (s_val * mu_val):
                # Mensaje de error en Español
                messagebox.showerror("Sistema Inestable",
                                     f"Error: La tasa de llegada (λ ≈ {lambda_val:.2f} cl/hr) es mayor o igual a la tasa de servicio total (s*μ ≈ {s_val * mu_val:.2f} cl/hr).\n\n"
                                     "El sistema es INESTABLE (ρ >= 1) y la cola crecería infinitamente.\n\n"
                                     "Por favor, aumente el número de cajeros o el tiempo de servicio.")
                return

                # 4. Calculate Theoretical Metrics
            metrics = calculate_metrics(lambda_val, mu_val, s_val)
            if not metrics:
                messagebox.showerror("Error",
                                     "No se pudieron calcular las métricas. Revise los parámetros.")  # <--- Español
                return

            # 5. Create and Show Results Popup Window
            # Mensaje de resultados
            results_string = (
                f"--- Resultados Teóricos del Modelo M/M/{s_val} ---\n\n"
                f"Parámetros del Sistema:\n"
                f"  λ (Tasa de Llegada): {lambda_val:.2f} clientes/hora\n"
                f"  μ (Tasa de Servicio): {mu_val:.2f} clientes/hora\n"
                f"  s (Servidores): {s_val}\n\n"
                f"Métricas de Rendimiento:\n"
                f"  ρ (Factor de Utilización): {metrics['rho'] * 100:.2f} %\n"
                f"  Po (Prob. Sistema Vacío): {metrics['Po'] * 100:.2f} %\n\n"
                f"  Lq (Clientes en Cola): {metrics['Lq']:.2f} clientes\n"
                f"  Ls (Clientes en Sistema): {metrics['Ls']:.2f} clientes\n\n"
                f"  Wq (Tiempo en Cola): {format_time(metrics['Wq'])}\n"
                f"  Ws (Tiempo en Sistema): {format_time(metrics['Ws'])}\n"
            )

            messagebox.showinfo("Resultados Teóricos de la Simulación", results_string)  

            # 6. If all is well, close the menu and run the simulation
            self.destroy()  # Closes the menu window

            # --- CALL THE SIMULATION CODE  ---
            event_log = run_simulation(s_val, total_clients, lambda_val, mu_val)

            # --- CALL THE VISUALIZATION  ---
            run_visualizer(event_log, s_val)

        except ValueError:
            messagebox.showerror("Error de Entrada",
                                 "Por favor, ingrese solo números válidos en los campos de tiempo.")
        except KeyboardInterrupt:
            print("Simulación cancelada.")


if __name__ == "__main__":
    app = App()
    app.mainloop()