# Evidence for the post log

Screenshots, small charts and short clips that prove a `docs/POST_LOG.md` entry
(decision E-58). Step 6 writes the LinkedIn and X posts from the post log and links
here, so every claim in a post has its proof in the repo.

## Where files go

```
docs/evidence/
  step1/
    PL-011_secret-blocked.png
  step2/
    PL-0xx_short-name.png
```

- One folder per step: `stepN/`.
- Name every file after its post log entry: `PL-<number>_<two-to-four-words>.png`.
- If one entry needs several images, add a letter: `PL-016a_...`, `PL-016b_...`.
- Write the path in the entry's **Evidence** line, so the two always point at each other.

## Rules before you save a file here

This folder is public. Check every image before you commit it.

1. **No secrets.** No real API key, password, token or `.env` content, even partly hidden. A fake test key made by the guide's leak test is fine.
2. **No private details.** No email address, phone number, other people's names, open browser tabs or desktop notifications. Crop to the part that proves the point.
3. **Small files.** PNG for terminal and screen captures, JPG for photos, about 500 KB at most. Use the Windows Snipping Tool (`Win + Shift + S`) and save the cropped area only.
4. **Videos stay out of Git.** Screen recordings and demo clips are large. Keep them in a local folder outside the project, for example `Documents\Emole media\stepN\`, named the same way (`PL-0xx_...mp4`). Only a short GIF under 2 MB may live here.
5. **Real events only.** Capture the actual run. Never stage or edit a screenshot to show a result that did not happen.