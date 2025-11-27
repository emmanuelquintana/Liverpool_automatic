# Liverpool Orders Automation

Este proyecto es una herramienta de automatización para gestionar pedidos del portal de Liverpool. Utiliza una interfaz gráfica (GUI) construida con Tkinter y automatización de navegador con Selenium (Edge).

## Funcionalidades

La aplicación permite realizar las siguientes tareas en 4 fases principales:

1.  **Escanear Pedidos (Dry-run)**: Escanea el portal de Liverpool en busca de pedidos con estado "Pendiente de aceptación".
2.  **Procesar Detalles**: Navega a los detalles de cada pedido, captura información y toma capturas de pantalla de los artículos. Genera reportes en Excel y PDF.
3.  **Aceptar y Descargar Guías**: Acepta automáticamente los pedidos en el portal y descarga las etiquetas de envío (guías) en formato PDF.
4.  **Unir Guías PDF**: Combina todas las guías descargadas de un día específico en un solo archivo PDF para facilitar su impresión.

## Requisitos

*   **Python 3.8+**
*   **Navegador Microsoft Edge** instalado.
*   **Edge WebDriver**: Debe coincidir con la versión de tu navegador Edge. El script espera encontrarlo en `C:\WebDrivers\msedgedriver.exe`.

### Librerías Python

Las principales dependencias son:

*   `selenium`: Para la automatización del navegador.
*   `PyPDF2`: Para manipular y unir archivos PDF.
*   `openpyxl`: Para generar reportes en Excel.
*   `Pillow` (PIL): Para procesamiento de imágenes.
*   `reportlab`: Para generación de PDFs.

Puedes instalarlas ejecutando:

```bash
pip install -r requirements.txt
```

## Instalación y Configuración

1.  Clona o descarga este repositorio.
2.  Asegúrate de tener el **Edge WebDriver** en `C:\WebDrivers\msedgedriver.exe`.
3.  La aplicación utiliza un perfil de usuario de Edge dedicado ubicado en `C:\EdgeProfiles\LiverpoolAuto` (se crea automáticamente o debe configurarse según `config.py`).

## Uso

1.  Ejecuta el archivo principal:
    ```bash
    python main.py
    ```
2.  Se abrirá la interfaz gráfica.
3.  **Selecciona la Carpeta Base**: Elige donde se guardarán los archivos generados (imágenes, reportes, guías).
4.  Sigue los botones numerados en orden:
    *   **1) Escanear pedidos**: Busca pedidos pendientes.
    *   **Selecciona las fechas** que deseas procesar en la lista que aparece.
    *   **2) Procesar detalles**: Genera la evidencia y reportes locales.
    *   **3) Aceptar pedidos**: Realiza la acción en el portal y baja las guías.
    *   **4) Unir guías**: Genera el PDF consolidado de guías.

## Estructura del Proyecto

*   `main.py`: Punto de entrada de la aplicación.
*   `view.py`: Interfaz gráfica (Tkinter).
*   `viewmodel.py`: Lógica de presentación y comunicación entre la vista y los servicios.
*   `services.py`: Lógica principal de automatización (Selenium) y procesamiento de archivos.
*   `models.py`: Definición de clases de datos (Order, OrderItem, etc.).
*   `config.py`: Configuraciones globales (URLs, rutas por defecto).
*   `js/`: Scripts de JavaScript inyectados en el navegador para extracción de datos.
