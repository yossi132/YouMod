#!/usr/bin/env python3
"""Update the SideStore AltSource from a successfully built, accessible IPA."""
import argparse
import datetime as dt
import json
import pathlib
import plistlib
from urllib.parse import urlsplit
from zipfile import ZipFile


def ipa_metadata(path: pathlib.Path):
    with ZipFile(path) as archive:
        manifests = [
            name for name in archive.namelist()
            if name.startswith("Payload/")
            and name.endswith(".app/Info.plist")
            and name.count("/") == 2
        ]
        if len(manifests) != 1:
            raise ValueError(f"Expected one app's Info.plist, found {len(manifests)}")
        info = plistlib.loads(archive.read(manifests[0]))
    bundle_id = str(info["CFBundleIdentifier"]).strip()
    version = str(info["CFBundleShortVersionString"]).strip()
    if not bundle_id or not version:
        raise ValueError("IPA is missing its bundle ID or short version")
    return bundle_id, version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ipa", type=pathlib.Path, required=True)
    parser.add_argument("--source", type=pathlib.Path, required=True)
    parser.add_argument("--download-url", required=True)
    args = parser.parse_args()

    if urlsplit(args.download_url).scheme != "https":
        raise ValueError("A public HTTPS direct IPA download URL is required")
    bundle_id, version = ipa_metadata(args.ipa)
    if bundle_id != "com.google.ios.youtube":
        raise ValueError(f"Unexpected bundle ID {bundle_id!r}; refusing to change the source")

    source = json.loads(args.source.read_text(encoding="utf-8"))
    apps = source.setdefault("apps", [])
    if len(apps) > 1 or (apps and apps[0].get("bundleIdentifier") != bundle_id):
        raise ValueError("Unexpected source app configuration; refusing to overwrite it")
    if apps:
        app = apps[0]
    else:
        app = {
            "name": "YouTube (YouMod)",
            "bundleIdentifier": bundle_id,
            "developerName": "yossi132",
            "localizedDescription": "Personal YouMod-enhanced YouTube builds.",
            "iconURL": "https://raw.githubusercontent.com/yossi132/YouMod/main/Icon.png",
            "versions": [],
        }
        apps.append(app)

    release = {
        "version": version,
        "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "downloadURL": args.download_url,
        "size": args.ipa.stat().st_size,
    }
    previous = [item for item in app.get("versions", []) if item.get("version") != version]
    app["versions"] = [release, *previous]
    # Older SideStore builds can require these app-level fields even when
    # all version data is supplied via the modern `versions` array.
    app["version"] = version
    app["versionDate"] = release["date"]
    app["downloadURL"] = args.download_url
    app["size"] = release["size"]
    args.source.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated SideStore source for {bundle_id} {version}; {len(app['versions'])} version(s)")


if __name__ == "__main__":
    main()
