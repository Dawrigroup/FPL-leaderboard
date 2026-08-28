"""
FPL League Standings + Gameweek Summary Scraper
Fetches classic league standings and a per-gameweek recap (top scorers,
averages, closest rivals, captain analysis) from FPL's public API.
No login required.
"""
import json
import urllib.request
from datetime import datetime, timezone

LEAGUE_ID = 2908
STANDINGS_URL = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
LIVE_URL_TMPL = "https://fantasy.premierleague.com/api/event/{gw}/live/"
PICKS_URL_TMPL = "https://fantasy.premierleague.com/api/entry/{entry_id}/event/{gw}/picks/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FPL-Leaderboard-Bot/1.0)"
}


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_current_gw(bootstrap):
    for event in bootstrap.get("events", []):
        if event.get("is_current"):
            return event.get("id")
        if event.get("is_next"):
            return (event.get("id") or 1) - 1
    return None


def build_player_name_map(bootstrap):
    """Maps FPL player element id -> short display name (e.g. 'Salah')."""
    return {p["id"]: p.get("web_name", "Unknown") for p in bootstrap.get("elements", [])}


def build_live_points_map(gw):
    """Maps FPL player element id -> raw points scored in a given gameweek."""
    if not gw:
        return {}
    try:
        live = fetch_json(LIVE_URL_TMPL.format(gw=gw))
    except Exception as e:
        print(f"Could not fetch live points for GW{gw}: {e}")
        return {}
    return {el["id"]: el.get("stats", {}).get("total_points", 0) for el in live.get("elements", [])}


def fetch_standings():
    standings_raw = fetch_json(STANDINGS_URL)
    bootstrap = fetch_json(BOOTSTRAP_URL)

    current_gw = fetch_current_gw(bootstrap)
    player_names = build_player_name_map(bootstrap)
    live_points = build_live_points_map(current_gw)

    league_name = standings_raw.get("league", {}).get("name", "FPL League")
    results = standings_raw.get("standings", {}).get("results", [])

    players = []
    for entry in results:
        players.append({
            "rank": entry.get("rank"),
            "last_rank": entry.get("last_rank"),
            "team_name": entry.get("entry_name"),
            "manager_name": entry.get("player_name"),
            "team_id": entry.get("entry"),
            "gw_points": entry.get("event_total"),
            "total_points": entry.get("total"),
        })

    players.sort(key=lambda p: p["total_points"] or 0, reverse=True)

    gw_summary = build_gw_summary(players, current_gw, player_names, live_points)

    output = {
        "league_id": LEAGUE_ID,
        "league_name": league_name,
        "current_gw": current_gw,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "players": players,
        "gw_summary": gw_summary,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(players)} entries for league '{league_name}'")


def build_gw_summary(players, gw, player_names, live_points):
    if not gw or not players:
        return None

    scored = [p for p in players if p.get("gw_points") is not None]
    if not scored:
        return None

    # --- Basic gameweek stats (no extra API calls needed) ---
    by_gw = sorted(scored, key=lambda p: p["gw_points"], reverse=True)
    top_scorers = [
        {"team_name": p["team_name"], "manager_name": p["manager_name"], "points": p["gw_points"]}
        for p in by_gw[:3]
    ]
    avg_score = round(sum(p["gw_points"] for p in scored) / len(scored), 1)
    highest_score = by_gw[0]["gw_points"]
    lowest_score = by_gw[-1]["gw_points"]

    # --- Derby of the week: closest two teams by total points ---
    by_total = sorted(scored, key=lambda p: p["total_points"])
    derby = None
    smallest_gap = None
    for i in range(len(by_total) - 1):
        gap = abs(by_total[i + 1]["total_points"] - by_total[i]["total_points"])
        if smallest_gap is None or gap < smallest_gap:
            smallest_gap = gap
            derby = (by_total[i], by_total[i + 1])
    derby_data = None
    if derby:
        derby_data = {
            "team_a": derby[0]["team_name"],
            "team_b": derby[1]["team_name"],
            "score_a": derby[0]["total_points"],
            "score_b": derby[1]["total_points"],
            "diff": smallest_gap,
        }

    # --- Captain analysis: needs one API call per manager for this gameweek ---
    captain_counts = {}   # element_id -> number of managers who captained them
    manager_captain_info = []  # list of {team, manager, captain_id, captain_pts}
    bench_totals = []     # list of {team, manager, bench_points}

    for p in scored:
        entry_id = p.get("team_id")
        if not entry_id:
            continue
        try:
            picks_data = fetch_json(PICKS_URL_TMPL.format(entry_id=entry_id, gw=gw))
        except Exception as e:
            print(f"Could not fetch picks for entry {entry_id}: {e}")
            continue

        picks = picks_data.get("picks", [])
        captain_pick = next((pk for pk in picks if pk.get("is_captain")), None)
        if captain_pick:
            cap_id = captain_pick["element"]
            cap_pts = live_points.get(cap_id, 0)
            cap_name = player_names.get(cap_id, "Unknown")
            captain_counts[cap_id] = captain_counts.get(cap_id, 0) + 1
            manager_captain_info.append({
                "team_name": p["team_name"],
                "manager_name": p["manager_name"],
                "captain_id": cap_id,
                "captain_name": cap_name,
                "captain_points": cap_pts,
            })
            # Also attach directly to the player's row for the main table's "C" column
            p["captain_name"] = cap_name
        else:
            p["captain_name"] = None

        bench_picks = [pk for pk in picks if pk.get("position", 0) > 11]
        bench_pts = sum(live_points.get(pk["element"], 0) for pk in bench_picks)
        bench_totals.append({
            "team_name": p["team_name"],
            "manager_name": p["manager_name"],
            "bench_points": bench_pts,
        })

    bench_king = None
    if bench_totals:
        top_bench = max(bench_totals, key=lambda b: b["bench_points"])
        bench_king = top_bench

    worst_captain = None
    best_differential = None
    if manager_captain_info:
        worst_captain = min(manager_captain_info, key=lambda c: c["captain_points"])

        # Differential captain: captained by only 1 manager, with the highest points among those
        differentials = [c for c in manager_captain_info if captain_counts.get(c["captain_id"]) == 1]
        if differentials:
            best_differential = max(differentials, key=lambda c: c["captain_points"])

    return {
        "gw": gw,
        "top_scorers": top_scorers,
        "average_score": avg_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "derby": derby_data,
        "bench_king": bench_king,
        "worst_captain": worst_captain,
        "best_differential_captain": best_differential,
    }


if __name__ == "__main__":
    fetch_standings()
