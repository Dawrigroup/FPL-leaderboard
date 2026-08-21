# FPL League Leaderboard (League 2908)

A live-updating leaderboard for your FPL classic league, hosted free on GitHub Pages.
- `scraper.py` fetches standings from the public FPL API (no login needed)
- GitHub Actions runs the scraper every 15 minutes and saves `data.json`
- `index.html` displays the table and refreshes itself in the browser

## Setup (one-time, ~5 minutes)

1. **Create a new repository**
   - Go to https://github.com/new
   - Name it something like `fpl-leaderboard`
   - Set it to **Public** (required for free GitHub Pages)
   - Click **Create repository**

2. **Upload these files**
   - On your new repo page, click **"uploading an existing file"**
   - Drag in: `scraper.py`, `data.json`, `index.html`, and the whole `.github` folder (including `workflows/update.yml`)
   - Commit the files

3. **Enable GitHub Pages**
   - Go to **Settings → Pages** (left sidebar)
   - Under "Build and deployment", set **Source** to `Deploy from a branch`
   - Set **Branch** to `main` and folder to `/ (root)`
   - Save. Your site will appear at:
     `https://YOUR-USERNAME.github.io/fpl-leaderboard/`

4. **Allow Actions to push updates**
   - Go to **Settings → Actions → General**
   - Scroll to "Workflow permissions"
   - Select **"Read and write permissions"**
   - Save

5. **Trigger the first run manually** (don't wait 15 min)
   - Go to the **Actions** tab → **Update FPL Leaderboard** → **Run workflow**
   - After ~30 seconds, check your repo — `data.json` should now have real standings
   - Refresh your GitHub Pages site to see it live

That's it. From here, GitHub Actions will run automatically every 15 minutes, all year, for free — no server, no maintenance. GitHub's free tier includes 2,000 Action-minutes/month, and this uses only a few minutes/day, so you won't hit any limits.

## Changing the league ID later
Edit `LEAGUE_ID = 2908` at the top of `scraper.py` if you ever need to point it at a different league.
