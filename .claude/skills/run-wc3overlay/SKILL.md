---
name: run-wc3overlay
description: >
  Launch, restart, or check the WC3 Replay Overlay app (overlay_native + analyzer).
  Use this skill whenever the user says "启动", "重启", "run", "start", "restart",
  "跑一下", "开一下", or wants to test/verify the overlay is running.
  Also use when the user reports something broken and wants to restart the service.
---

# Running the WC3 Overlay

## Key facts

- **Always use system Python**: `C:\Users\huang\AppData\Local\Programs\Python\Python312\python.exe`
  The `.venv` uses MSYS2 Python which lacks PyQt6 — never use `.venv` to launch the app.
- **Entry point**: `python -m overlay_native` (run from project root)
- **Analyzer WebSocket**: `ws://localhost:8125` (port must be free before launching)
- **Log files**: `app_out.txt` and `app_err.txt` in the project root

## Steps

### 1. Kill existing processes

Free port 8125 and any leftover python instances from this project:

```powershell
$pids = netstat -ano | Select-String ":8125" | ForEach-Object { ($_ -split '\s+')[-1] } | Sort-Object -Unique
foreach ($p in $pids) { try { Stop-Process -Id $p -Force -ErrorAction Stop; Write-Host "Killed $p" } catch {} }
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*Python312*" } | ForEach-Object { Stop-Process -Id $_.Id -Force; Write-Host "Killed python $($_.Id)" }
```

### 2. Launch the app

```powershell
$py = "C:\Users\huang\AppData\Local\Programs\Python\Python312\python.exe"
Remove-Item "app_out.txt","app_err.txt" -Force -ErrorAction SilentlyContinue
Start-Process -FilePath $py -ArgumentList "-m", "overlay_native" `
  -WorkingDirectory "D:\war3observer-master\wc3rep" `
  -RedirectStandardOutput "D:\war3observer-master\wc3rep\app_out.txt" `
  -RedirectStandardError  "D:\war3observer-master\wc3rep\app_err.txt" `
  -NoNewWindow
```

### 3. Wait and verify

Wait 7 seconds, then read the logs:

```powershell
Start-Sleep -Seconds 7
Get-Content "D:\war3observer-master\wc3rep\app_out.txt" -ErrorAction SilentlyContinue
Write-Host "--- STDERR ---"
Get-Content "D:\war3observer-master\wc3rep\app_err.txt" -ErrorAction SilentlyContinue
```

**Success looks like** (in stderr):
```
INFO: server listening on 127.0.0.1:8125
INFO: 等待 WC3 启动...
INFO: connection open
INFO: 客户端连接: ('::1', ...)
```

stdout from overlay_native may be empty (GUI app) — that's normal.

### 4. Confirm process count

```powershell
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, @{N='Mem(MB)';E={[math]::Round($_.WorkingSet64/1MB,1)}}
```

Expect two processes: overlay_native (~100+ MB) and analyzer subprocess (~5 MB).

## Common problems

| Symptom | Fix |
|---|---|
| `OSError: [Errno 10048]` port in use | Step 1 didn't fully clean up — run kill block again |
| `ModuleNotFoundError: No module named 'PyQt6'` | Wrong Python used — make sure it's the Python312 path, not venv |
| analyzer stderr shows errors but WS binds OK | overlay_native still running fine; analyzer errors are usually WC3 not open |
| stdout empty after 7s | Normal for GUI app — check stderr for the real status |
