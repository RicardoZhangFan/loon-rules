# 🎮 我的游戏日程

Apple Calendar **subscription** (not one-time import):

https://raw.githubusercontent.com/RicardoZhangFan/loon-rules/main/game-calendar/calendar.ics

On iPhone: Calendar → Calendars → Add Calendar → Add Subscription Calendar → paste URL.
On macOS: Calendar → File → New Calendar Subscription → paste URL. Set refresh interval to daily if available.

This feed is hosted directly by GitHub raw. The repository is public. Events are all-day dates (Asia/Shanghai context), with 7-day and 1-day DISPLAY alarms. **Apple may ignore alarms in subscribed calendars** depending on OS/account settings; for critical reminders, also set local alerts. Apple determines subscription refresh frequency.

**Confirmed tracking list:** GTA 6, 无限大 ANANTA, Diablo IV seasons / expansion, Forza Horizon series. Last Epoch excluded by request. No unconfirmed release dates are published.

## Updates

GitHub Actions runs every Monday 09:17 Beijing time (01:17 UTC) and can also be run manually via Actions → Weekly game calendar update → Run workflow.

The workflow checks publisher/official information and Steam API release-date fields, writes a review report to `latest-check.md`, and creates a GitHub issue when stable page metadata changes. It regenerates `calendar.ics` from `data/tracked.json`. **It does not automatically infer release dates from arbitrary webpages**: this avoids invented events or silently propagating marketing dates. Newly announced events must be verified and added to `data/tracked.json`, followed by a workflow run. This is a source-change detector, not autonomous editorial research.

To add or remove a title, edit the `games` array in `data/tracked.json`. To add a confirmed event, add an object to `events` with stable id, game_id, title, date (YYYY-MM-DD), source_url, type, then run workflow. Removing a game also removes its events from the feed.

GitHub Actions schedules can be delayed by GitHub and might be disabled after long inactivity. Check the Actions page if the report stops updating. Public repo branch workflow files require appropriate permissions.
