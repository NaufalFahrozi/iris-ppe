# Catat suhu, daya, dan VRAM GPU tiap 30 detik ke CSV selama training.
# Pemakaian: powershell -File training/gpu_log.ps1 -Out runs/train/<name>/gpu_log.csv
param([string]$Out = "runs/train/gpu_log.csv", [int]$Interval = 30)

New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
nvidia-smi --query-gpu=timestamp,temperature.gpu,power.draw,memory.used,utilization.gpu,clocks_throttle_reasons.active --format=csv -l $Interval | Out-File -FilePath $Out -Encoding utf8
