# Running Locally

The Docker app runs FastAPI at `http://localhost:8000`. FastAPI serves the built frontend at `/` and the API under `/api/`.

## Start

Mac:
```bash
./scripts/start-mac.sh
```

Linux:
```bash
./scripts/start-linux.sh
```

Windows PowerShell:
```powershell
.\scripts\start-windows.ps1
```

## Check

- Open `http://localhost:8000` to see the app.
- Open `http://localhost:8000/api/health` to see the backend health JSON.

## Stop

Mac:
```bash
./scripts/stop-mac.sh
```

Linux:
```bash
./scripts/stop-linux.sh
```

Windows PowerShell:
```powershell
.\scripts\stop-windows.ps1
```
