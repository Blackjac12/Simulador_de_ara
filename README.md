# 🛒 Simulador de Colas de Servicio - Tienda Ara (M/M/s)

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Simulación M/M/s](https://img.shields.io/badge/Modelo-M%2FM%2Fs-orange?style=for-the-badge)](https://en.wikipedia.org/wiki/M/M/c_queue)
[![Licencia MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

Este proyecto es una aplicación de simulación discreta de eventos construida en Python. Modela el sistema de servicio de cajas de una tienda (Tienda Ara) usando el modelo de colas **M/M/s**, donde 's' es el número de cajeros disponibles.

Permite a los usuarios ingresar parámetros de llegada (λ) y servicio (μ) para visualizar el comportamiento de la fila y el estado de los cajeros en tiempo real.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python
* **Simulación:** [SimPy](https://simpy.readthedocs.io/en/latest/) (Para el motor de eventos discretos).
* **Visualización:** [Pygame](https://www.pygame.org/) (Para la interfaz gráfica animada).
* **Interfaz Gráfica (GUI):** [TTkBootstrap](https://ttkbootstrap.readthedocs.io/en/latest/) (Para la ventana de configuración).
* **Manejo de Datos:** [Pandas](https://pandas.pydata.org/) (Para el registro y análisis de eventos).

---

## 🚀 Uso del Programa

### 1. Ejecutable para Windows (Recomendado)

Si solo deseas usar el simulador sin tocar el código:

1.  Ve a la sección de [Releases](LINK_AQUÍ_DE_TU_PÁGINA_DE_RELEASES_DE_GITHUB).
2.  Descarga el archivo `simulation_complete.exe` (o el nombre de tu aplicación).
3.  Ejecuta el archivo. **No se requiere ninguna instalación de Python.**

### 2. Ejecución desde Código (Desarrolladores)

Si deseas modificar el código o ejecutarlo directamente desde Python:

#### Requisitos

Necesitas tener Python 3.x y [git] (si clonas el repositorio).

#### Instalación y Ejecución

1.  **Clonar el Repositorio:**
    ```bash
    git clone [https://github.com/Tu-Usuario/Simulador_de_ara.git](https://github.com/Tu-Usuario/Simulador_de_ara.git)
    cd Simulador_de_ara
    ```

2.  **Crear Entorno Virtual (Opcional, pero recomendado):**
    ```bash
    python -m venv .venv
    # Activar el entorno virtual:
    # Windows: .venv\Scripts\activate
    # Linux/Mac: source .venv/bin/activate
    ```

3.  **Instalar Dependencias:**
    Utiliza el archivo `requirements.txt` para instalar todas las librerías necesarias:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecutar el Simulador:**
    ```bash
    python simulation_complete.py
    ```

---

## ⚙️ Estructura del Código

El proyecto se divide en módulos lógicos dentro de `simulation_complete.py`:

1.  **Lógica de Simulación (SimPy):** Define los procesos de llegada (`generate_arrivals`) y servicio (`serve_client`).
2.  **Lógica de Visualización (Pygame):** Maneja la carga de imágenes (`/Imagenes`), el movimiento de los sprites y el bucle de renderizado.
3.  **Lógica de Interfaz (ttkbootstrap):** Recibe los parámetros del usuario y llama a la simulación.
4.  **Función `resource_path`:** Función crítica para que el programa se ejecute correctamente como un ejecutable (`.exe`) al manejar las rutas de los archivos de imagen.

---

## 📝 Contribuciones y Licencia

Este proyecto está disponible bajo la **Licencia MIT**. Si deseas mejorar el proyecto, eres libre de hacerlo.