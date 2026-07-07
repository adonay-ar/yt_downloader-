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

## 🛠️ Instalación de Docker

Docker es el único requisito para correr esta aplicación. A continuación los pasos mínimos por sistema operativo:

### Windows

1. Descarga **Docker Desktop** desde: https://www.docker.com/products/docker-desktop
2. Ejecuta el instalador y sigue el asistente (requiere reinicio).
3. Al abrir Docker Desktop por primera vez, acepta los términos y espera a que el motor arranque (ícono verde en la barra de tareas).
4. Verifica que funciona abriendo una terminal (`PowerShell` o `CMD`):
    ```bash
    docker --version
    ```

> **Nota Windows:** Docker Desktop requiere **WSL 2** (Windows Subsystem for Linux). Si el instalador lo solicita, sigue el enlace que aparece para activarlo; generalmente es automático en Windows 10 v2004+ y Windows 11.

### macOS

1. Descarga **Docker Desktop** desde: https://www.docker.com/products/docker-desktop  
   *(elige la versión correcta: Apple Silicon o Intel)*
2. Arrastra Docker al directorio de Aplicaciones y ábrelo.
3. Acepta los permisos del sistema y espera a que el ícono de la ballena aparezca en la barra de menús.
4. Verifica en Terminal:
    ```bash
    docker --version
    ```

### Linux (Ubuntu / Debian)

Copia y ejecuta estos 3 comandos en tu terminal:

```bash
# 1. Instala Docker Engine
curl -fsSL https://get.docker.com | sh

# 2. Agrega tu usuario al grupo docker (para no usar sudo)
sudo usermod -aG docker $USER

# 3. Reinicia la sesión y verifica
newgrp docker && docker --version
```

> Docker Compose ya viene incluido en versiones modernas de Docker (`docker compose` sin guión). Si tu versión es antigua, instálalo con: `sudo apt install docker-compose-plugin`

---

## 🚀 Instalación de la Aplicación

Una vez que Docker está corriendo:

1. Descarga o clona este repositorio en tu máquina:
    ```bash
    git clone https://github.com/adonay-ar/yt_downloader-.git
    cd yt_downloader-
    ```
    > Si no tienes git, descarga el ZIP desde GitHub y descomprímelo.

2. Levanta el contenedor (solo la primera vez tarda ~2 minutos en construir la imagen):
    ```bash
    docker compose up --build -d
    ```

3. Abre tu navegador e ingresa a:
    ```text
    http://localhost:38282
    ```

4. Para detener la aplicación:
    ```bash
    docker compose down
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

## 🔄 Sistema de Actualización Automática

La aplicación incluye un sistema de actualización automática vía GitHub. Cuando hay una nueva versión disponible, el usuario puede actualizarla desde la pestaña **Sistema** en la interfaz web con un solo clic.

### ¿Cómo funciona?

1. La app consulta el archivo `version.json` en la rama `main` de este repositorio.
2. Compara la versión remota con la versión instalada localmente.
3. Si hay una versión más nueva, descarga el ZIP de la rama `main`, sobrescribe los archivos del proyecto y reinicia el contenedor automáticamente.

### ¿Cómo publicar una nueva versión?

Para lanzar una actualización a todos los usuarios que tienen la app instalada:

1. **Realiza tus cambios** en el código.
2. **Actualiza el número de versión** en `version.json` (en la raíz del proyecto):
    ```json
    {
      "version": "1.2.0",
      "release_notes": "Descripción breve de los cambios en esta versión.",
      "zip_url": "https://github.com/adonay-ar/yt_downloader-/archive/refs/heads/main.zip"
    }
    ```
3. **Sube los cambios a GitHub:**
    ```bash
    git add .
    git commit -m "feat: v1.2.0 - descripción breve"
    git push origin main
    ```

A partir de ese momento, cualquier instancia de la app detectará la nueva versión al presionar **"Buscar Actualizaciones"** en la pestaña **Sistema**, y podrá instalarla sin intervención manual adicional.

> **Nota:** La actualización respeta los archivos de usuario (descargas, cookies, caché de tokens OAuth2) y solo sobrescribe el código de la aplicación.

---

## 📂 Estructura del Proyecto

```text
yt_downloader/
├── app/
│   ├── main.py          # API FastAPI y gestión de WebSockets
│   ├── downloader.py    # Integración con la API de yt-dlp y flujo OAuth2
│   ├── updater.py       # Módulo de actualización automática desde GitHub
│   ├── version.txt      # Versión instalada localmente (actualizada por el updater)
│   └── static/          # Archivos frontend (HTML, CSS, JS)
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   └── app.js
│       └── index.html
├── cache/               # [Volumen Host] Caché de tokens OAuth2 de YouTube
├── cookies/             # [Volumen Host] Archivos cookies.txt subidos
├── downloads/           # [Volumen Host] Carpeta local con los videos descargados
├── version.json         # Control de versión remota (leído por el actualizador)
├── Dockerfile           # Receta de la imagen Docker (Python + Deno + FFmpeg)
├── docker-compose.yml   # Orquestación de servicios y puertos (38282)
├── requirements.txt     # Dependencias de Python
└── README.md            # Documentación del proyecto
```
