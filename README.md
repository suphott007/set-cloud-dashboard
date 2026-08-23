# SET Cloud 4-Chart — Pilot Deploy V1

Cloud copy of the Galaxy Tab 4-chart dashboard. It is independent from the local Mac/FastAPI dashboard.

## Architecture

- `docs/` = GitHub Pages static site
- `docs/data/history/*.json` = historical OHLCV exported from the Mac archive
- `docs/data/live.json` = current-day snapshot used to replace today's daily candle
- `.github/workflows/intraday.yml` = pilot scheduled updater every 5 minutes during broad UTC windows; the Python script additionally enforces Thai market sessions
- `.github/workflows/eod.yml` = finalizes the current-day snapshot into history after market close

The initial pilot list is `IRPC, PTT, SCB, CPF` in `config/symbols.txt`.

## 1. Seed historical data on the Mac

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/export_history.py \
  --root "/Volumes/DATA/SET/stock_data_10y" \
  --symbols-file config/symbols.txt \
  --out docs/data/history
```

Confirm:

```bash
ls docs/data/history
cat docs/data/symbols.json
```

## 2. Local preview of the cloud-static site

```bash
python3 -m http.server 8080 --directory docs
```

Open `http://localhost:8080` on the Mac or `http://<MAC-LAN-IP>:8080` from the Tab.

## 3. Deploy to GitHub Pages

Create a GitHub repository and upload/commit this whole folder. In GitHub repository settings:

1. Settings → Pages
2. Build and deployment → Source: **Deploy from a branch**
3. Branch: `main`
4. Folder: `/docs`
5. Save

The Pages URL will be similar to:

`https://<github-username>.github.io/<repo-name>/`

## 4. Actions permissions

For the scheduled data commit to work:

Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save.

Then open Actions → `SET intraday pilot` → Run workflow once manually to test.

## Important pilot limitations

- GitHub Actions cron is best-effort; a `*/5` schedule can run late. This is a viewing/monitoring dashboard, not an execution feed.
- The pilot updater reads public quote pages and uses SET first with SETTRADE only as fallback. If either site blocks automated cloud runners or changes its page structure, the previous `live.json` remains and history still loads.
- Keep the pilot at four symbols until a live market-day test confirms reliability and permitted use. Do not scale to SET100 by simply increasing request volume without validating the data source/rate policy.
- For a public site, confirm that your intended market-data redistribution is allowed. A private/personal deployment avoids exposing portfolio holdings, but source licensing still matters.
