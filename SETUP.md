# 🕹️ SETUP — Arcade Profile for `KaustuvMohapatra`

Everything here goes into your **special profile repo**: a repo named exactly
`KaustuvMohapatra` (same as your username). You already have it — good.

```
KaustuvMohapatra/            <-- your profile repo
├── README.md               <-- the arcade README
├── github-metrics.svg      <-- auto-created by the Metrics action (don't hand-edit)
└── .github/
    └── workflows/
        ├── snake.yml        <-- contribution snake
        ├── metrics.yml      <-- full metrics dashboard  (needs 1 secret)
        ├── activity.yml     <-- recent-activity feed     (no secret)
        └── waka.yml         <-- coding time  (OPTIONAL — needs WakaTime)
```

---

## ✅ 1. Push the files

Copy `README.md` and the `.github/` folder into your `KaustuvMohapatra` repo and push to **main**.

```bash
cd KaustuvMohapatra
# copy README.md and .github/ in here, then:
git add .
git commit -m "feat: arcade profile README + automation"
git push origin main
```

## ✅ 2. Add ONE secret (for the Metrics dashboard)

`github-metrics.svg` needs a personal access token.

1. Create a **classic** token → https://github.com/settings/tokens
   → *Generate new token (classic)* → scopes: **`repo`** + **`read:user`** → copy it.
2. In the repo: **Settings → Secrets and variables → Actions → New repository secret**
   - **Name:** `METRICS_TOKEN`
   - **Value:** *(paste the token)*

> The snake and activity workflows need **no** secret — they use the built-in `GITHUB_TOKEN`.

## ✅ 3. Turn on Actions write access

**Settings → Actions → General → Workflow permissions →** select
**“Read and write permissions”** → Save.
(Without this, the snake/activity/metrics commits are rejected.)

## ✅ 4. First run (kickstart the widgets)

**Actions** tab → run each workflow once via **“Run workflow”**:
`🐍 Generate Snake` → `📊 GitHub Metrics` → `⌨️ Recent Activity`.

After the snake job finishes, an **`output` branch** appears containing the snake
SVGs — that's exactly what the README points to. ✔️

---

## 🔴 What updates automatically after this

| Widget | Trigger | Needs |
|---|---|---|
| Stats / Top-langs / Streak | live on every page view (vercel) | nothing |
| Activity graph / Trophies | live on every page view | nothing |
| Visitor counter / Followers / Stars | live | nothing |
| Repo pin cards | live | nothing |
| 🐍 Snake | push to main + every 12 h | nothing |
| 📊 Metrics dashboard | push to main + daily | `METRICS_TOKEN` |
| ⌨️ Recent activity feed | every 6 h | nothing |
| ⏱️ WakaTime | daily | WakaTime acct + key |

You gain followers / ship repos / change stats → the live widgets and the
scheduled jobs reflect it with **zero manual editing**.

---

## 🎮 Optional: WakaTime (coding-time bars)

1. Sign up at https://wakatime.com → install the editor plugin (VS Code etc.).
2. Copy your API key from https://wakatime.com/settings/api-key
3. Add repo secret **`WAKATIME_API_KEY`**.
4. Keep the `<!--START_SECTION:waka-->` block in the README (already there).

Don't use WakaTime? **Delete `waka.yml`** and the `waka` comment block — nothing else breaks.

---

## ✏️ Manual edit points (search the README for `EDIT`)

- **Footer social links** — already wired to your real Email / LinkedIn / X / Instagram / Twitch / Discord.
- **Featured Worlds** — change the `repo=` names to re-pin different repos.
- **Timezone** — `config_timezone` in `metrics.yml` (currently `Asia/Kolkata`).
- **Email** — currently `kaustuv4@outlook.com`.

## 🎨 The palette (keep everything cohesive)

| Role | Hex |
|---|---|
| BG (CRT black-purple) | `#0D0221` |
| Cyan (primary neon) | `#00F0FF` |
| Hot pink (accent) | `#FF2E97` |
| Purple (border) | `#7B2FF7` |
| Amber (highlight) | `#FFB800` |
| Lime (status OK) | `#39FF14` |

To retheme, find-replace these hex codes across `README.md`.

---

## 🩹 Troubleshooting

- **Snake image is a broken icon** → the Snake workflow hasn't run yet, or the
  `output` branch doesn't exist. Run `🐍 Generate Snake` once.
- **`github-metrics.svg` 404** → run `📊 GitHub Metrics` once; check `METRICS_TOKEN` exists.
- **Activity feed empty** → needs public events in the last 14 days; it fills within 6 h.
- **A repo card says “not found”** → that repo is private or renamed; update the `repo=` name.
- **Workflow commit rejected** → Step 3 (Read & write permissions) isn't enabled.

### ⚠️ Stats cards / repo pins / trophies show broken (503 / 402) — READ THIS

The **public** hosts for `github-readme-stats` (stats card, top-langs, the 6 repo
pins) and `github-profile-trophy` are shared by millions of profiles and
frequently hit their free quota → images intermittently break. This is the
single most common "why is my card broken" issue on GitHub profiles.

**Permanent fix — self-host on your own free Vercel (~10 min, then never touch it):**

1. Fork https://github.com/anuraghazra/github-readme-stats
2. Go to https://vercel.com → *Add New Project* → import your fork → **Deploy**.
   You get a URL like `https://your-stats.vercel.app`.
3. (For higher rate limits) add a `PAT_1` env var in Vercel = a classic token with
   `repo` scope, then redeploy.
4. In `README.md`, find-replace the host **only** on the stats/top-langs/pin URLs:
   `github-readme-stats.vercel.app` → `your-stats.vercel.app`
5. Same trick for trophies: fork https://github.com/ryo-ma/github-profile-trophy,
   deploy to Vercel, and swap `github-profile-trophy.vercel.app` → your host.

The `streak`, `activity-graph`, `capsule`, `typing`, `snake`, `metrics`, shields
and visitor-counter widgets are **not** affected and need no self-hosting.
