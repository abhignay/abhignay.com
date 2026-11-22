# abhignay.com

Source for [abhignay.com](https://www.abhignay.com): plain HTML and CSS, served by GitHub Pages from the `docs/` folder.

## Layout

```
src/              page content, one file per page (edit these)
src/post/         the old dev logs (closed series)
src/hopper-build-log/   the hopper build log: index.html plus one file per entry
build.py          wraps each page in the shared header and footer -> docs/
assets.json       list of photos, videos and PDFs to copy from the old Wix site
fetch_assets.py   downloads everything in assets.json into docs/assets/
docs/             the built site that GitHub Pages serves
  assets/style.css
  assets/img/     photos
  assets/video/   videos
  assets/docs/    PDFs
```

## First-time setup

1. Create an empty GitHub repository and push this folder to it.
2. While the Wix site is still live, open the repository's Actions tab, choose "Fetch assets from Wix" and press "Run workflow". It copies every photo, video and PDF into `docs/assets/` and commits them. (Or run `python3 fetch_assets.py` on your own computer and commit the result.) Until then, each missing photo shows a dashed box naming the file it expects.
3. In the repository, go to Settings, then Pages. Set the source to "Deploy from a branch", branch `main`, folder `/docs`.
4. Under "Custom domain" enter `www.abhignay.com` (the `docs/CNAME` file already says the same).
5. At your domain registrar, replace the Wix DNS records:
   - `www`: CNAME to `<your-github-username>.github.io`
   - root domain (`abhignay.com`): A records to `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
6. Once DNS has updated, tick "Enforce HTTPS" on the Pages settings screen.

Page file names match the old Wix addresses (`/tvc-hopper`, `/watchpi`, `/rocket`, `/post/june-july-2025` and so on), so existing links keep working.

## Editing

1. Change a file in `src/`. The lines above `---` set the page title, description and which nav item is highlighted.
2. Run `python3 build.py`.
3. Open `docs/index.html` in a browser to check, then commit and push.

- **Add a photo:** put the file in `docs/assets/img/` and write `{{img file.jpg | alt text | optional caption}}` in the page. On a dev log, wrap them in `<div class="figs figs-1">` (one photo), `figs-2` (a side-by-side pair) or `figs-3` (three or more in a row).
- **Add a video:** put the file in `docs/assets/video/` and write `{{video file.mp4 | optional caption}}`.
- **Post a hopper build log entry:** copy `src/hopper-build-log/entry-1.html` to a new file and write the entry, add a row for it at the top of the table in `src/hopper-build-log/index.html`, and update the "Latest" line in `src/tvc-hopper.html`.
- **Add a project to the Archive:** fill in one of the placeholder blocks in `src/archive.html` (the comment above them says how to turn one into a link).
- **Write about Hopper v2:** edit `src/hopperv2.html`. The contents list at the top links to each section.
- **Placeholders:** search `src/` for `class="placeholder"` to find every spot still waiting for your text.
