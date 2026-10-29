@echo off
rem IRIS launcher: double-click, pilih mode dari menu. Dashboard dan vision dibuka di jendela masing-masing.
rem ESP32 tetap dijalankan di wokwi.com (tombol play dan slide switch diklik manual).
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title IRIS Launcher

set "PY=.venv\Scripts\python.exe"
set "WOKWI=https://wokwi.com/projects/479194485722835969"
set "DASH=http://127.0.0.1:8050"

rem ---------- Pemeriksaan awal ----------
if not exist "%PY%" (
  echo [X] Folder .venv belum ada. Ikuti bagian "Pasang di laptop lain" di README.md.
  goto :end
)
"%PY%" -c "import sys" >nul 2>&1
if errorlevel 1 (
  echo [X] Python untuk .venv belum terpasang. Jalankan:  uv python install 3.12.12
  goto :end
)
if not exist "models\iris-best.pt" (
  echo [X] Model belum ada di models\iris-best.pt. Unduh dari GitHub Releases ^(lihat README.md^).
  goto :end
)

:menu
cls
echo ==============================================
echo   IRIS - Smart PPE Compliance Gate ^& Monitoring
echo ==============================================
echo.
echo   1. Gerbang  (helm + rompi)
echo   2. Zona     (helm + rompi)
echo   3. Gerbang  - latihan tanpa rompi
echo   4. Zona     - latihan tanpa rompi
echo   5. Simulator tanpa kamera (data contoh)
echo   6. Dashboard saja
echo   0. Keluar
echo.
set "CHOICE="
set /p "CHOICE=Pilih nomor: "

set "NODE=gate1"
set "ROLE=GATE (kiri)"
set "EXTRA="
if "%CHOICE%"=="1" goto :vision
if "%CHOICE%"=="2" (set "NODE=zoneA" & set "ROLE=ZONE (kanan)" & goto :vision)
if "%CHOICE%"=="3" (set "EXTRA=--ignore-vest" & goto :vision)
if "%CHOICE%"=="4" (set "NODE=zoneA" & set "ROLE=ZONE (kanan)" & set "EXTRA=--ignore-vest" & goto :vision)
if "%CHOICE%"=="5" goto :simulator
if "%CHOICE%"=="6" (call :dashboard & goto :end)
if "%CHOICE%"=="0" goto :end
goto :menu

:vision
set "CAM=1"
set /p "CAM=Nomor kamera [Enter = 1, webcam USB]: "
call :checkgpu
call :dashboard
call :wokwi
echo.
echo Menjalankan vision: kamera %CAM%, node %NODE% %EXTRA%
echo Tutup dengan menekan q di jendela "IRIS vision".
start "IRIS Vision (%NODE%)" cmd /k ""%PY%" vision\run_vision.py --source %CAM% --node %NODE% --show %EXTRA%"
goto :end

:simulator
set "NODE=gate1"
set "SCEN=demo"
set /p "SIMZ=Mode simulator - 1 = Gerbang, 2 = Zona [Enter = 1]: "
if "%SIMZ%"=="2" (set "NODE=zoneA" & set "ROLE=ZONE (kanan)" & set "SCEN=zone-escalation")
call :dashboard
call :wokwi
start "IRIS Simulator (%NODE%)" cmd /k ""%PY%" vision\sim_publisher.py --node %NODE% --scenario %SCEN% --loop"
goto :end

rem ---------- Subrutin ----------
:dashboard
rem cek langsung ke alamat dashboard (netstat tidak selalu menampilkan port ini)
"%PY%" -c "import urllib.request as u; u.urlopen('%DASH%', timeout=2)" >nul 2>&1
if errorlevel 1 (
  echo Menyalakan dashboard...
  start "IRIS Dashboard" cmd /k ""%PY%" dashboard\app.py"
  ping -n 5 127.0.0.1 >nul
) else (
  echo Dashboard sudah berjalan.
)
start "" "%DASH%"
exit /b

:wokwi
start "" "%WOKWI%"
echo.
echo ---------------- Langkah di wokwi.com ----------------
echo  1. Klik tombol play hijau, tunggu "[MQTT] connected" (+-30 detik)
echo  2. Slide switch SOURCE ke kiri (LIVE)
echo  3. Slide switch ROLE ke %ROLE%
echo ------------------------------------------------------
exit /b

:checkgpu
"%PY%" -c "import sys, torch; sys.exit(0 if torch.cuda.is_available() else 1)" >nul 2>&1
if errorlevel 1 (
  echo [!] GPU tidak terdeteksi: vision akan lambat. Colok charger; jika baru bangun dari sleep, restart laptop.
) else (
  echo [OK] GPU terdeteksi.
)
exit /b

:end
echo.
pause
