import simpy
import random
import pandas as pd
import pygame
import sys


global_event_log = []


def generate_arrivals(env, arrival_rate, total_clients, cashiers, service_time):


    for client_id in range(1, total_clients + 1):
        yield env.timeout(random.expovariate(arrival_rate / 60))

        print(f"Time {env.now:.2f}: Client {client_id} arrived and queued.")
        global_event_log.append({
            "Time": env.now,
            "ID_Cliente": client_id,
            "Event": "Arrival",
            "Clients_in_Queue": len(cashiers.queue)
        })

        # 3. Send the client to the service process
        env.process(serve_client(env, f"Client {client_id}", cashiers, service_time))


def serve_client(env, client_name, cashiers, service_time):
    with cashiers.request() as req:
        # 4. Wait in line until a cashier is free
        yield req

        # 5. Log the start of service
        print(f"Time {env.now:.2f}: {client_name} is being served.")
        global_event_log.append({
            "Time": env.now,
            "ID_Cliente": int(client_name.split(' ')[1]),
            "Event": "Service_Start"
        })

        yield env.timeout(service_time)


        print(f"Time {env.now:.2f}: {client_name} finished and left.")
        global_event_log.append({
            "Time": env.now,
            "ID_Cliente": int(client_name.split(' ')[1]),
            "Event": "Exit"
        })


def run_simulation(num_cashiers, total_clients, clients_per_hour, service_time_min):

    global global_event_log
    global_event_log = []

    print(f"\n[PASO 1/2] Ejecutar la simulación matemática (SimPy)...")
    env = simpy.Environment()

    print(f"Modelo de colas M/M/{num_cashiers} inicializado.")
    cashiers = simpy.Resource(env, capacity=num_cashiers)

    arrival_rate = clients_per_hour

    env.process(generate_arrivals(env, arrival_rate, total_clients, cashiers, service_time_min))

    env.run()

    print("Simulación matemática completada.")

    if not global_event_log:
        print("Advertencia: No se generaron eventos en la simulación.")
        return None

    return pd.DataFrame(global_event_log)



WIDTH, HEIGHT = 800, 600
TITLE = "Ara Store Queue Visualizer"
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

    print(f"[PASO 2/2] Iniciando la visualización (Pygame)...")


    cashier_positions = [(200 + i * 100, 50) for i in range(num_active_cashiers)]


    cashier_states = {i: "free" for i in range(num_active_cashiers)}

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 30)

    clients = {}
    simulation_time = 0.0
    simulation_speed = 5.0

    current_event_index = 0
    num_events = len(events_df)

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
                client_id = event['ID_Cliente']
                event_type = event['Event']

                if event_type == "Arrival":
                    clients_in_queue = event['Clients_in_Queue']
                    pos_x = QUEUE_START_POS[0]
                    pos_y = QUEUE_START_POS[1] + (clients_in_queue * QUEUE_SPACING_Y)
                    clients[client_id] = {"id": client_id, "pos": (pos_x, pos_y), "state": "in_queue", "cashier_id": -1}

                elif event_type == "Service_Start":
                    # --- Logic to assign to a free cashier ---
                    assigned_cashier = -1
                    for i in range(num_active_cashiers):
                        if cashier_states[i] == "free":
                            cashier_states[i] = client_id  # Occupy cashier
                            assigned_cashier = i
                            break

                    if assigned_cashier != -1:
                        clients[client_id]["pos"] = cashier_positions[assigned_cashier]
                        clients[client_id]["state"] = "at_cashier"
                        clients[client_id]["cashier_id"] = assigned_cashier

                elif event_type == "Exit":
                    cashier_id = clients[client_id]["cashier_id"]
                    if cashier_id != -1:
                        cashier_states[cashier_id] = "free"  # Free up cashier
                    del clients[client_id]

                current_event_index += 1
            else:
                break


        screen.fill(WHITE)

        # Draw the ACTIVE cashiers
        for i in range(num_active_cashiers):
            pos = cashier_positions[i]

            cashier_color = RED_ARA if cashier_states[i] != "free" else GREEN_ARA

            cashier_text = font.render(f"Cashier {i + 1}", True, BLACK)
            pygame.draw.rect(screen, cashier_color, (pos[0] - 30, pos[1] - 10, 60, 20))
            screen.blit(cashier_text, (pos[0] - 30, pos[1] + 20))

        for client_id, client_info in clients.items():
            pos = client_info["pos"]
            pygame.draw.circle(screen, CLIENT_COLOR, (int(pos[0]), int(pos[1])), 10)


        clock_text_str = f"Time: {int(simulation_time // 60):02d}:{int(simulation_time % 60):02d}"
        clock_image = font.render(clock_text_str, True, RED_ARA)
        screen.blit(clock_image, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()




def main():

    print("==================================================")
    print("    📊 Simulador de colas de la tienda Ara 📊")
    print("==================================================")


    try:

        num_cashiers = int(input(f"Ingrese el número de cajeros activos (Max {4}): "))
        if num_cashiers > 4:
            print(f"Error: El número máximo de cajeros es {4}. Se están utilizando {4}..")
            num_cashiers = 4
        elif num_cashiers <= 0:
            print("Error: Debe haber al menos 1 cajero. Se está utilizando 1.")
            num_cashiers = 1


        total_clients = int(input(f"¿Cuántos clientes en total se simularán? (Máx. {15}): "))
        if total_clients > 15:
            print(f"Error: Max clients is {15}. Simulating {15}.")
            total_clients = 15
        elif total_clients <= 0:
            print("Error: Debe haber al menos 1 cliente. Simulando 1.")
            total_clients = 1

    except ValueError:
        print("Error: Introduzca un número entero válido.")
        return
    except KeyboardInterrupt:
        return


    clients_per_hour = 85
    service_rate_per_hour = 55
    service_time_min = 60 / service_rate_per_hour


    event_log = run_simulation(num_cashiers, total_clients, clients_per_hour, service_time_min)


    run_visualizer(event_log, num_cashiers)


if __name__ == "__main__":
    main()