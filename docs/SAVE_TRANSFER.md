# Bringing Your Save Across

The portrait build is a separate app (`com.unofficial.balatro`), so it starts
with an empty save. You can carry your unlocks and progression over from either:

- **Desktop Balatro** (Steam/standalone) — the save folder, e.g. `%APPDATA%\Balatro`
  on Windows.
- **The official Play Store app** — exported with **Google Takeout** (no root, no
  Shizuku), since that build backs its save up to Google Play Games Services.

> **What transfers:** unlocks, stats, money, stake/deck progression (`profile.jkr`
> and `meta.jkr`). An in-progress run is not carried over. The Zygisk path doesn't
> need any of this; it runs on the official app and keeps that app's save.

## Easiest: bake it into the build

`build.py` can fold a save straight into the APK. On the first launch it drops
the save into an empty profile, so there's nothing to copy by hand.

```sh
# Desktop save folder (Windows shown; point at your own Balatro save folder)
python build.py --import-save "%APPDATA%\Balatro"

# Or a Google Takeout export from the official app
python build.py --import-save takeout-XXXXXXXX-001.zip
```

Run without the flag and the build asks anyway (it offers your detected desktop
save). On Termux the helper prompts for a Takeout zip path. Install the APK,
launch it, and your progress is on profile 1.

It only fills an **empty** profile, so it never overwrites a save you already
have on the device.

## Manual route (already built, or no rebuild)

If you'd rather not rebuild, convert the save and drop the files in yourself.

**1. Get the `.jkr` files.** From a Takeout export:

```sh
python tools/import_save.py takeout-XXXXXXXX-001.zip
```

This writes `balatro-save-import/game/<slot>/meta.jkr` and `profile.jkr` (the
leading number on a `1-meta.jkr` snapshot is the profile slot). By hand, just
rename `Saved Games/1-meta.jkr/Data.bin` to `meta.jkr` and the profile one to
`profile.jkr`. A desktop save already has plain `1/meta.jkr`, `1/profile.jkr`.

**2. Drop them into the portrait app at `game/<slot>/`.**

No root (Material Files / SAF):

1. Launch the portrait app once so the save folders exist, then close it.
2. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files).
3. Menu -> **Add storage...** -> **External storage** -> pick the **Balatro** app
   -> **Use this folder**.
4. Open `game/1/` (create the `1` folder if needed) and paste the two `.jkr` files.

Root:

```text
/data/user/0/com.unofficial.balatro/files/save/game/1/
```

Copy the files there, then fix ownership/labels so the app can read them (match
the surrounding files, e.g. `chown -R u0_aNNN:u0_aNNN` and `restorecon`).

**3.** Launch and load profile 1. Your unlocks and progression should be there.

> Mods live in `ASET/Mods/`, saves live in `game/<slot>/` — different folders,
> don't mix them. See [MODDING.md](MODDING.md) for the mod side.

The Takeout route was documented by the community in
[issue #31](https://github.com/ShaggyLorean/balatro-portrait-mobile/issues/31).
