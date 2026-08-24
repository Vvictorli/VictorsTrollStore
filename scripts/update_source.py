#!/usr/bin/env python3
"""Generate a TrollStore-compatible source from GitHub release assets."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_VERSION = "2022-11-28"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def github_releases(repository: str) -> list[dict[str, Any]]:
    url = f"https://api.github.com/repos/{repository}/releases?per_page=20"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "VictorsTrollStore-source-updater",
        "X-GitHub-Api-Version": API_VERSION,
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API 请求失败 ({error.code}): {detail}") from error


def select_release_asset(
    releases: list[dict[str, Any]], pattern: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    matcher = re.compile(pattern, re.IGNORECASE)
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        for asset in release.get("assets", []):
            if matcher.search(asset.get("name", "")):
                return release, asset
    raise RuntimeError(f"最近 20 个正式 Release 中没有匹配资源: {pattern}")


def compact_release_notes(body: str | None) -> str:
    if not body:
        return "上游项目发布了新版本。"
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return "\n".join(lines)[:1000]


def release_version(tag_name: str, pattern: str | None = None) -> str:
    if not pattern:
        return tag_name.lstrip("v")
    match = re.search(pattern, tag_name)
    if not match:
        raise RuntimeError(f"无法从 Tag 提取版本号: {tag_name}")
    return match.group(1)


def build_app(app_config: dict[str, Any]) -> dict[str, Any]:
    release, asset = select_release_asset(
        github_releases(app_config["repository"]), app_config["assetPattern"]
    )
    published_at = release.get("published_at") or release.get("created_at", "")
    return {
        "name": app_config["name"],
        "bundleIdentifier": app_config["bundleIdentifier"],
        "version": release_version(
            str(release["tag_name"]), app_config.get("versionPattern")
        ),
        "versionDate": published_at[:10],
        "versionDescription": compact_release_notes(release.get("body")),
        "size": asset["size"],
        "downloadURL": asset["browser_download_url"],
        "developerName": app_config["developerName"],
        "localizedDescription": app_config["localizedDescription"],
        "iconURL": app_config["iconURL"],
    }


def generate_source(source_path: Path, apps_path: Path) -> dict[str, Any]:
    source = load_json(source_path)
    source_url = os.environ.get("SOURCE_URL")
    if source_url:
        source["sourceURL"] = source_url
    source["apps"] = [build_app(app) for app in load_json(apps_path)]
    return source


def write_if_changed(output_path: Path, source: dict[str, Any]) -> bool:
    content = json.dumps(source, ensure_ascii=False, indent=2) + "\n"
    if output_path.exists() and output_path.read_text(encoding="utf-8") == content:
        return False
    output_path.write_text(content, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "config/source.json")
    parser.add_argument("--apps", type=Path, default=ROOT / "config/apps.json")
    parser.add_argument("--output", type=Path, default=ROOT / "apps.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        changed = write_if_changed(
            args.output, generate_source(args.source, args.apps)
        )
    except (KeyError, OSError, ValueError, RuntimeError) as error:
        print(f"更新失败: {error}", file=sys.stderr)
        return 1
    print("源已更新" if changed else "源已是最新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
