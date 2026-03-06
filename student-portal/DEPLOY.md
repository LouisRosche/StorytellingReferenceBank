# Deployment Guide — Student Portal

Free, static deployment via GitHub Pages. No server, no database, no cost.

---

## How It Works

The portal is a single HTML file that:
1. Validates the student's access code against SHA-256 hashes in `codes.json`
2. Fetches markdown files directly from the same repo
3. Renders them in-browser

Everything runs client-side. GitHub Pages serves the static files. No backend required.

---

## One-Time Setup (5 minutes)

### 1. Push the branch to main

Merge the `claude/student-access-library-8UMci` branch via pull request, or merge locally:

```bash
git checkout main
git merge claude/student-access-library-8UMci
git push origin main
```

### 2. Enable GitHub Pages

1. Go to the repo on GitHub: `github.com/LouisRosche/StorytellingReferenceBank`
2. **Settings → Pages** (left sidebar)
3. Under **Source**, select:
   - Branch: `main`
   - Folder: `/ (root)`
4. Click **Save**
5. Wait ~60 seconds. GitHub shows the live URL:

```
https://louisrosche.github.io/StorytellingReferenceBank/
```

### 3. Confirm the portal loads

Open:
```
https://louisrosche.github.io/StorytellingReferenceBank/student-portal/
```

Enter one of the starter codes (e.g. `INKWELL-2026`). The library should open.

---

## Before Each Class / Cohort

### Generate codes for your students

```bash
# From the repo root — one command per class section
python scripts/manage_student_codes.py generate "Spring2026-Period3" --count 30
python scripts/manage_student_codes.py generate "Spring2026-Period4" --count 30
```

This prints 30 codes like `VIVID-VOICE-6822` and updates `codes.json` with their hashes.

### Commit and push the updated codes.json

```bash
git add student-portal/codes.json
git commit -m "Add access codes for Spring 2026"
git push origin main
```

GitHub Pages updates automatically within ~60 seconds.

### Distribute codes to students

Share by any means — printed, emailed, posted to your LMS. One code per student is enough. Codes can be shared; the gate is intentionally light.

**What to tell students:**

> Go to: `https://louisrosche.github.io/StorytellingReferenceBank/student-portal/`
> Enter your access code when prompted. The code works for the whole semester.

---

## Ongoing Management

### List all active codes

```bash
python scripts/manage_student_codes.py list
```

### Revoke a code (e.g. if a code was widely shared)

```bash
python scripts/manage_student_codes.py revoke VIVID-VOICE-6822
git add student-portal/codes.json && git commit -m "Revoke code" && git push origin main
```

### Verify a specific code

```bash
python scripts/manage_student_codes.py verify INKWELL-2026
```

### Add a custom code (e.g. for a specific student or guest)

```bash
python scripts/manage_student_codes.py add MYSCHOOL-2026 --note "principal demo"
git add student-portal/codes.json && git commit -m "Add guest code" && git push origin main
```

---

## Starter Codes (Pre-loaded)

These 8 codes are active from day one:

| Code | Use for |
|------|---------|
| `INKWELL-2026` | Demo / instructor |
| `STORYWISE-2026` | Demo / instructor |
| `CRAFTWORK-2026` | Demo / instructor |
| `VOICEFOUND-2026` | Demo / instructor |
| `WRITEDARK-2026` | Demo / instructor |
| `SPARKPAGE-2026` | Demo / instructor |
| `ICEBERG-2026` | Demo / instructor |
| `CATALYST-2026` | Demo / instructor |

Revoke any you don't want active. Generate class-specific codes for students.

---

## Testing Locally

```bash
# From the repo root:
python -m http.server 8000

# Open:
# http://localhost:8000/student-portal/
```

The portal fetches markdown via relative paths, so the server must run from the repo root — not from inside `student-portal/`.

---

## Updating the Library

### Add a new resource

1. Edit `student-portal/library.json` — add an entry to the relevant category
2. Commit and push — live within ~60 seconds

```bash
git add student-portal/library.json
git commit -m "Add [resource name] to library"
git push origin main
```

### Remove a resource

Delete its entry from `library.json`. The markdown file can stay in the repo.

---

## Security Notes

**What the access code protects:** The UX. Students without a code see the lock screen.

**What it does not protect:** The underlying markdown files. Because this is a public GitHub repo, anyone who knows the file paths can read them directly. The code system is an organizational gate — appropriate for educational material you're happy to have public.

**If the content must stay private:** Make the repository private (requires GitHub Pro, $4/month) or use a free alternative host with password protection (Netlify Identity, Cloudflare Access). For most classroom use, a public repo is fine.

**The hashes in codes.json are safe to commit.** SHA-256 hashes cannot be reversed to recover the original codes.

**Do not commit `codes-admin.json`.** It contains plaintext codes and is gitignored by default.

---

## Repo Structure Reference

```
student-portal/
  index.html          Portal (lock screen + library browser)
  library.json        Curated content manifest — edit to add/remove resources
  codes.json          SHA-256 hashes of valid codes — commit this
  codes-admin.json    Plaintext code mapping — DO NOT commit (gitignored)
  DEPLOY.md           This file

scripts/
  manage_student_codes.py   Admin CLI for code management
```
