@echo off
cls
echo ========================================
echo AIBES Analytics - EXE Builder
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    echo.
)

REM Install required packages
echo Installing required packages...
pip install dash dash-bootstrap-components sqlalchemy pandas pymysql reportlab matplotlib qrcode
echo.

REM Clean previous builds
if exist dist (
    echo Cleaning previous build...
    rmdir /s /q dist
)
if exist build (
    rmdir /s /q build
)
if exist *.spec (
    del *.spec
)
echo.

REM Build the executable
echo Building executable...
pyinstaller --name=AIBES_Analytics ^
    --onedir ^
    --windowed ^
    --add-data="assets;assets" ^
    --add-data="apps;apps" ^
    --add-data="settings.db;." ^
    --hidden-import=dash ^
    --hidden-import=dash_bootstrap_components ^
    --hidden-import=sqlalchemy ^
    --hidden-import=pandas ^
    --hidden-import=pymysql ^
    --hidden-import=reportlab ^
    --hidden-import=matplotlib ^
    --hidden-import=qrcode ^
    --hidden-import=email.mime.multipart ^
    --hidden-import=email.mime.text ^
    --hidden-import=email.mime.base ^
    --hidden-import=ssl ^
    --hidden-import=hashlib ^
    --hidden-import=urllib.parse ^
    --hidden-import=sqlite3 ^
    --hidden-import=io ^
    --hidden-import=matplotlib.backends.backend_agg ^
    --clean ^
    --noconfirm ^
    --icon=assets/aibes.png ^
    main.py

echo.
echo ========================================
echo Build Process Completed!
echo ========================================
echo Location: dist\AIBES_Analytics\
echo To run: double-click AIBES_Analytics.exe
echo Application will be available at: http://127.0.0.1:8050
echo.
pause