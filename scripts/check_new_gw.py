"""
Checks whether the current gameweek's journal image has already been
generated. Writes need_generate=true/false to $GITHUB_OUTPUT so the
workflow can skip the (slower) Playwright steps most of the time --
this runs every 5 minutes via the scraper, but the image only needs
to be rebuilt once per gameweek.
"""
import json
import os

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

current_gw = data.get("current_gw")

last_gw = None
if os.path.exists("last_image_gw.txt"):
    with open("last_image_gw.txt", encoding="utf-8") as f:
        content = f.read().strip()
        if content:
            last_gw = int(content)

need_generate = current_gw is not None and current_gw != last_gw

gh_output = os.environ.get("GITHUB_OUTPUT")
if gh_output:
    with open(gh_output, "a", encoding="utf-8") as f:
        f.write(f"need_generate={'true' if need_generate else 'false'}\n")
        f.write(f"current_gw={current_gw}\n")

print(f"current_gw={current_gw}, last_gw={last_gw}, need_generate={need_generate}")
