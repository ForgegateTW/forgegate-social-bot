# ForgeGate Social Bot

Plans, designs and posts three Instagram carousels a week for ForgeGate, one per division (TechWorx, Media, Estate Operations). Scheduled Claude sessions run it by following [RUNBOOK.md](RUNBOOK.md). Zachary holds or pauses posts from the **ForgeGate Post Queue** page.

- `render/render.py` turns a `posts/<id>/post.json` into 1080×1350 slides in the division's locked style.
- `posts/` holds every post and its slides. They're public because Instagram fetches slides from these links.
- `assets/` holds the ForgeGate art, logo and fonts (Tenor Sans, DM Serif Display, Figtree, IBM Plex Mono: all SIL Open Font License).
- `MANYCHAT.md` has the comment-keyword DMs.

No passwords, keys or private data belong in this repo.
