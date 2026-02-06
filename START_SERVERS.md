# 🚀 Start Servers

## Production Mode (Single Process)

With `SERVE_FRONTEND=true` in `.env`, one process serves everything on port 8000:

```bash
# Build frontend + start
./deploy/build-and-start.sh

# Or if using systemd service
sudo systemctl start sqlaiagent
```

Access at: `http://<server-ip>:8000`

---

## Development Mode (E2E Testing)

You need **3 terminals** open:

### Terminal 1: Backend Server
```powershell
.\venv_win\Scripts\Activate.ps1
python -m backend.app.main
```

**Wait for:** `INFO: Uvicorn running on http://0.0.0.0:8000`

---

### Terminal 2: Frontend Server
```powershell
cd frontend
npm run dev
```

**Wait for:** `Local: http://localhost:3000/`

---

### Terminal 3: Run Tests
```powershell
# Interactive UI mode (recommended)
npm run test:e2e:ui

# Or headless mode
npm run test:e2e

# Or specific tests
npx playwright test e2e/auth.spec.ts
```

---

## ✅ Verification

Before running tests, verify both servers are accessible:

1. **Backend:** Open http://localhost:8000/docs in your browser
   - Should see FastAPI Swagger UI

2. **Frontend:** Open http://localhost:3000 in your browser
   - Should see login page

If both work, you're ready to run tests! 🎉

---

## 🐛 Troubleshooting

### Port already in use

```powershell
# Check what's using the ports
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill processes if needed (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Backend won't start

```powershell
# Verify venv exists
ls .\venv_win\Scripts\python.exe

# Reinstall dependencies if needed
.\venv_win\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend won't start

```powershell
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Database not initialized

```powershell
.\venv_win\Scripts\python.exe scripts\init_db.py
```

---

## 💡 Pro Tips

1. **Keep servers running** between test runs for faster development
2. **Use Playwright UI mode** (`npm run test:e2e:ui`) to debug failures visually
3. **Run specific tests** while developing: `npx playwright test e2e/auth.spec.ts:33`
4. **Clear browser state** if tests behave strangely (restart servers)

---

## 📝 Why Manual Startup?

**Auto-start** (used in CI) has issues on Windows:
- ❌ Slower (restarts servers each time)
- ❌ Virtual env path complications
- ❌ Blocks Playwright UI from loading
- ❌ Harder to debug server startup issues

**Manual start** (recommended for local dev):
- ✅ Faster (reuse running servers)
- ✅ Easier to debug (see server logs)
- ✅ Playwright UI loads instantly
- ✅ More control over server lifecycle

---

**Ready?** Start all 3 terminals and run `npm run test:e2e:ui`!
