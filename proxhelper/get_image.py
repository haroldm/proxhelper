#!/usr/bin/env python3
import typer
import sys
import requests
from pathlib import Path
from typing_extensions import Annotated

HYDRA_BASE = "https://hydra.nixos.org"

app = typer.Typer()

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

def get_nixos_lxc(version: str, dest_dir: Path, force: bool) -> Path:
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

def get_nixos_vma(version: str, dest_dir: Path, force: bool) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)

    job_url = f"{HYDRA_BASE}/job/nixos/release-{version}/nixos.proxmoxImage.x86_64-linux"
    if version == "unstable":
        job_url = f"{HYDRA_BASE}/job/nixos/nixos-unstable/nixos.proxmoxImage.x86_64-linux"

    download_url = f"{job_url}/latest/download-by-type/file/vma"

    print(f"🔗 Resolving latest vma image for version: {version}")
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

def get_nixos_iso(version: str, dest_dir: Path, force: bool) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)

    job_url = f"{HYDRA_BASE}/job/nixos/release-{version}/nixos.iso_minimal.x86_64-linux"
    if version == "unstable":
        job_url = f"{HYDRA_BASE}/job/nixos/nixos-unstable/nixos.iso_minimal.x86_64-linux"

    download_url = f"{job_url}/latest/download-by-type/file/iso"

    print(f"🔗 Resolving latest minimal ISO image for version: {version}")
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

def validate_choices(value: str, valid: list[str], name: str):
    if value not in valid:
        raise typer.BadParameter(f"{name} must be one of {valid}")
    return value

@app.command()
def get_image(
    type: Annotated[str, typer.Option(help="Image type (lxc, vm)")],
    os: Annotated[str, typer.Option(help="Operating system (e.g., nixos)")],
    version: Annotated[str, typer.Option(help="OS version (e.g. 25.05 or 'unstable')")],
    dest_dir: Annotated[Path, typer.Option(help="Directory to save the image")] = Path("placeholder"),
    force: Annotated[bool, typer.Option(help="Overwrite existing file if present")] = False
):
    type = validate_choices(type, ["lxc", "iso", "vma"], "type")
    os = validate_choices(os, ["nixos"], "os")

    if dest_dir == Path("placeholder"):
        if type == "lxc":
            dest_dir = Path("/var/lib/vz/template/cache")
        elif type == "iso":
            dest_dir = Path("/var/lib/vz/template/iso")
        elif type == "vma":
            dest_dir = Path("/var/lib/vz/dump")
   
    if os == "nixos":
        if type == "lxc":
            return get_nixos_lxc(version, dest_dir, force)
        elif type == "iso":
            return get_nixos_iso(version, dest_dir, force)
        elif type == "vma":
            return get_nixos_vma(version, dest_dir, force)

    print("❌ Unsupported combination of --type and --os.")

if __name__ == "__main__":
    app()
