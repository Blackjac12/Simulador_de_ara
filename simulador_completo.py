import simpy
import random
import pandas as pd
import pygame
import sys

event_log_global = []


def generar_llegadas(env, tasa_llegada, num_clientes_totales, cajeros, tiempo_servicio):

    for id_cliente in range(1, num_clientes_totales + 1):
        # 1. Espera a que llegue el próximo cliente
        yield env.timeout(random.expovariate(tasa_llegada / 60))

        print(f"Tiempo {env.now:.2f}: Cliente {id_cliente} llegó y se formó.")
        event_log_global.append({
            "Tiempo": env.now,
            "ID_Cliente": id_cliente,
            "Evento": "Llegada",
            "Clientes_en_Fila": len(cajeros.queue)
        })

        env.process(atender_cliente(env, f"Cliente {id_cliente}", cajeros, tiempo_servicio))


def atender_cliente(env, nombre_cliente, cajeros, tiempo_servicio):
    with cajeros.request() as req:
        yield req

        event_log_global.append({
            "Tiempo": env.now,
            "ID_Cliente": int(nombre_cliente.split(' ')[1]),
            "Evento": "Inicio_Servicio"
        })

        yield env.timeout(tiempo_servicio)

        event_log_global.append({
            "Tiempo": env.now,
            "ID_Cliente": int(nombre_cliente.split(' ')[1]),
            "Evento": "Salida"
        })


def ejecutar_simulacion(num_cajeros, num_clientes_totales, clientes_por_hora, tiempo_servicio_min):

    global event_log_global
    event_log_global = []

    print(f"\n[PASO 1/2] Corriendo simulación matemática (SimPy)...")
    env = simpy.Environment()

    print(f"Modelo de colas tipo M/M/{num_cajeros} inicializado.")
    cajeros = simpy.Resource(env, capacity=num_cajeros)


    tasa_llegada = clientes_por_hora

    env.process(generar_llegadas(env, tasa_llegada, num_clientes_totales, cajeros, tiempo_servicio_min))

    env.run()

    print("Simulación matemática completada.")

    if not event_log_global:
        print("Advertencia: No se generaron eventos en la simulación.")
        return None

    return pd.DataFrame(event_log_global)

ANCHO, ALTO = 800, 600
TITULO = "Visualizador de Colas - Tienda Ara"
FPS = 60
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
VERDE_ARA = (0, 105, 55)
ROJO_ARA = (228, 0, 43)
CLIENTE_COLOR = (50, 150, 255)
POS_INICIO_FILA = (400, 500)
ESPACIO_FILA_Y = -25


def ejecutar_visualizador(eventos_df, num_cajeros_activos):

    if eventos_df is None or eventos_df.empty:
        print("No hay eventos para visualizar. Saliendo.")
        return

    print(f"[PASO 2/2] Iniciando visualización (Pygame)...")

    posiciones_cajeros = [(200 + i * 100, 50) for i in range(num_cajeros_activos)]

    estado_cajeros = {i: "libre" for i in range(num_cajeros_activos)}

    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption(TITULO)
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont(None, 30)

    clientes = {}
    tiempo_simulacion = 0.0
    velocidad_simulacion = 5.0

    indice_evento_actual = 0
    num_eventos = len(eventos_df)

    corriendo = True
    while corriendo:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                corriendo = False
        dt_segundos = reloj.get_time() / 1000.0
        tiempo_simulacion += dt_segundos * velocidad_simulacion

        while indice_evento_actual < num_eventos:
            evento = eventos_df.iloc[indice_evento_actual]
            if evento['Tiempo'] <= tiempo_simulacion:
                id_cliente = evento['ID_Cliente']
                tipo_evento = evento['Evento']

                if tipo_evento == "Llegada":
                    num_en_fila = evento['Clientes_en_Fila']
                    pos_x = POS_INICIO_FILA[0]
                    pos_y = POS_INICIO_FILA[1] + (num_en_fila * ESPACIO_FILA_Y)
                    clientes[id_cliente] = {"id": id_cliente, "pos": (pos_x, pos_y), "estado": "en_fila",
                                            "cajero_id": -1}

                elif tipo_evento == "Inicio_Servicio":
                    cajero_asignado = -1
                    for i in range(num_cajeros_activos):
                        if estado_cajeros[i] == "libre":
                            estado_cajeros[i] = id_cliente  # Ocupar cajero
                            cajero_asignado = i
                            break

                    if cajero_asignado != -1:
                        clientes[id_cliente]["pos"] = posiciones_cajeros[cajero_asignado]
                        clientes[id_cliente]["estado"] = "en_caja"
                        clientes[id_cliente]["cajero_id"] = cajero_asignado

                elif tipo_evento == "Salida":
                    cajero_id = clientes[id_cliente]["cajero_id"]
                    if cajero_id != -1:
                        estado_cajeros[cajero_id] = "libre"
                    del clientes[id_cliente]

                indice_evento_actual += 1
            else:
                break

        pantalla.fill(BLANCO)

        for i in range(num_cajeros_activos):
            pos = posiciones_cajeros[i]
            color_caja = ROJO_ARA if estado_cajeros[i] != "libre" else VERDE_ARA

            texto_caja = fuente.render(f"Caja {i + 1}", True, NEGRO)
            pygame.draw.rect(pantalla, color_caja, (pos[0] - 30, pos[1] - 10, 60, 20))
            pantalla.blit(texto_caja, (pos[0] - 30, pos[1] + 20))

        for id_cliente, info_cliente in clientes.items():
            pos = info_cliente["pos"]
            pygame.draw.circle(pantalla, CLIENTE_COLOR, (int(pos[0]), int(pos[1])), 10)

        texto_reloj = f"Tiempo: {int(tiempo_simulacion // 60):02d}:{int(tiempo_simulacion % 60):02d}"
        img_reloj = fuente.render(texto_reloj, True, ROJO_ARA)
        pantalla.blit(img_reloj, (10, 10))

        pygame.display.flip()
        reloj.tick(FPS)

    pygame.quit()
    sys.exit()



def main():
    print("==================================================")
    print("    📊 Simulador de Colas para Tiendas Ara 📊")
    print("==================================================")

    try:
        num_cajeros = int(input(f"Ingrese el número de cajeros activos (Máximo {4}): "))
        if num_cajeros > 4:
            print(f"Error: El máximo de cajeros es {4}. Se usará {4}.")
            num_cajeros = 4
        elif num_cajeros <= 0:
            print("Error: Debe haber al menos 1 cajero. Se usará 1.")
            num_cajeros = 1

        # --- Validación de Clientes ---
        num_clientes_totales = int(input(f"¿Cuántos clientes totales simular? (Máximo {15}): "))
        if num_clientes_totales > 15:
            print(f"Error: El máximo de clientes es {15}. Se simularán {15}.")
            num_clientes_totales = 15
        elif num_clientes_totales <= 0:
            print("Error: Debe haber al menos 1 cliente. Se simulará 1.")
            num_clientes_totales = 1

    except ValueError:
        print("Error: Por favor, ingrese un número entero válido.")
        return
    except KeyboardInterrupt:
        return

    clientes_por_hora = 85  # Tasa de llegada (Lambda)
    tasa_servicio_por_hora = 55  # Tasa de servicio (Mu)
    tiempo_servicio_min = 60 / tasa_servicio_por_hora

    log_de_eventos = ejecutar_simulacion(num_cajeros, num_clientes_totales, clientes_por_hora, tiempo_servicio_min)

    ejecutar_visualizador(log_de_eventos, num_cajeros)


if __name__ == "__main__":
    main()