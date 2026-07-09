@echo off
echo ===================================================
echo YouTube Downloader EXE Builder (Python Portable)
echo ===================================================
echo.

set PYTHON_DIR=%~dp0python
set LOCAL_PYTHON=%PYTHON_DIR%\python.exe

if not exist "%LOCAL_PYTHON%" (
    echo [ERROR] No se encontro "%LOCAL_PYTHON%".
    echo Por favor, asegúrate de extraer el archivo ZIP de Python embebido
    echo dentro de la carpeta "python" de este proyecto.
    echo.
    pause
    exit /b
)

echo Configurando Python portable...
REM Descomentar "import site" en el archivo ._pth para habilitar el uso de librerías externas (site-packages)
"%LOCAL_PYTHON%" -c "import glob; [open(p, 'w').write(open(p, 'r').read().replace('#import site', 'import site')) for p in glob.glob('python/python3*._pth') if '#import site' in open(p, 'r').read()]"

REM Comprobar si pip está instalado en el Python embebido
"%LOCAL_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] pip no esta instalado en el Python portable. Descargando e instalando...
    "%LOCAL_PYTHON%" -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', 'get-pip.py')"
    if errorlevel 1 (
        echo [ERROR] No se pudo descargar get-pip.py. Verifica tu conexion a internet.
        pause
        exit /b
    )
    "%LOCAL_PYTHON%" get-pip.py --no-warn-script-location
    if errorlevel 1 (
        echo [ERROR] Fallo la instalacion de pip.
        del get-pip.py >nul 2>&1
        pause
        exit /b
    )
    del get-pip.py >nul 2>&1
)

echo Instalando dependencias del proyecto desde requirements.txt...
"%LOCAL_PYTHON%" -m pip install -r requirements.txt --no-warn-script-location
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b
)

echo Instalando PyInstaller...
"%LOCAL_PYTHON%" -m pip install pyinstaller --no-warn-script-location
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de PyInstaller.
    pause
    exit /b
)

echo Compilando aplicacion a un unico ejecutable .exe...
"%LOCAL_PYTHON%" -m PyInstaller --onefile --noconsole --add-data "app/static;app/static" --add-data "app/version.txt;app" --name yt_downloader run.py
if errorlevel 1 (
    echo [ERROR] Fallo la compilacion de la aplicacion.
    pause
    exit /b
)

echo.
echo ===================================================
echo [EXITO] Compilacion finalizada correctamente!
echo El ejecutable compilado esta en: dist\yt_downloader.exe
echo ===================================================
echo.
pause
