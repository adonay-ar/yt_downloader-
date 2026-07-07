# YTDL Premium - YouTube Downloader en Docker

Una aplicación web moderna, premium y responsiva para descargar videos y audios de YouTube. Está encapsulada en Docker, desarrollada con **FastAPI** (Python) en el backend, potenciada por **`yt-dlp`**, y utiliza **Deno** como motor de ejecución JavaScript para evadir de manera óptima las restricciones de firmas y retos de YouTube.

---

## 🌟 Características Principales

*   **Diseño Premium Glassmorphic:** Interfaz oscura, elegante e intuitiva adaptada para todo tipo de pantallas (monitores, tablets y móviles).
*   **Bypass de Bloqueos de YouTube:**
    *   **OAuth2 Oficial Integrado:** Permite enlazar tu cuenta de YouTube mediante el flujo oficial de dispositivo de Google (copiando y registrando un código en tu navegador). El token se guarda en caché y persiste al apagar el contenedor.
    *   **Carga de Cookies:** Drag-and-drop para subir tu archivo `cookies.txt` (formato Netscape) exportado de tu navegador habitual para saltar retos anti-bot.
*   **Progreso en Tiempo Real:** Barra de progreso dinámica, velocidad de descarga y cálculo de tiempo restante (ETA) transmitido a través de WebSockets de forma eficiente y segura.
*   **Gestión de Descargas Directa:** Los archivos multimedia descargados se guardan inmediatamente en una carpeta local de tu máquina host. También se pueden descargar de vuelta a través del navegador desde la pestaña **Descargados**.
*   **Ligero y Eficiente:** No requiere Node.js completo en la imagen; en su lugar, utiliza el motor estático de **Deno** para resolver los retos de firma.

---

## 🛠️ Requisitos Previos

Solo necesitas tener instalado:
*   [Docker](https://www.docker.com/)
*   [Docker Compose](https://docs.docker.com/compose/)

---

## 🚀 Instalación y Uso Rápido

1.  Clona o copia esta carpeta en tu máquina.
2.  Levanta el contenedor con Docker Compose:
    ```bash
    docker compose up --build -d
    ```
3.  Abre tu navegador web e ingresa a la siguiente dirección:
    ```text
    http://localhost:38282
    ```

---

## 🔑 Guía para Evadir Bloqueos (Retos de Firma/Bots)

YouTube cambia constantemente sus políticas y bloquea IPs de servidores o descargas automatizadas que no estén validadas. Para evitar el error de *"Sign in to confirm you're not a bot"*, cuentas con dos opciones en la pestaña **Autenticación**:

### Opción A: Autenticación por Dispositivo (OAuth2) — Recomendado
1. Ve a la pestaña **Autenticación** y haz clic en **Iniciar Flujo OAuth2**.
2. Copia el código de dispositivo que aparecerá en pantalla.
3. Haz clic en el enlace de Google provisto (`https://google.com/device`), pega el código y autoriza el acceso con tu cuenta de Google.
4. El contenedor guardará de forma persistente tus tokens en la carpeta local `./cache`, por lo que solo deberás hacer este paso una vez.

### Opción B: Cargar cookies.txt
1. Instala una extensión en tu navegador como *Get cookies.txt LOCALLY* (Chrome/Firefox).
2. Ve a YouTube en tu navegador (asegúrate de estar logueado en tu cuenta de preferencia) y exporta las cookies de YouTube en formato de texto (`cookies.txt`).
3. Ve a la pestaña **Autenticación** y arrastra el archivo `cookies.txt` al área de carga de cookies de la app web.
4. Las cookies se guardarán y persistirán localmente en la carpeta `./cookies`. Puedes eliminarlas en cualquier momento con el botón de papelera.

---

## 📂 Estructura del Proyecto

```text
yt_downloader/
├── app/
│   ├── main.py          # API FastAPI y gestión de WebSockets
│   ├── downloader.py    # Integración con la API de yt-dlp y flujo OAuth2
│   └── static/          # Archivos frontend (HTML, CSS, JS)
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   └── app.js
│       └── index.html
├── cache/               # [Volumen Host] Caché de tokens OAuth2 de YouTube
├── cookies/             # [Volumen Host] Archivos cookies.txt subidos
├── downloads/           # [Volumen Host] Carpeta local con los videos descargados
├── Dockerfile           # Receta de la imagen Docker (Python + Deno + FFmpeg)
├── docker-compose.yml   # Orquestación de servicios y puertos (38282)
├── requirements.txt     # Dependencias de Python
└── README.md            # Documentación del proyecto
```
