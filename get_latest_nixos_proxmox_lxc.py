#!/usr/bin/env python3
import sys
import requests
from pathlib import Path

HYDRA_BASE = "https://hydra.nixos.org"

def download_file(url: str, dest_path: Path):
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        written = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    written += len(chunk)
                    if total:
                        percent = written / total * 100
                        print(f"\r⬇ Downloading: {percent:.1f}% ({written // 1024} KB)", end="", flush=True)
        print("\n✅ Download complete.")

def download_proxmox_lxc(version: str, dest_dir: Path, force: bool) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)

    job_url = f"{HYDRA_BASE}/job/nixos/release-{version}/nixos.proxmoxLXC.x86_64-linux"
    if version == "unstable":
        job_url = f"{HYDRA_BASE}/job/nixos/nixos-unstable/nixos.proxmoxLXC.x86_64-linux"

    download_url = f"{job_url}/latest/download-by-type/file/system-tarball"

    print(f"🔗 Resolving latest image for version: {version}")
    head = requests.head(download_url, allow_redirects=True, timeout=30)
    final_url = head.url
    filename = Path(final_url).name
    out_path = dest_dir / filename

    if out_path.exists():
        if not force:
            reply = input(f"⚠ File {filename} already exists. Overwrite? [y/N] ").strip().lower()
            if reply != 'y':
                print("❌ Skipping download.")
                return out_path
        print("⚠ Overwriting existing file.")

    print(f"📦 Downloading from: {final_url}")
    download_file(final_url, out_path)
    print(f"✅ Saved to: {out_path}")
    return out_path

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download a NixOS Proxmox LXC image.")
    parser.add_argument("target_dir", nargs="?", default="/var/lib/vz/template/cache", help="Directory to save the image")
    parser.add_argument("--version", default="25.05", help="Release version (e.g. 25.05, 24.11, unstable). Default: 25.05")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite of existing files without prompting")
    args = parser.parse_args()

    try:
        download_proxmox_lxc(args.version, Path(args.target_dir), args.force)
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == "__main__":
    main()
