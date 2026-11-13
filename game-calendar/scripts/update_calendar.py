#!/usr/bin/env python3
"""Build a stable Apple Calendar subscription, and monitor official game pages."""
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "tracked.json"
STATE = ROOT / "data" / "state.json"
ICS = ROOT / "calendar.ics"
REPORT = ROOT / "latest-check.md"
UA = "PersonalGameCalendar/1.0 (github.com/RicardoZhangFan/loon-rules)"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/html,*/*"})
    with urllib.request.urlopen(req, timeout=22) as r:
        return r.read(1500000).decode("utf-8", errors="replace")

def esc(v):
    return str(v).replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")

def folded(line):
    # RFC 5545 75 octet max; continuation begins with one space
    parts = []
    current = ""
    for ch in line:
        if len((current + ch).encode("utf-8")) > 73 and current:
            parts.append(current)
            current = " " + ch
        else:
            current += ch
    parts.append(current)
    return parts

def build_ics(cfg):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    games = {g["id"]: g for g in cfg["games"]}
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Personal Game Calendar//ZH", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", "X-WR-CALNAME:" + esc(cfg["calendar"]["name"]),
             "X-WR-TIMEZONE:Asia/Shanghai"]
    for event in sorted(cfg["events"], key=lambda e: (e["date"], e["id"])):
        if event["game_id"] not in games:  # prevent removed games from recurring
            continue
        date = dt.date.fromisoformat(event["date"])
        end = date + dt.timedelta(days=1)
        stable_uid = re.sub(r"[^a-z0-9_-]", "", event["id"].lower())
        lines.extend(["BEGIN:VEVENT", "UID:" + stable_uid + "@ricardozhangfan.game-calendar",
                      "DTSTAMP:" + now, "DTSTART;VALUE=DATE:" + date.strftime("%Y%m%d"),
                      "DTEND;VALUE=DATE:" + end.strftime("%Y%m%d"),
                      "SUMMARY:" + esc(event["title"]),
                      "DESCRIPTION:" + esc("平台：" + games[event["game_id"]]["platform"] + "\n来源：" + event["source_url"]),
                      "URL:" + event["source_url"], "STATUS:CONFIRMED", "TRANSP:TRANSPARENT"])
        for days in cfg["calendar"]["reminder_days"]:
            lines.extend(["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + esc(event["title"]),
                          "TRIGGER;RELATED=START:-P" + str(days) + "D", "END:VALARM"])
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    out = "\r\n".join(part for line in lines for part in folded(line)) + "\r\n"
    # Don't force re-commit if nothing materially changed: remove dynamic DTSTAMP
    if ICS.exists():
        previous = ICS.read_bytes().decode("utf-8")
        cleaned = lambda s: re.sub(r"DTSTAMP:\\d{8}T\\d{6}Z", "DTSTAMP:TIMESTAMP", s)
        if cleaned(previous) == cleaned(out):
            return False
    ICS.write_bytes(out.encode("utf-8"))
    return True

def monitor(cfg):
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    previous = state.get("page_hashes", {})
    updated = dict(previous)
    findings = []
    reports = []
    for g in cfg["games"]:
        urls = [g["source_url"]]
        if g.get("steam_app_id"):
            urls.insert(0, "https://store.steampowered.com/api/appdetails?appids=" + str(g["steam_app_id"]) + "&cc=us&l=english")
        for url in urls:
            try:
                body = get(url)
                # Avoid flagging random changes to highly dynamic HTML pages: extract stable text where possible.
                if "api/appdetails" in url:
                    obj = json.loads(body)
                    details = obj.get(str(g["steam_app_id"]), {}).get("data") or {}
                    if not details:
                        raise ValueError("Steam API has no game data")
                    marker = json.dumps({"release_date": details.get("release_date"),
                                         "coming_soon": details.get("release_date", {}).get("coming_soon")}, sort_keys=True)
                else:
                    # Public pages can vary each request; monitor title, canonical dates and first 3000 clean chars.
                    title = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
                    meta = re.findall(r'<meta[^>]+(?:description|published_time|release_date)[^>]+>', body[:120000], re.I)
                    marker = (title.group(1).strip() if title else "") + "\n" + "\n".join(meta[:5])
                    if not marker.strip():
                        marker = re.sub(r"\\s+", " ", re.sub("<[^>]+>", " ", body[:3000]))
                digest = hashlib.sha256(marker.encode("utf-8")).hexdigest()
                if url in previous and previous[url] != digest:
                    findings.append({"game": g["name"], "url": url, "change": "官方页面的日期/标题元信息变化，请人工核实后修改 data/tracked.json"})
                updated[url] = digest
                reports.append((g["name"], "OK", url))
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as err:
                reports.append((g["name"], "CHECK FAILED: " + str(err)[:100], url))
    state["page_hashes"] = updated
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# 游戏日历每周核查", "", "核查时间：" + stamp, "",
             "日期必须来自可靠官方公告；网页变化不会直接改写发售日。", "",
             "| 游戏 | 结果 | 官方来源 |", "|---|---|---|"]
    lines += ["| " + n + " | " + s.replace("|", "/") + " | " + u + " |" for n, s, u in reports]
    lines += ["", "## 值得人工核实的变化", ""]
    lines += ["- " + f["game"] + "：" + f["change"] + " " + f["url"] for f in findings] or ["本次没有识别到官方页面变化。"]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # GitHub Actions can use this structured output to create an issue, including on manual dispatch.
    (ROOT / "data" / "changes.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Checked", len(reports), "sources; changes:", len(findings))

def main():
    cfg = json.loads(DATA.read_text(encoding="utf-8"))
    monitor(cfg)
    print("Calendar updated:", build_ics(cfg))

if __name__ == "__main__":
    main()
