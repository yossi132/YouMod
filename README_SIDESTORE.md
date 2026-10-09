# Personal SideStore source for YouMod

SideStore source URL (add once under **Sources → +**):

`https://raw.githubusercontent.com/yossi132/YouMod/main/source.json`

The source starts empty until the first **published** IPA build succeeds. An unpublished draft release is not anonymously downloadable by SideStore.

## Build and update

1. Run [Build IPA with tweaks](https://github.com/yossi132/YouMod/actions/workflows/ipa.yml).
2. Supply a direct downloadable URL for your **own legitimately obtained** decrypted YouTube IPA. For Dropbox shared links, change `dl=0` to `dl=1`; verify download in Actions.
3. Ensure **Repository to build from** is `yossi132/YouMod` and **Bundle ID** remains `com.google.ios.youtube`.
4. **Publish to SideStore source** is optional and defaults off: checking it publishes the output IPA as a **public GitHub Release** and updates `source.json` with the actual IPA version, URL, size, and date. **Only select this if you have permission to redistribute the entire bundled IPA.** Otherwise, the output remains a draft and the source stays unchanged.
5. After publication, open SideStore and refresh your Sources page. Updates should appear when the new IPA's `CFBundleShortVersionString` is newer than the installed version.

The workflow preserves past entries for different YouTube versions, replacing an entry if rebuilding that same version. It does not silently publish draft builds or change installed apps.

**Important:** The source JSON is public. Publicly publishing a modified YouTube IPA distributes Google's proprietary app binary; possession of a decrypted IPA does not necessarily grant redistribution rights. For private personal builds, leave the publish option off and install the draft IPA manually, or arrange a private distribution endpoint accessible to SideStore.
