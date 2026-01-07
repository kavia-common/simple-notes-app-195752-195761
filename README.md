# simple-notes-app-195752-195761 (database)

This workspace contains the SQLite database (`database/myapp.db`) and helper utilities.

## Port 5001 readiness (SQLite)

The “Port 5001 is not ready” signal is typically caused by the DB visualizer (a small Node/Express app) failing to start/bind its HTTP port.

The visualizer lives at:

- `database/db_visualizer/`

### Start the DB visualizer on port 5001

From `database/`:

```bash
./start_db_visualizer.sh
```

This script will:
- Run `npm ci` if dependencies are missing/corrupted (fixes runtime errors like `Cannot find module './lib/express'`)
- Start the viewer on port `5001` (override via `PORT=...`)

Then open:

- `http://localhost:5001/`
