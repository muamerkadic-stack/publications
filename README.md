# Google Scholar → Google Sites publication list (free version)

Every Monday a GitHub Action reads your Google Scholar profile with the free
`scholarly` library, rebuilds `index.html`, and publishes it with GitHub Pages.
Your Google Sites page embeds that page, so it updates by itself. No account or
API key is needed besides GitHub.

Your Scholar ID (`opodZE4AAAAJ`) is already set in `.github/workflows/update.yml`.

## Setup (about 5 minutes)

1. **GitHub repository** – create a new **public** repository (e.g. `publications`) and
   upload all files from this folder, including `.github/workflows/update.yml`.
   (With "Add file → Upload files", drag the whole folder in so the `.github` path is kept.)
2. **First run** – *Actions* tab → **Update publications** → **Run workflow**.
   After a minute or two, `index.html` appears in the repository.
3. **GitHub Pages** – *Settings → Pages* → Source: **Deploy from a branch**,
   branch `main`, folder `/ (root)` → Save. Your list will be at
   `https://YOUR-GITHUB-USERNAME.github.io/publications/`.
4. **Google Sites** – open your page, **Insert → Embed → By URL**, paste the link above,
   insert it, drag the box to make it tall enough, then **Publish**.

## Options

- **Full author lists**: by default each entry shows title, venue/year and citation
  count (that's what the Scholar profile page provides in one request). To also show
  every paper's full author list, set `FILL_DETAILS: "1"` in the workflow file. This
  makes one extra request per paper, so it's slower and more often blocked.
- **Frequency**: edit the `cron` line in the workflow file.
- **Look**: edit the `<style>` block in `update_publications.py`.

## If a run fails

Google sometimes blocks requests from GitHub's servers (CAPTCHA). The script then
retries through free proxies, and if all attempts fail it leaves the existing list
online and exits with an error. Just run it again later from the *Actions* tab, or
wait for the next weekly run. If it fails every time, the SerpApi version is the
reliable alternative.

GitHub pauses scheduled workflows in repositories with no activity for 60 days;
if that happens, re-enable it in the *Actions* tab.
