"""
FPL League Standings Scraper
Fetches classic league standings from the public FPL API and saves to data.json
No login required — this uses FPL's public read-only endpoint.
"""
import json
import urllib.request
from datetime import datetime, timezone

LEAGUE_ID = 2908
URL = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

# FPL blocks requests with no User-Agent header, so we set one
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FPL-Leaderboard-Bot/1.0)"
}


def fetch_current_gw():
    req = urllib.request.Request(BOOTSTRAP_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = json.loads(response.read().decode("utf-8"))
    for event in raw.get("events", []):
        if event.get("is_current"):
            return event.get("id")
        if event.get("is_next"):
            return (event.get("id") or 1) - 1
    return None


def fetch_standings():
    req = urllib.request.Request(URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = json.loads(response.read().decode("utf-8"))

    current_gw = fetch_current_gw()

    league_name = raw.get("league", {}).get("name", "FPL League")
    results = raw.get("standings", {}).get("results", [])

    players = []
    for entry in results:
        players.append({
            "rank": entry.get("rank"),
            "last_rank": entry.get("last_rank"),
            "team_name": entry.get("entry_name"),
            "manager_name": entry.get("player_name"),
            "gw_points": entry.get("event_total"),
            "total_points": entry.get("total"),
        })

    # Sort by total points descending, just in case
    players.sort(key=lambda p: p["total_points"] or 0, reverse=True)

    output = {
        "league_id": LEAGUE_ID,
        "league_name": league_name,
        "current_gw": current_gw,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "players": players,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(players)} entries for league '{league_name}'")


if __name__ == "__main__":
    fetch_standings()
