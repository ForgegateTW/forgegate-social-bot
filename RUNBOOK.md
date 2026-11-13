# ForgeGate Social Bot: runbook

This repo is the bot. Scheduled Claude sessions follow this file. Read it fully before doing anything.

## What the bot does

- Posts 3 Instagram carousels a week for ForgeGate, one per division, split across two accounts:
  - TechWorx posts go to **@forgegatetech** (Windsor account id `17841438122178552`)
  - Media and Estate Operations posts go to **@weareforgegate** (Windsor account id `17841450093722489`)
  - **Monday: ForgeGate TechWorx** (technology, systems, automation including AI)
  - **Wednesday: ForgeGate Media** (strategy, brand, photo, film, social media, collaborations)
  - **Friday: ForgeGate Estate Operations** (property care, project management, trades & vendors, billing & invoicing, documentation)
- Every post goes out at **10:45 a.m. America/New_York**.
- Zachary can **hold** any post or **pause** the whole bot from the queue page. A held post is skipped. A paused bot plans and posts nothing.
- Facebook: the bot never posts to Facebook directly. Whether Instagram's share-to-Facebook setting carries API posts across is being checked on the first posts.
- If Windsor answers "Media ID is not available", Instagram was still processing the slides and nothing was posted (seen on the first live test, 2026-11-11). Wait 2 minutes, confirm with `get_data` (fields `media_id`, `timestamp`, `media_caption`) that no post with this caption exists today, then retry exactly once. If that fails too, mark the post `failed`.
- If Windsor answers "Application does not have permission for this action", that account's Windsor connection needs reconnecting with publishing allowed: mark the post `failed` with that reason and tell Zachary which account.

## Where things live

| Thing | Where |
| --- | --- |
| Code, brand art, fonts, rendered slides | this repo: `github.com/ForgegateTW/forgegate-social-bot` (public) |
| Queue, holds, pause switch, results, reports | artifact **ForgeGate Post Queue**, slug `83ab056c-a73e-4ee6-bf8f-7c6208df2da1`, database via `db_get` / `db_list` / `db_query` / `db_write` |
| Queue page thumbnails | the same artifact's files: `thumbs/<post-id>/slide-NN.jpg` (publish with `publish_files`, patch mode) |
| Instagram publishing and stats | Windsor.ai connector `instagram`: TechWorx → `17841438122178552` (@forgegatetech); Media and Estate Operations → `17841450093722489` (@weareforgegate). Each post document stores its `ig_account`. |
| Booking link (used in DMs) | https://calendar.app.google/uN18u155s3iJzi4dA |
| Website | https://forgegatemedia.com |

Public image URL for a slide: `https://raw.githubusercontent.com/ForgegateTW/forgegate-social-bot/main/posts/<post-id>/slide-NN.jpg`

## Database shape (artifact db)

- `settings/bot`: `{ paused: bool, changed_at }`. If `paused` is true, stop: do nothing except tell Zachary the bot is paused.
- `posts/<post-id>` where post-id is `YYYY-MM-DD-<division>`:
  `{ id, division, ig_account, publish_at (ISO, -05:00 or -04:00), title, caption, keyword, slides (count), status, image_urls[], ig_media_id?, permalink?, posted_at?, metrics?, error?, caption_edited_at?, hashtags?, hashtag_notes? }`
  - `hashtags`: the caption's hashtags in order. `hashtag_notes`: one short line on why they were picked (shown on the queue page).
  - `caption` here is what gets posted. Zachary can edit it on the queue page (that sets `caption_edited_at`), so it can differ from `post.json`. Never overwrite a caption that has `caption_edited_at`.
  - `status`: `queued` (will post) · `held` (Zachary held it: skip) · `posted` · `failed`
- `reports/latest`: `{ week, summary, written_at }` (the Friday report; overwrite each week)
- `learnings/log`: `{ entries: [ { week, note } ] }` (keep the last 12 entries; what worked and what didn't)
- `learnings/hashtags`: `{ updated_at, accounts: { "<ig_account>": { posts, avg_reach, avg_saves, avg_follows } }, tags: { "#tag": { uses, avg_reach, avg_saves, avg_follows, last_used, accounts: [] } } }`. Rebuilt from scratch every Friday (Job 3), so nothing is counted twice.

Every write to an existing document needs `ifVersion` from a fresh read.

## Brand rules (non-negotiable)

- Name: **ForgeGate**. Never "Forgegate.AI", "Agentic Solutions" or "Technology division". The rendered logo already carries the red serif G; never type a substitute wordmark.
- Division names exactly: ForgeGate TechWorx (red X), ForgeGate Media, ForgeGate Estate Operations. Only list the services above. Estate Operations never mentions leases, inspections or owner reporting. Media never lists web or systems. AI and automation messaging belongs only to TechWorx.
- No client names anywhere (no HRI, MDA, RIK or any real customer).
- No invented statistics, results, testimonials, dollar amounts or client stories. Opinions are fine when phrased as opinions.
- Voice: confident, calm, plain-spoken. Short sentences. One idea per carousel. 0–2 emoji per caption. Never: revolutionize, game-changer, unlock, supercharge, 10x, "in today's fast-paced world", em dashes.
- If something isn't covered here, keep it general or leave it out.

## What performs (keep applying, update from learnings)

- Real systems and concrete steps beat concepts. Lists and frameworks get saved.
- Hook on slide 1 that names the reader's problem or promises a specific list.
- One idea per slide: label, short title, 1–2 sentence body.
- CTA: "Comment KEYWORD and we'll DM you [the free guide]" plus "Save this".
- Hashtags: end every caption with **#ForgeGate** first, then 1–2 specific topic hashtags (3 in total). Instagram allows 5 at most per post. Hashtags help people find a post in search, not reach, so put search words in the caption text too.

## Comment keywords (fixed, set up once in ManyChat)

| Division | Keyword | DM sends |
| --- | --- | --- |
| TechWorx | `TECH` | the one-page AI employee template |
| Media | `MEDIA` | the 10-point brand checklist |
| Estate Operations | `ESTATE` | the property file checklist |

Every post's last slide and caption must use its division's keyword exactly, and promise exactly that guide. Don't invent new keywords or new freebies.

## Slide JSON (`posts/<post-id>/post.json`)

```json
{
  "id": "2026-11-16-techworx", "division": "techworx|media|estate",
  "publish_at": "2026-11-16T10:45:00-05:00", "keyword": "TECH",
  "title": "...", "caption": "...",
  "slides": [
    {"type": "cover", "label": "...", "title": "...", "body": "short sub-line"},
    {"type": "point", "label": "01 · ...", "title": "...", "body": "...", "you": "optional highlighted line"},
    {"type": "table", "label": "Example", "title": "...", "rows": [["Job", "..."], ["Tools", "..."]]},
    {"type": "cta", "label": "Free template", "title": "...", "body": "Comment TECH and we'll DM you ...", "keyword": "TECH"}
  ]
}
```

6–9 slides. Titles under ~45 characters, bodies under ~130. Render with `python3 render/render.py posts/<id>/post.json` (needs Pillow and numpy). Then look at every slide image yourself and fix anything clipped, cramped or off-brand before queuing.

## Job 1: Weekly plan (Sunday 7 p.m. ET)

1. Read `settings/bot`. If paused, stop and say so.
2. Clone this repo. Read `learnings/log` and last week's `posts/*` metrics in the db.
3. Research 15 minutes, max: WebSearch for what's trending this week in AI/automation for small business, brand and content marketing, and property operations. Skip anything you can't verify.
4. Pick 3 topics (one per division) that don't repeat any title in `posts/` from the last 8 weeks. Lean toward what the learnings say worked.
5. Write the 3 `post.json` files for Monday, Wednesday and Friday of the coming week (`publish_at` 10:45 ET, using -05:00 in winter and -04:00 in summer).
6. Hashtag check (5 minutes, max), for each post:
   - Read `learnings/hashtags` first. Keep using a tag whose average saves or reach beat its account's average after 3 or more uses; stop using one that fell below average after 3 or more uses. `#ForgeGate` is on every post, so never judge it.
   - Then WebSearch 2–3 candidate tags for the post's topic (hashtag-tool pages that show a tag's post count and related tags). Treat those counts as estimates: never put them in a caption, a report or a message as fact.
   - Pick 1–2 specific tags that match the post's one idea and its readers (small and local business owners) and are in active use; a rule of thumb is a mid-sized tag, not one with tens of millions of posts. Avoid broad tags (#business, #marketing, #love), tags whose recent posts look like spam or are off-topic, other companies' brand tags, and anything you couldn't check. Prefer a tested tag from the learnings over a new one, but try at least one new tag a week so the learnings keep growing.
   - The caption ends with `#ForgeGate` and then the chosen tags. Store `hashtags` and `hashtag_notes` (for example "used 4 times, saves above average" or "new: specific, active, fits the topic") on the post document in step 10.
7. Render, inspect every slide, fix, re-render.
8. Make 432×540 thumbnails and publish them to the queue artifact (`publish_files`, patch mode, `as: thumbs/<post-id>/slide-NN.jpg`).
9. Commit and push `posts/<post-id>/` to `main`. Confirm each raw URL returns 200.
10. Write each `posts/<post-id>` document with `status: "queued"`, its `ig_account` (by division, see above), the 2–10 `image_urls` in order, `hashtags` and `hashtag_notes`.
11. Finish with one short message: the 3 titles and dates, each post's hashtags, and that he can hold any of them or edit its caption on the queue page.

## Job 2: Post (Mon, Wed, Fri at 10:45 a.m. ET)

1. Read `settings/bot`. If paused, stop.
2. Find today's post: `db_query` posts where `publish_at` starts with today's date (ET). If none, stop and say "nothing queued for today".
3. If `status` is `held`, stop: say it was held and skipped. If `posted`, stop (never post twice).
4. Check every `image_urls` entry returns HTTP 200 and is a JPEG. If not, set `status: "failed"` with `error` and stop.
5. Check the caption from the database document (not `post.json`): at most 2,200 characters and at most 5 hashtags. If it breaks either, set `status: "failed"` with that reason and stop. If `#ForgeGate` is missing, post it anyway (Zachary may have removed it on purpose) and mention it in your final message.
6. Publish with Windsor `execute_action` → connector `instagram`, account = the post's `ig_account`, action `create_carousel_post`, params `{ image_urls, caption }`. This standing schedule is Zachary's explicit approval to publish queued, un-held posts. Publish exactly once; if the call times out, check the account's latest media before retrying.
7. On success, `update` the document: `status: "posted"`, `posted_at`, `ig_media_id` (from the action result). Then fetch `media_permalink` for it (`get_data`, fields `["media_id", "media_permalink", "timestamp"]`, `date_preset: "last_3dT"`, `force_refresh: true`) and store `permalink`.
8. On failure, set `status: "failed"` and `error` (plain words), and say what went wrong and what Zachary needs to do.

## Job 3: Weekly report (Friday 6 p.m. ET)

1. Read `settings/bot` (report even if paused).
2. For each post published in the last 14 days, pull its stats from Windsor (14, so every post is measured again once it's about a week old): `get_data`, connector `instagram`, accounts `["17841438122178552", "17841450093722489"]`, `date_preset: "last_14d"`, fields `["media_id", "media_permalink", "timestamp", "media_type", "media_reach", "media_views", "media_like_count", "media_comments_count", "media_saved", "media_shares", "media_follows"]`. Match rows to posts by `ig_media_id` (or by `timestamp` on the post date when the id wasn't stored), then `update` each post's `metrics` `{reach, views, likes, comments, saves, shares, follows}` and `permalink`.
3. Rebuild `learnings/hashtags` from every `posted` post that has `metrics` and is at least 3 days old: read the hashtags in the post's `caption` (what was actually posted, including Zachary's edits), then for each tag store its uses, average reach, saves and follows, when it was last used and on which accounts. Store each account's own averages too, because the two accounts have different audiences: always compare a tag with its account's average, never across accounts. Keep `#ForgeGate`'s count but leave it out of comparisons. Overwrite the document (`set`).
4. Write `reports/latest`: 5–8 plain lines: what posted, best and worst performer by saves and comments, one hashtag line, one thing to try next week. The hashtag line names tags that beat or trailed their account's average after 3 or more uses; until a tag has 3 uses, say it's too early to judge. With this few posts a week, call these early signals, not proof.
5. Append one entry to `learnings/log` (keep the last 12).
6. Finish with the same short summary as the final message.
