#!/usr/bin/env python3
"""Update the SideStore AltSource from a successfully built, accessible IPA."""
import argparse
import datetime as dt
import json
import pathlib
import plistlib
from urllib.parse import urlsplit
from zipfile import ZipFile

# Pin the standard YouTube icon for all SideStore source updates.
YOUTUBE_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/YouTube_social_white_squircle_%282024%29.svg/500px-YouTube_social_white_squircle_%282024%29.svg.png"


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
    parser.add_argument("--youmod-version", default="")
    args = parser.parse_args()

    if urlsplit(args.download_url).scheme != "https":
        raise ValueError("A public HTTPS direct IPA download URL is required")
    bundle_id, version = ipa_metadata(args.ipa)
    if bundle_id != "com.google.ios.youtube":
        raise ValueError(f"Unexpected bundle ID {bundle_id!r}; refusing to change the source")

    app_description = (
        f"YouTube {version} with YouMod {args.youmod_version}. "
        if args.youmod_version else f"YouTube {version} with YouMod. "
    ) + (
        "Customize playback and interface settings, use SponsorBlock, "
        "and access the optional tweaks selected for this build."
    )

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
            "localizedDescription": app_description,
            "iconURL": YOUTUBE_ICON_URL,
            "versions": [],
        }
        apps.append(app)

    # Restore the standard YouTube icon even when older source data exists.
    app["iconURL"] = YOUTUBE_ICON_URL
    # Refresh the app listing itself, not only the per-version release notes.
    app["localizedDescription"] = app_description

    release = {
        "version": version,
        "date": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "downloadURL": args.download_url,
        "size": args.ipa.stat().st_size,
        "localizedDescription": (
            f"YouTube {version} with YouMod {args.youmod_version}. Includes YouMod playback "
            "and interface customization, SponsorBlock, and the optional tweaks "
            "selected for this build."
            if args.youmod_version else
            f"YouTube {version} with YouMod. Includes playback and interface "
            "customization, SponsorBlock, and the optional tweaks selected for this build."
        ),
    }
    previous = [item for item in app.get("versions", []) if item.get("version") != version]
    app["versions"] = [release, *previous]
    # Older SideStore builds can require these app-level fields even when
    # all version data is supplied via the modern `versions` array.
    app["version"] = version
    app["versionDate"] = release["date"]
    app["versionDescription"] = release["localizedDescription"]
    app["downloadURL"] = args.download_url
    app["size"] = release["size"]
    args.source.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated SideStore source for {bundle_id} {version}; {len(app['versions'])} version(s)")


if __name__ == "__main__":
    main()
