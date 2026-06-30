#!/usr/bin/env python3
"""Build a desktop app for Ascent Inventory (macOS .app or Windows .exe folder).

Prerequisites:
  pip install -r requirements.txt -r requirements-build.txt

Config (pick one):
  - config/firebase_config.py exists locally, or
  - set FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID, API_BASE_URL env vars

Usage:
  python scripts/build_desktop.py          # macOS or Windows
  python scripts/build_desktop.py --zip    # also create a zip for sharing
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "firebase_config.py"
DIST = ROOT / "dist"
APP_NAME = "Ascent Inventory"
DEFAULT_API_URL = "https://ascent-inventory.onrender.com"


def ensure_config() -> None:
    if CONFIG.is_file():
        text = CONFIG.read_text()
        if "127.0.0.1" in text or "localhost" in text:
            print("Warning: firebase_config.py still points at localhost.")
            print(f"Set API_BASE_URL to {DEFAULT_API_URL} before distributing.")
        return

    api_key = os.environ.get("FIREBASE_API_KEY")
    auth_domain = os.environ.get("FIREBASE_AUTH_DOMAIN")
    project_id = os.environ.get("FIREBASE_PROJECT_ID")
    api_url = os.environ.get("API_BASE_URL", DEFAULT_API_URL)

    if not all([api_key, auth_domain, project_id]):
        print("Missing config/firebase_config.py")
        print("Copy config/firebase_config.example.py → config/firebase_config.py")
        print("Or set FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID env vars.")
        sys.exit(1)

    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(
        f'''import os

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "{api_key}")
FIREBASE_AUTH_DOMAIN = os.environ.get("FIREBASE_AUTH_DOMAIN", "{auth_domain}")
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "{project_id}")
API_BASE_URL = os.environ.get("API_BASE_URL", "{api_url}")
''',
        encoding="utf-8",
    )
    print(f"Wrote {CONFIG} from environment variables.")


def _separator() -> str:
    return ";" if platform.system() == "Windows" else ":"


def _add_data(src: Path, dest: str) -> str:
    return f"{src}{_separator()}{dest}"


APP_ICON_PNG = ROOT / "media" / "app-icon.png"


def _make_mac_icns(png: Path) -> Path:
    icns = ROOT / "media" / "app-icon.icns"
    if icns.is_file():
        return icns

    try:
        from PIL import Image

        iconset = ROOT / "media" / "app-icon.iconset"
        if iconset.exists():
            shutil.rmtree(iconset)
        iconset.mkdir()

        img = Image.open(png).convert("RGBA")
        spec = [
            ("icon_16x16.png", 16),
            ("icon_16x16@2x.png", 32),
            ("icon_32x32.png", 32),
            ("icon_32x32@2x.png", 64),
            ("icon_128x128.png", 128),
            ("icon_128x128@2x.png", 256),
            ("icon_256x256.png", 256),
            ("icon_256x256@2x.png", 512),
            ("icon_512x512.png", 512),
            ("icon_512x512@2x.png", 1024),
        ]
        for name, size in spec:
            img.resize((size, size), Image.Resampling.LANCZOS).save(iconset / name)

        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(icns)],
            check=True,
            capture_output=True,
        )
        shutil.rmtree(iconset)
        print(f"Created {icns}")
        return icns
    except Exception as exc:
        print(f"Could not create .icns ({exc}); using PNG for app icon.")
        return png


def _icon_path() -> Path:
    png = APP_ICON_PNG
    if not png.is_file():
        print("Missing media/app-icon.png")
        sys.exit(1)

    if platform.system() == "Darwin":
        return _make_mac_icns(png)

    if platform.system() == "Windows":
        ico = ROOT / "media" / "app-icon.ico"
        if ico.is_file():
            return ico
        try:
            from PIL import Image

            img = Image.open(png)
            img.save(
                ico,
                format="ICO",
                sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
            )
            print(f"Created {ico}")
            return ico
        except ImportError:
            print("Tip: pip install pillow for a proper Windows .ico icon (using .png for now).")
            return png

    return png


def _codesign_mac_app(app: Path) -> None:
    """Ad-hoc sign so Gatekeeper is less likely to mark the app as damaged."""
    if not app.is_dir():
        return
    result = subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(app)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Warning: codesign failed:", result.stderr.strip() or result.stdout)
    else:
        print(f"Signed: {app}")


def _write_mac_install_notes() -> None:
    notes = DIST / "INSTALL-MAC.txt"
    notes.write_text(
        """Ascent Inventory — macOS install

1. Unzip Ascent-Inventory-macOS.zip
2. Drag "Ascent Inventory.app" to Applications

If macOS says the app is "damaged" or won't open:
  This is normal for apps shared outside the App Store (not Apple-notarized).

  Fix — pick one:
  A) Right-click "Ascent Inventory.app" → Open → Open (first time only)
  B) In Terminal:
     xattr -cr "/Applications/Ascent Inventory.app"

3. Sign in with your Firebase email and password.
""",
        encoding="utf-8",
    )


def _zip_output(system: str) -> Path | None:
    if system == "Darwin":
        src = DIST / f"{APP_NAME}.app"
        if not src.is_dir():
            return None
        _codesign_mac_app(src)
        _write_mac_install_notes()
        zip_path = DIST / "Ascent-Inventory-macOS.zip"
        if zip_path.exists():
            zip_path.unlink()
        subprocess.run(
            ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(src), str(zip_path)],
            check=True,
        )
        return zip_path

    if system == "Windows":
        src = DIST / APP_NAME
        if not src.is_dir():
            return None
        zip_path = DIST / "Ascent-Inventory-Windows"
        if zip_path.with_suffix(".zip").exists():
            zip_path.with_suffix(".zip").unlink()
        shutil.make_archive(str(zip_path), "zip", DIST, APP_NAME)
        return zip_path.with_suffix(".zip")

    return None


def build(make_zip: bool = False) -> None:
    ensure_config()

    datas = [
        _add_data(ROOT / "media", "media"),
        _add_data(ROOT / "frontend" / "styles.qss", "frontend"),
        _add_data(CONFIG, "config"),
    ]

    icon = _icon_path()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        APP_NAME,
        "--windowed",
        f"--icon={icon}",
        *[f"--add-data={d}" for d in datas],
        "--hidden-import=config.firebase_config",
        "--hidden-import=backend.auth_client",
        "--hidden-import=backend.api_server",
        "--hidden-import=frontend.workers",
        "--collect-submodules=backend",
        "--collect-submodules=frontend",
        "--collect-all=PyQt6",
        str(ROOT / "main.py"),
    ]

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)

    system = platform.system()
    if system == "Darwin":
        app = DIST / f"{APP_NAME}.app"
        _codesign_mac_app(app)
        print(f"\nBuilt: {app}")
        print("Install: drag to Applications, then open from Launchpad or Dock.")
        print("If sharing via zip, recipients may need: Right-click → Open (first time)")
        print("  or run: xattr -cr \"/Applications/Ascent Inventory.app\"")
    elif system == "Windows":
        exe = DIST / APP_NAME / f"{APP_NAME}.exe"
        print(f"\nBuilt: {exe}")
        print("Copy the whole 'Ascent Inventory' folder to each PC.")
        print("Right-click the .exe → Send to → Desktop (create shortcut).")
    else:
        print(f"\nBuilt in: {DIST / APP_NAME}")

    if make_zip:
        zip_file = _zip_output(system)
        if zip_file:
            print(f"Zip for sharing: {zip_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Ascent Inventory desktop app")
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Create a zip file in dist/ for sharing",
    )
    args = parser.parse_args()
    build(make_zip=args.zip)


if __name__ == "__main__":
    main()
