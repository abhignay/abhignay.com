#!/usr/bin/env python3
"""Downloads the photos, videos and PDFs from the old Wix site into docs/assets/.

The list of files is in assets.json. Run this once, while the Wix site is
still live (the "Fetch assets from Wix" GitHub Action runs it for you):

    python3 fetch_assets.py

Files that already exist are skipped, so it is safe to run again.
"""
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).parent
WIX = "https://static.wixstatic.com/media/54096e_"
MAX_BYTES = 95 * 1024 * 1024  # GitHub rejects files over 100 MB


def fetch(url, dest):
    if dest.exists():
        print("have   ", dest.name)
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        if len(data) > MAX_BYTES:
            print("TOO BIG", dest.name, f"({len(data) // 1048576} MB) - host it on YouTube instead")
            return False
        dest.write_bytes(data)
        print("fetched", dest.name)
        return True
    except Exception as err:  # keep going so one bad file does not stop the rest
        print("FAILED ", dest.name, "-", err)
        return False


def main():
    manifest = json.loads((ROOT / "assets.json").read_text(encoding="utf-8"))
    assets = ROOT / "docs" / "assets"
    jobs = []
    for folder, key, prefix in (("img", "images", WIX), ("video", "videos", ""), ("docs", "docs", "")):
        (assets / folder).mkdir(parents=True, exist_ok=True)
        jobs += [(prefix + src, assets / folder / name) for name, src in manifest[key].items()]
    results = [fetch(url, dest) for url, dest in jobs]
    print(f"\n{sum(results)} of {len(results)} files in place.")


if __name__ == "__main__":
    main()
