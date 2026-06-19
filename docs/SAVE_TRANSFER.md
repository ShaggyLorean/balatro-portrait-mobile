# Bringing Your Save From the Official App

The portrait build is a separate app (`com.unofficial.balatro`), so it starts
with an empty save. If you already played the official Google Play Balatro, you
can move that progress over without root and without Shizuku.

This works because the official Play build backs its save up to **Google Play
Games Services**, and Google lets you export that data through **Google Takeout**.

> **What transfers:** unlocks, stats, money, stake/deck progression (`profile.jkr`
> and `meta.jkr`). An in-progress run usually is not part of the cloud snapshot,
> so don't expect a half-finished run to come across. Back up the portrait app's
> current save before overwriting it.

## 1. Export from Google Takeout

1. Go to [takeout.google.com](https://takeout.google.com).
2. Click **Deselect all**, then tick only **Google Play Games Services**.
3. Request the export. You get an email quickly, and a download link within a few
   minutes. The archive is small.
4. Download and keep the `.zip` (for example `takeout-XXXXXXXX-001.zip`).

## 2. Convert the snapshots to `.jkr` files

Inside the export, each save is a Play Games snapshot folder like
`Saved Games/1-meta.jkr/` with the real blob stored as `Data.bin`. The helper
script pulls those out and renames them for you:

```sh
python tools/import_save.py takeout-XXXXXXXX-001.zip
```

It writes the recovered files to `balatro-save-import/game/<slot>/`, for example:

```text
balatro-save-import/game/1/meta.jkr
balatro-save-import/game/1/profile.jkr
```

The leading number on each snapshot (`1-meta.jkr`) is the Balatro profile slot,
so most people end up with `game/1/`.

If you prefer to do it by hand, just rename `Saved Games/1-meta.jkr/Data.bin` to
`meta.jkr` and `Saved Games/1-profile.jkr/Data.bin` to `profile.jkr`.

## 3. Drop the files into the portrait app

The portrait build keeps profile saves in its own storage at `game/<slot>/`.
Copy the `meta.jkr` and `profile.jkr` from step 2 into the matching slot folder.

**No root (Material Files / SAF):**

1. Launch the portrait app once so the save folders exist, then close it.
2. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files).
3. Material Files menu -> **Add storage...** -> **External storage** -> pick the
   **Balatro** app -> **Use this folder**.
4. Open `game/1/` (create the `1` folder if it isn't there yet) and paste the two
   `.jkr` files.

**Root:**

```text
/data/user/0/com.unofficial.balatro/files/save/game/1/
```

Copy the files there with a root file manager, then fix ownership so the app can
read them (match the surrounding files, e.g. `chown -R u0_aNNN:u0_aNNN` and
`restorecon`).

## 4. Launch and check

Open the portrait app and load profile 1. Your unlocks and progression should be
there.

> Mods live in a different place (`ASET/Mods/`), saves live in `game/<slot>/`.
> Don't mix the two folders. See [MODDING.md](MODDING.md) for the mod side.

Method documented by the community in
[issue #31](https://github.com/ShaggyLorean/balatro-portrait-mobile/issues/31).
