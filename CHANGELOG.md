# Changelog

All notable changes to Balatro Portrait Mobile.

## [v2.6.3](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.6.3) - 2026-06-19

The headline here is Steamodded. Newer Steamodded builds ship Lovely patches that
target vanilla Balatro UI code, and the portrait rework had moved that code, so
starting a run with Steamodded loaded could crash on the blind select screen.
This release makes the portrait UI handle modded content directly instead of
leaning on those patches landing.

**Steamodded compatibility**

- **Starting a run with Steamodded no longer crashes on the blind select.** The
  blind name and description boxes now render Steamodded's parsed localization
  through `SMODS.localize_box`, with a plain-string fallback for vanilla. This
  covers both the blind-choice cards and the blind info popup.
- **Hand and discard limits have safe defaults.** `play_limit`, `discard_limit`,
  and `no_limit` are seeded in the starting params, so mods that read them at the
  start of a run no longer hit a nil value.
- **Fixed two variable-shadowing bugs that surfaced under mods.** A local named
  `type` was shadowing Lua's builtin inside the blind description code, and a
  local named `os` was shadowing the `os` library during startup.

**Save transfer**

- **Carry your save into the portrait app**, from desktop Balatro or the official
  Play Store app (via Google Takeout, no root or Shizuku). `build.py --import-save`
  bakes the save into the APK and the first launch restores it into an empty
  profile; `tools/import_save.py` and a manual copy still work too. See
  [docs/SAVE_TRANSFER.md](docs/SAVE_TRANSFER.md).

**Mods**

- **One-command Steamodded.** `build.py --steamodded` fetches a version you pick
  from GitHub and bundles it into the APK. It installs itself on the first launch;
  restart the game once and it is active. See [docs/MODDING.md](docs/MODDING.md).
- **The mod folder moved to `game/Mods/`.** This sits inside the LOVE save dir, so
  a bundled mod can install itself without root. Put manual mods there instead of
  the old `ASET/Mods/`. (The Zygisk path keeps using `ASET/Mods/`.)

**Other**

- The rootless APK now forces portrait at the SDL layer during the build, so the
  orientation is locked even before the Lua side starts.

## [v2.6.2](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.6.2) - 2026-06-17

This is a small but important polish release for the portrait HUD and shop flow.
The focus is not a new install path this time; it is making the existing Android
paths feel less patched-together in real play.

**Portrait gameplay fixes**

- **Consumable Sell/Use buttons no longer fight the right edge of the screen.**
  The tray button column is now drawn after the selected card and nudged inward
  only when it would overflow. This keeps the button visible without moving the
  card row or breaking the empty-slot outlines.
- **Booster-pack USE buttons reveal below the selected card instead of covering
  the card art.** Booster cards lift a little higher in portrait, the hand row
  sits clear of the selected pack card, and the USE button is anchored in the
  revealed space below it.
- **Shop Open/Redeem/Buy labels sit better inside the larger portrait buttons.**
  The button boxes stay anchored to the card, but text nodes now support a local
  draw offset, so the labels can be optically centered without changing the
  global font metrics or Readabletro's font patch.
- **Partial joker and consumable rows stay lined up with their outlines.** When
  you have fewer cards than the row limit, held cards now stay centered in their
  fixed portrait slots instead of spreading away from the faint empty outlines.
- **Tag hover popups keep fitting after layout settles.** Tag tooltips are
  re-fitted while they exist, so measured-width changes no longer leave a popup
  hanging off the side of the screen.

**Build and install flow**

- **Termux builds now ask the same user-facing questions as PC builds.**
  `termux-build.sh` prompts for Readabletro and CRT-disable choices, while still
  accepting `--readabletro`, `--no-readabletro`, `--crt`, and `--no-crt` for
  scripted runs.
- **The Zygisk module metadata is bumped to 2.6.2.** The release ZIP is rebuilt
  from the same portrait sources as the rootless builder.

**Docs**

- The README has been simplified around the real user choice: rootless APK
  builder, no-PC Termux build, experimental Zygisk module, or experimental iOS.
  The long Termux and Zygisk details now live in their own docs pages instead of
  crowding the first install path.

**Release artifact**

- `balatro_portrait.zip` is the Zygisk module for rooted users who want to keep
  the official Play Store app installed.
- Rootless APK builds are still built locally and are not uploaded because they
  contain the user's own game files.

## [v2.6.1](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.6.1) - 2026-06-14

A small portrait-mode bugfix release covering the in-game tag HUD. Both fixes are
portrait-only and do not change the rootless or Termux build flow.

**Fixes**

- **Skip tags no longer push the tag row off-screen.** When you already had two or
  more tags and then took a Skip Blind tag, removing a tag re-aligned the
  remaining tags using the landscape anchor, which slid the whole row out of the
  visible area in portrait. The removal path in `tag.lua` now reuses the same
  portrait alignment that new tags are created with (left or right anchor based on
  the play-hand side, attached to the joker row), so the row stays in place.
  Thanks to Cpt-mustard for the detailed report and patch in #28.
- **Tag tooltips stay inside the screen near the edges.** Hovering a tag close to
  the left or right edge in portrait could let its info popup run off-screen,
  because the tooltip relied on a width measurement that is not settled for a
  static HUD element. Tag popups now compute their horizontal position directly
  from the tag's on-screen location and pull the popup back inside the screen,
  with the existing room-fit clamp kept as a fallback. The new
  `get_portrait_top_popup_config` helper in `portrait_config.lua` centralizes this
  so other top-anchored sprites can reuse it.

**Zygisk**

- The release `balatro_portrait.zip` is rebuilt so rooted Zygisk users get both
  fixes. The rootless APK is still not uploaded because it contains the user's own
  game files.

## [v2.6.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.6.0) - 2026-06-13

This release finishes the other half of the Android story. v2.5.0 gave rooted
users a Zygisk route that keeps the official Play Store app installed. v2.6.0
brings the rootless builder closer to the same idea for people with no PC: build
the separate portrait APK directly on the phone, using the already-installed
official Play Store Balatro as the resource source.

The important part is what is no longer required. You do not need to copy
`Balatro.exe` from a computer, hunt for a working Termux apktool fork, or manually
wire up an ARM `aapt2`. Install the official game, install Termux, clone the repo,
run the helper, and the builder can make the portrait APK on-device.

**New: PC-free Termux build from the installed Play Store app**

- **`build.py` can find the official Android app automatically.** On Termux, when
  no `--balatro` path is provided, it calls `/system/bin/pm path
  com.playstack.balatro.android`, finds the installed `base.apk`, and uses that
  as the resource source. This avoids Termux's own `pm` wrapper, which can fail
  on package-manager calls.
- **Official Android APK resources are understood directly.** The extractor now
  accepts both the desktop/LÖVE layout (`resources/`, `localization/`) and the
  Play Store APK layout (`assets/resources/`, `assets/localization/`).
- **`termux-build.sh` is a one-command phone build helper.** It installs missing
  Python/Java packages through Termux, then runs the normal builder with the
  recommended rootless options.
- **Termux signing no longer depends on desktop signing tools.** On Android, the
  build uses native `apksigner` with a local debug keystore. If `zipalign` is not
  available in the Termux repo, the build signs without it instead of failing at
  the last step.
- **The existing ReVanced ARM `aapt2` path is now tested in the real flow.** The
  builder still uses the downloaded iBotPeaches apktool jar unless a native
  apktool is already present, and passes ReVanced's ARM `aapt2` during rebuilds.
- **`docs/TERMUX.md` documents the actual phone flow.** Storage permission is a
  separate Android dialog step; after that, the build command can be pasted as a
  single `pkg update -y && pkg install -y git && ...` chain.

**Android compatibility fixes found while testing the phone-only path**

- **Official Android CRT shaders are patched during build.** The Play Store APK's
  `CRT.fs` comments out `noise_fac`, but portrait `game.lua` still sends that
  uniform. The builder now restores the noise uniform and its use after extracting
  the user's own shader, fixing the `Shader uniform 'noise_fac' does not exist`
  crash.
- **Generated resource folders are refreshed cleanly.** `game_original_files/` is
  cleared before extraction, which avoids stale desktop/Android resource layouts
  getting mixed together between builds.

**Verified on-device**

- Tested on Android with shell superuser disabled.
- Termux built the APK from the installed official Play Store Balatro.
- The resulting `com.unofficial.balatro` APK installed and reached portrait
  in-game play.
- The release still includes `balatro_portrait.zip` for rooted Zygisk users. The
  rootless APK is not uploaded because it contains the user's own game files.

## [v2.5.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.5.0) - 2026-06-12

2.4.0 is skipped on purpose. This release opens a second install path that has
been asked for since the project started: keep the official Google Play
Balatro installed, keep its Play signature intact, and load the portrait port at
runtime.

Until now the rootless APK builder was the only practical route. It still is the
recommended path for most people, and it is better than before, but it has one
hard limit: the built APK contains the user's game files, so releases can never
ship a ready-to-install APK. The new Zygisk path changes that for rooted users.
The release can now include `balatro_portrait.zip` directly, because the module
does not contain the official APK or redistribute Balatro's packaged assets. You
install the Play Store game yourself, install the module from KernelSU, Magisk,
or APatch, reboot, and the official app is patched in memory when it starts.

**New: Zygisk module for the official Play Store app**

- **Runtime portrait injection for `com.playstack.balatro.android`.** The module
  hooks LÖVE's Lua chunk loader inside `liblove.so` and swaps matching chunks
  with the portrait Lua payload as the official game starts. The APK is not
  modified or re-signed.
- **Portrait orientation is forced at runtime.** The module intercepts SDL's
  orientation request and calls Android's portrait orientation directly, instead
  of letting the game briefly request landscape first.
- **Readabletro and CRT choices are made during module install.** The ZIP builds
  all four variants into one package. The installer tries the root manager's
  volume-key helper first and falls back to direct `getevent` key reading, which
  fixes KernelSU-Next installs where `chooseport` is unavailable.
- **The Zygisk release ZIP is now a real release artifact.** Rootless APKs still
  cannot be uploaded because they include the user's game copy. The Zygisk ZIP
  can be uploaded because it only contains the module, portrait payload, hook
  support library, and optional Readabletro resources.

**Rootless builder changes**

- **Android modding is always on.** `build.py` no longer asks whether to include
  Lovely or accepts `--with-lovely` / `--no-lovely`; Android builds always use
  the Lovely base path. If you build the rootless APK, you get mod support.
- **Termux apktool handling is less fragile.** On Termux, the script now expects
  native `apktool` and `aapt2` in `PATH`, passes `--use-aapt2 -a <aapt2>` during
  rebuilds, and prints the failed command/stdout/stderr when apktool fails.

**Zygisk compatibility fixes found on-device**

- **Official mobile LÖVE 12.5.6 runs the portrait Lua payload.** The first proof
  was rough, but useful: the official app reached game startup with injected
  Lua, which meant the plan was viable.
- **Localization stays official.** Early manual packaging accidentally deleted
  Lua localization files, which produced `G.localization` nil crashes. The
  Zygisk generator now skips localization entirely and leaves the Play APK's
  localization files alone.
- **Landscape flash is removed.** The orientation hook no longer forwards the
  original landscape request before forcing portrait.
- **`G.CANV_SCALE` is guarded during early Android resizes.** Official mobile can
  hit `love.resize` before the portrait canvas scale exists.
- **Shaders are injected through a Lua preload.** The official mobile shaders
  differ enough that missing/optimized uniforms can crash `:send`; portrait
  shaders now come from an injected `portrait_shaders` module.
- **Readabletro resources are binary-safe.** PNG and TTF resources are embedded
  as base64 with size and magic-byte checks, then verified again after writing
  to LÖVE's save filesystem. This fixes the `BlindChips.png unsupported file
  format` crash and gives us a safer path for future embedded resource work.

**Docs**

- README now presents two install paths: the rootless APK builder for most users
  and the experimental Zygisk module for rooted users who want to keep the
  official Play install.
- `docs/MODDING.md` separates rootless Lovely modding from the current Zygisk
  path. Full Lovely/Steamodded parity for the official Play package is still
  future work, not something this release pretends to solve.
- `zygisk/README.md` documents local module builds, release ZIP installs, and
  why this route can be published as an artifact while APK builds cannot.

## [v2.3.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.3.0) - 2026-06-11

Swipe Only mode, a full gesture overhaul, experimental iOS support, building directly on your phone via Termux, rootless mod installs — and root fixes for the launch-time layout shift and the last of the phantom-input bugs.

**New: Swipe Only mode (Settings → Game):**

- **Play without buttons.** A new toggle hides the Play Hand/Discard buttons entirely — swipe up plays, swipe down discards — leaving only a compact `Sort | Rank | Suit` strip under the hand and freeing the bottom of the screen for the cards. Gestures are force-enabled in this mode regardless of the `gestures.enabled` config, so the game can never become unplayable.
- **Applies instantly, anywhere** — menu, shop, or mid-run. The layout flag is session-latched (`G.F_SWIPE_ONLY`) and the toggle is pure layout (button row swap + hand offset), so flipping it never desyncs live animations.
- Boss-blind code that pokes the play button UIE is nil-guarded for buttonless layouts (`blind.lua`).

**Swipe gesture overhaul (user feedback):**

- **The selection moves together.** While a selected card is touch-dragged vertically, the rest of the highlighted cards visibly lift with it (`group_follow`), so throwing a 5-card flush reads as throwing five cards, not one. Horizontal drags are ignored — drag-to-reorder is untouched.
- **Slow "carry and release" plays too.** A deliberate vertical drag past the threshold triggers play/discard even when slower than a flick, but only when it started on a selected card — matching what the group-follow animation promises.
- **Flicking an unselected card no longer throws the selection.** A gesture starting on a hand card requires that card to be highlighted.
- On a successful flick every highlighted card gets a `juice_up` pop at the same moment.

**New: iOS build (EXPERIMENTAL, testers wanted):**

- **`python build.py --ios` produces a sideloadable `balatro-portrait.ipa`** — no Xcode or macOS needed. The build downloads the prebuilt unsigned LÖVE iOS app shell from [balatro-apk-maker](https://github.com/blake502/balatro-apk-maker)'s Additional Tools (SHA-256 verified, contains no game data), inserts your locally built `Game.love` into `Payload/Balatro.app/`, locks `Info.plist` to portrait orientation, and stamps the mod version. Sideload with Sideloadly or AltStore — see [docs/IOS.md](docs/IOS.md) for the full guide and the list of things we need testers to verify. **Untested by the maintainer** (no iOS device) — please report results either way.
- **iOS now gets the mobile feature flags.** `globals.lua` only set `F_MOBILE_UI`, `F_VERTICAL_SETTINGS`, `F_HAPTIC` etc. for Android; on iOS the game would have behaved like a desktop build. The engine code was already iOS-safe.
- Lovely mod support remains Android-only (`liblovely.so`); the IPA is always vanilla.

**New: build on your phone (Termux), mod without root:**

- **Termux support in `build.py`.** The desktop JDK and the apktool jar's bundled aapt binaries are x86-64 only and can't run on ARM64 Android. The script now detects Termux and uses the native toolchain instead (`pkg install python openjdk-17 apktool`) — no PC needed to build the APK.
- **Mods install without root.** Material Files → *Add storage…* → *External storage* → pick the Balatro app → *Use this folder* exposes `ASET/Mods/` on stock, unrooted devices (method from Lovely Mobile Maker's FAQ, confirmed against this project's builds). [docs/MODDING.md](docs/MODDING.md) now documents all three methods (SAF, root, ADB) with the no-root path as the recommended default.

**Bug Fixes:**

- **The splash screen and main menu no longer drift left until the first touch.** Root cause found via on-device telemetry: the v2.2.0 phantom-touch fix parked the virtual cursor at (-9999, -9999), and the room-shake parallax — which leans the whole ROOM toward the cursor every frame — translated that into a constant ~1.08-unit left shift (scaling with the screenshake setting). The cursor now parks just offscreen at (-100, -100): hover remains impossible before the first touch, while the parallax error drops to an imperceptible ~0.03 units.
- **The rare "pre-clicked card on launch" is fully closed.** Android occasionally emits synthetic (non-touch) mouse events at boot with a phantom position; one slipping through flipped the controller back into mouse mode. All mouse-flavored events are now ignored on Android/iOS until a real touch has been seen.
- **Boss debuff alerts no longer run off the screen** (e.g. The Arm's "Decrease level of played poker hand"): portrait popups clamp their max width to the room and shrink to fit.
- **The boot loading card re-centers on every resize** — Android fires several resizes while the window settles (fullscreen, nav bar), and the card's once-computed position could go stale.
- **Card-area widths clamp to the room** in `set_screen_positions`, so shelves can never overflow the screen edges regardless of scale settings.

**Notes:**

- `swipe_only.scale_mult` exists in `portrait_config.lua` to scale the whole UI up in Swipe Only mode, but ships disabled (1.0): changing `TILESCALE` mid-session desynced every previously computed position. Enable at your own risk.

## [v2.2.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.2.0) - 2026-06-10

Mobile gameplay UX overhaul: swipe gestures, a floating hand preview, thumb-sized touch targets, high-refresh-rate support, and root fixes for two long-standing phantom-input bugs that made the game feel like a PC port. Every new behavior is tunable (or can be disabled) from `src/portrait_config.lua`.

**New Features (portrait only):**

- **Swipe gestures — flick up to play, flick down to discard.** A quick vertical flick (under 0.45s, mostly vertical, starting in the lower half of the screen) on selected cards triggers the same `play_cards_from_highlighted`/`discard_cards_from_highlighted` flows as the buttons, with the same guards as `can_play`/`can_discard` (1–5 cards highlighted, `blind.block_play`, discards remaining, no overlay/pause, not mid-play). Slow drags still reorder cards as before. Tune or disable via `PORTRAIT_CONFIG.gestures`.
- **Floating hand preview above the hand.** While selecting cards, a chip shows the detected poker hand (name, level, chips × mult) right above the hand — no more eye travel to the HUD at the top of the screen on every tap. The values are live `DynaText`/`ref_table` bindings to `G.GAME.current_round.current_hand`, so they always match the HUD. The chip pops (`juice_up` + text pulse) when it appears or when the detected hand changes, hides outside `SELECTING_HAND`, and is removed in `Game:delete_run`. Configure via `PORTRAIT_CONFIG.hand_preview`.
- **High refresh rate.** `fps_cap = 'auto'` (new default) reads the display's refresh rate from `love.window.getMode` and caps there, so 90/120 Hz phones run at native refresh instead of 60. Set a number to pin it.
- **Visible empty joker/consumable slots.** Empty slots in the joker and consumable shelves draw faint rounded outlines (under the cards), so the top of the screen reads as reserved capacity instead of dead felt. Configure via `PORTRAIT_CONFIG.joker_slots`.
- **Experimental: `deck_position = 'bottom_right'`** moves the deck next to the hand instead of the top shelf. Default remains `'shelf'`.

**UI/UX Improvements (portrait only):**

- **Played cards now land center-stage.** The play area centers in the gap between the joker shelf and the hand (accounting for the hand's 3-unit slide while selecting) instead of hugging the hand and leaving the middle of the screen empty.
- **Bigger scoring feedback.** Floating score/attention popups during play are scaled 1.3× (`score_text_mult`).
- **Thumb-sized touch targets.** The Use/Sell buttons on highlighted cards are scaled 1.4× (`mobile_ui.card_button_mult`) — they were PC-sized and genuinely below Android's recommended minimum touch target. Run Info/Options were resized to 1.95×0.78 units.
- **Quieter chrome.** Run Info/Options are now compact single-row grey buttons, so red stays reserved for Discard and gameplay actions.
- **Readable counters.** The card-count labels (deck 44/52, jokers 1/5, hand 8/8) scale up from 0.3 to 0.42 in portrait.

**Bug Fixes:**

- **Cards/buttons no longer come up "pre-touched" on launch.** The controller's HID flags default to mouse mode, so before the first touch the game polled `love.mouse.getPosition()` every frame — which reports a phantom position on Android — and hover-selected whatever sat under it: a shop joker with its tooltip open on launch, the Reroll button rendering pressed. On Android/iOS the controller now starts in touch mode with the cursor parked offscreen (`engine/controller.lua`), and nothing can hover until a real touch arrives. Desktop behavior is unchanged.
- **Touch tilt warp, root fix.** v2.1.2 clamped the cursor distance fed to the 3D tilt shader; this release goes further: on portrait touch the cursor-lean `hovering` uniform is zeroed entirely (`disable_touch_tilt`, default on), making the sheared-parallelogram warp impossible. Scripted tilt animations (`tilt_var`, e.g. the title screen) are unaffected, and desktop keeps full tilt.

**Build & Tooling:**

- **SHA-256 verification for all version-pinned downloads** (JDK, apktool, uber-apk-signer, APK patch, LÖVE base APK). A mismatch deletes the file and aborts the build. The LMM base APK is rebuilt upstream without versioned URLs, so it can't be pinned — noted inline.
- **CI on GitHub Actions:** LuaJIT syntax check over all of `src/`, `py_compile` on the build script, and a Game.love packaging smoke test (no game files in CI — packaging `src/` alone catches path bugs and patch-target drift).
- **`argparse` CLI** replaces the hand-rolled flag parser; unknown flags now error instead of being silently ignored.
- **Mod version in the APK:** `MOD_VERSION` is injected into `android:versionName`, replacing the hardcoded `1.0.0n-FULL-p1`.
- **Licensing clarified:** MIT license for the build tooling and portrait modifications, with an explicit scope note that all Balatro game code and assets remain LocalThunk/Playstack's (see `LICENSE`).
- **Docs:** `docs/MODDING.md` updated to the unified `build.py` (was still referencing `build_apk.py`); `requirements.txt` removed (stdlib only); this CHANGELOG introduced.

## [v2.1.2](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.1.2) - 2026-05-29

Hotfix for a portrait/touch-only visual glitch where cards would randomly shear into a warped parallelogram.

**Bug Fix:**

- **Attempt to fix cards randomly warping into a sheared parallelogram on touch.** The 3D tilt shader (`src/engine/sprite.lua:93-98`) leans a card toward `mouse_screen_pos`, with the shear proportional to the distance between the card centre and that point. `Card:draw` (`src/card.lua:4408-4413`) feeds it `G.CONTROLLER.cursor_position` directly. On desktop the cursor sits on the hovered card so the lean is subtle; on touch `cursor_position` stays pinned to the last touch point (`src/engine/controller.lua:178`), and a card can enter hover/focus while that point is far away — during dealing, or when a canvas refresh/`love.resize` changes `G.TILESCALE` while the cursor is still in old coordinates — so the distance blows up and the card shears off, which is why it looked random. The virtual cursor that drives the tilt is now clamped to within one card extent of the card's own centre, using the same screen-space formula as the ambient tilt path. Desktop hovering already sits inside that range, so the clamp never triggers and vanilla behavior is unchanged.

No vanilla-only changes in this release.

## [v2.1.1](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.1.1) - 2026-05-17

Hotfix for a SteamModded-only crash that hit whenever a debuffed card scored.

**Bug Fix:**

- **Game no longer crashes when a debuffed card scores under SteamModded.** `SMODS.juice_up_blind` (in `src/utils.lua:256`) looks up the HUD's debuff container via `G.HUD_blind:get_UIE_by_ID('HUD_blind_debuff')`. Our portrait HUD had ids on the inner text nodes (`HUD_blind_debuff_1`, `HUD_blind_debuff_2`) but no id on the wrapper row, so the lookup returned `nil` and SMODS crashed indexing `ui_elem.children`. The matching SMODS lovely regex patch only fires on the vanilla landscape structure (specific scales/paddings/dimensions); our portrait HUD uses different values, so the id never got injected. The wrapper now carries `id = 'HUD_blind_debuff'` directly. Vanilla behavior is unchanged — nothing in the base game queries this id.

No vanilla-only changes in this release.

## [v2.1.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.1.0) - 2026-05-14

This release makes the portrait mobile port work end-to-end with [Steamodded](https://github.com/Steamodded/smods) (`smods-1.0.0-beta-0711a`) without crashes or visual regressions, and fixes a portrait-only layout bug where the boss panel ballooned vertically when rerolled. All SteamModded fixes are no-ops when SteamModded isn't loaded — vanilla portrait behavior is unchanged.

**Bug Fixes (portrait, vanilla):**

- **Boss reroll no longer balloons in portrait mode.** Reroll Boss tag (and the `v_directors_cut`/`v_retcon` $10 reroll button) rebuilt the boss UIBox through `UIBox_dyn_container`, which hardcodes `minh = 30` and landscape paddings. The rerolled boss panel now uses the same triple-row wrapper as `compact_blind_choice`, with portrait-aware paddings and no `minh` constraint, so the panel stays in place at its original size.

**SteamModded Compatibility:**

- **Build pipeline normalizes packaged Lua files to LF.** Lovely-injector's regex patches anchor on `\n`; Windows checkouts ship CRLF, which made several SMODS regex patches silently fail and leave behind dangling code that crashed with `ambiguous syntax (function call x new statement)` at runtime.
- **Game no longer crashes at run start with SMODS loaded.** SMODS's overridden `G.FUNCS.HUD_blind_debuff` asserts `G.HUD_blind == e.UIBox`, which failed when `engine/ui.lua`'s init-time func dispatch ran on the HUD's text nodes before the assignment landed. The HUD debuff text nodes now get their `func` attached after `self.HUD_blind = UIBox{...}` returns.
- **HUD debuff lines no longer crash mid-run.** SMODS's override of `HUD_blind_debuff` expects a container with child rows and calls `set_parent_child` on the node; on text nodes this added children whose `T` field never got initialized (`calculate_xywh` doesn't recurse into text-node children), which crashed `set_wh` with `attempt to index field 'T' (a nil value)`. The portrait HUD text nodes now reference a dedicated `portrait_HUD_blind_debuff` alias that SMODS doesn't override.
- **Blind info no longer disappears from the top-left HUD when SMODS is loaded.** SMODS injects a `row_blind_bottom` spacer into the landscape `row_blind` pattern and reanchors HUD_blind to it; our portrait `row_blind` is a different node shape, so the injection silently skipped it and left HUD_blind anchored to nothing. The portrait `row_blind` now ships the spacer itself.

**Other:**

- Removed `changelog.txt`. Release notes live on the Releases page going forward.

## [v2.0.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v2.0.0) - 2026-05-02

This is the biggest portrait/mobile pass since 1.9.6. It focuses on readability, touch behavior, tooltip placement, and a more mobile-native layout across the run, shop, blind-select, and setup screens.

**Highlights:**

- Reworked the portrait HUD so round score, current hand, money, hands, discards, ante, round, and boss blind information use the top area more intelligently.
- Made boss blind panels more compact in-game so long boss text such as The Hook no longer overlaps the Hands/Discards row.
- Rebalanced blind-select cards for mobile readability, including larger critical values, tighter padding, and better use of the available vertical space.
- Reworked the shop layout for portrait so jokers, vouchers, packs, reroll, and next-round controls fit more naturally without accidentally enlarging the shop sign.
- Improved main menu positioning so the Play/Options/Quit/Collection stack and profile/language buttons sit higher and avoid bottom-edge clipping.
- Improved New Run deck selection readability; Magic Deck, Green Deck, and other deck descriptions now scale into their description panel.

**Tooltip and Touch Fixes:**

- Tooltips now dynamically stay inside the visible screen instead of clipping off the left or right edge.
- Long-press tooltips are moved higher so they are not hidden directly under the player's finger.
- Tooltip fitting now applies broadly to cards, jokers, tarot/planet/spectral cards, tags, and side info popups.
- Disabled dragging/collision on portrait tooltips to prevent long-press and swipe from moving tooltip text around.
- Fixed skipped/finished blind tag popups drifting upward or flying away after repeated presses.
- Fixed boss reroll/blind-select alignment so rerolled bosses start from the existing slot instead of snapping from a zero-size position.

**Bug Fixes:**

- Fixed the CRT edge/eclipse effect staying visible at low CRT slider values. The CRT edge mask now follows the CRT slider intensity instead of always applying at full strength. This addresses #22.
- Fixed rare Android touch launches where input could stop responding until the app was restarted by tracking touch coordinates from touch events instead of relying on stale mouse coordinates.
- Fixed hand-card spacing so larger mobile cards clamp to the usable screen width instead of spilling off-screen.
- Fixed profile/language UI cleanup when returning to the main menu or deleting a run.
- Fixed run setup deck description refresh so cycled decks keep the mobile-scaled layout.

**Build System:**

- Default build profile is now: CRT-disabling patch off, Readabletro on, Lovely mod support off.
- Build prompts now work better in non-interactive environments by falling back to saved/default answers on EOF.
- Added a build-time CRT shader mask patch so generated Balatro resources get the slider-aware CRT edge fix automatically.
- Included PR #21: macOS users can pass the Balatro `.app` bundle path and the build script will auto-detect `Contents/Resources/Balatro.love`.
- Updated README build defaults and macOS path examples.

**Technical Notes:**

- Added shared portrait tooltip fit helpers in `portrait_config.lua`.
- Added `UIBox:fit_to_room()` and popup snap-to-fit support for portrait UI.
- Centralized many mobile HUD, blind-select, shop, run-setup, and main-menu dimensions in `PORTRAIT_CONFIG.mobile_ui`.
- Added event-driven Android touch position tracking in `main.lua` and `controller.lua`.

Full Changelog: https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.9.6...v2.0.0

## [v1.9.6](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.9.6) - 2026-05-01

**Bug Fixes:**

- Fixed bottom-edge rendering artifact in portrait mode on tall phones (canvas wrap mode + screen clear before canvas draw).
- Fixed Windows console encoding error in build time report.

**Improvements:**

- Merged all build scripts (`setup.py`, `rebuild_game.py`, `build_apk.py`) into a single `build.py`.
- Removed `game_original_files/` from the repository (auto-generated from your Balatro copy, not meant to be committed).
- Cleaned up `.gitignore`.
- Updated README with clearer build instructions and troubleshooting.

**CRT Shader:** Remains enabled by default. Users experiencing a black ellipse or colored sliver can rebuild with the CRT patch: `python build.py --crt`

## [v1.9.5](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.9.5) - 2026-04-26

Bug Fixes:
- Fixed portrait tutorial progression after shop and Big Blind.
- Fixed tutorial bubble positioning in portrait.
- Fixed portrait main menu and round-end layout alignment.

## [v1.9.4](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.9.4) - 2026-04-22

Bug Fixes:

- Fixed tutorial Next button and hand-info progression issues in portrait mode.
- Fixed tutorial hand-info follow-up dialogue positioning so Jimbo stays visible.
- Fixed a tutorial overlay nil crash during tutorial event cleanup.

## [v1.9.3h](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.9.3h) - 2026-04-22

Fixed tutorial dialogue in portrait mode so the Next button is anchored below Jimbo's speech bubble instead of covering the text.

## [v1.9.3](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.9.3) - 2026-04-21

Bug Fixes:

- Fixed Android profile rename keyboard not appearing in portrait mode.
- Fixed text input crash when typing from the Android virtual keyboard.
- Fixed duplicate character input while renaming profiles on Android.
- Removed Android-wide touch haptic spam so haptics stay tied to card interactions.

Full Changelog: https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.9.2...v1.9.3

## [v1.9.2](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.9.2) - 2026-04-20

Bug Fixes:

- Fixed the Haptic Feedback toggle so disabling it now shuts off Android vibration paths instead of leaving some haptics active.
- Restored Android haptics for card movement sounds, including the card draw/deck animation path (cardSlide1, cardSlide2, card1, cardFan2).
- Restored stronger action haptics on Android while keeping the settings toggle behavior correct.
- Added light haptics for toggle presses and option-cycle changes to improve UI feedback.

Technical Notes:

- Unified haptic gating in src/globals.lua.
- Gated Android sound-driven vibration in src/functions/misc_functions.lua.
- Gated controller rumble on Android in src/functions/common_events.lua.
- Wired the settings toggle callback in src/functions/UI_definitions.lua.
- Added UI interaction haptics in src/functions/button_callbacks.lua.

Full Changelog: https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.9.1...v1.9.2

## [v1.9.1](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.9.1) - 2026-04-08

Bug Fixes:
- Fixed black bar appearing at bottom of screen after locking/unlocking phone during gameplay. Canvas now fully refreshes on resume via love.visible + love.draw size mismatch detection.
- Fixed crash log not copying to clipboard. Crash screen now stays open until BACK/ESC is pressed. Font fallback chain added.
- Fixed tooltips overflowing screen edges in portrait mode. Tooltips now dynamically flip anchor direction based on card position.
- Fixed tutorial speech bubble rendering too high in portrait mode. Bubble now positions below Jimbo.
- Fixed syntax error in common_events.lua preventing game launch.

Removed:
- Removed pinch-to-zoom feature (caused layout glitches and served no practical purpose).

Full Changelog: https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.9.0...v1.9.1

## [v1.9.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.9.0) - 2026-04-08

Centralized Configuration:
- Created portrait_config.lua: all scattered magic numbers (scale factors, margins, offsets, thresholds) now live in a single config table.
- Dynamic aspect ratio scaling via get_portrait_scale(): adapts to phone (0.63), tall phone (0.58), tablet (0.70-0.80) automatically.

Crash Reporting:
- Crash log is now automatically copied to clipboard on crash (love.system.setClipboardText).
- Crash log is saved to crash_log.txt file on disk.
- Crash screen stays open until user presses BACK or ESC. No more auto-closing.
- Font fallback chain: TypoQuik-Bold -> m6x11plus -> system default.

Input Improvements:
- Pinch-to-zoom: two-finger gesture scales the game view in real time (range 2.0-8.0).
- Android back button: opens options menu during gameplay, closes overlay menus.
- Touch cursor sync: force controller cursor to exact tap position for accurate hit-testing.

Display and Layout:
- Immersive mode: hides system bars for full-screen gaming on Android.
- Keep screen alive: prevents display sleep during gameplay.
- Adaptive HUD: vertical HUD scale adjusts 0.35-0.45 based on screen aspect ratio.
- Smart tooltip anchoring: tooltips dynamically flip direction (above/below) based on card position and shift horizontally to stay within screen bounds.
- Tutorial speech bubble repositioned for portrait mode: shows below Jimbo instead of above, moved lower on screen.

Bug Fixes:
- Discard off-screen bug: changed from hardcoded +15 offset to relative positioning from play area.
- Landscape resize black screen: canvas now updates even when landscape resize events are ignored on mobile.
- Readabletro patch FileNotFoundError: destination directories are now created with os.makedirs before copying.
- Build script .bak restore issue: backup files are always recreated from current source, preventing stale backups from reverting changes.

Build System:
- Incremental builds: file hash caching in .build_cache.json, skips rebuild if no source changes detected.
- Sequential downloads: replaced parallel downloads with reliable sequential transfers using urllib with 120s timeout.
- Build profiler with per-step timing report.
- Download progress bars use ASCII-safe characters for Windows console compatibility.
- build.py now checks for src/resources existence (not just src/) before prompting for setup.

Settings:
- Portrait-specific haptic toggle added to Game settings tab.
- FPS cap configurable via portrait_config.fps_cap (default 60 on mobile).

Full Changelog: https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.8.5...v1.9.0

## [v1.8.5](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.8.5) - 2026-04-06

Major Additions:
- Haptic Feedback Engine: Added comprehensive haptic feedback (vibrations) on Android devices for tapping buttons, purchasing items, playing cards, opening packs, and rerolling the shop.
- Engine Optimization: Hardcoded an FPS cap tailored for mobile (60 FPS limit on iOS/Android). This resolves previous battery drain and thermal overheating issues caused by the default 500 FPS behavior.
- Suspended State Auto-Save: Implemented an active state listener. The game now automatically triggers a background save whenever the application loses focus, preventing data loss.
- Layout Safe Area: Shifted the portrait HUD down symmetrically to clear front-camera notches and cutouts present on modern hardware.
- Anti-Jitter Touch Deadzones: Added a movement threshold to prevent the game from accidentally confusing brief card taps with drag movements on highly sensitive touch screens.

Bug Fixes & Refinements:
- Readabletro Textures Fix: Corrected the texture replacement logic within the build script. The high-resolution 2x Readabletro textures will now correctly apply and replace the vanilla assets upon building.
- Build Automation: The build.py script now supports saved configurations (.buildconfig.json). Users will no longer be asked redundant setup questions on subsequent builds, and the CRT disable patch now defaults to false.

Note: For the haptic features and optimized builds to apply, please rebuild your APK using the updated scripts.

## [v1.8.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.8.0) - 2026-04-06

- Added native support for Readabletro typography and shaders.
- Users are now prompted to apply the Readabletro mod during rebuild_game.py allowing for significantly better text scaling and readability on mobile devices.
- Modified the Readabletro PC shaders to be completely compatible with Android OpenGL ES, fixing the background crashes occurring on some devices. 

Bug Fixes:
- Improved internal build scripts to handle temporary patches via `.bak` restoration seamlessly, keeping the repo clean.

## [v1.7.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.7.0) - 2026-04-06

### Lovely Mod Support
Balatro Portrait Mobile now supports the [Lovely](https://github.com/ethangreen-dev/lovely-injector) runtime Lua injector for loading mods on Android.

> ⚠️ **Root Required**: Installing mods requires a **rooted Android device** (e.g. via [Magisk](https://github.com/topjohnwu/Magisk)). The mod directory is located in the root filesystem (`/data/user/0/`), which is not accessible without root privileges.

### How to Build with Mods

```
python rebuild_game.py
python build_apk.py --with-lovely
```

Or answer **yes** when prompted during `build_apk.py`.

### Installing Mods

1. Build and install the Lovely-enabled APK
2. Launch the game once
3. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files)
4. Navigate to: `/data/user/0/com.unofficial.balatro/files/save/ASET/Mods/`
5. Place your mod folders there
6. Restart the game

> ⚠️ The mod directory is in the **root filesystem** (`/`), not in `Android/data/`. Use Material Files to navigate from `/`.

See [docs/MODDING.md](docs/MODDING.md) for detailed instructions.

### Technical Changes
- Lovely injector embedded via [LMM](https://github.com/WilsontheWolf/lovely-mobile-maker) base APK
- LMM manifest preserved in-place (prevents AndroidX/provider crashes)
- Smali patches skipped in Lovely mode (preserves native Lovely initialization)
- Package name: `com.unofficial.balatro`
- CLI flags: `--with-lovely` / `--no-lovely` for CI/automation
- APK built as debuggable for ADB mod access

### Full Changelog
https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.6.0...v1.7.0

## [v1.6.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.6.0) - 2026-03-07

- Added dynamic Left/Right Hand layouts
- Customizable Run Info / Options button positioning
- Visual and UI alignment fixes
- Source code release

## [v1.5.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.5.0) - 2026-03-07

- Full portrait mode layout on all screens
- MacOS compatibility and removed 7-zip requirement
- Fixed blind selection visual states in portrait mode
- Source code release

## [v1.4.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.4.0) - 2026-02-04

### Game Over Screen
- **Portrait layout redesigned**
  - Jimbo repositioned at bottom (stats at top)
  - Vertical single-column layout instead of horizontal two-column
  - Speech bubble now fits properly on screen
  - Smaller Jimbo sprite to save space

### Lock Screen Resize Issue
- **Fixed black bar appearing after unlocking phone** (Issue #1)
  - Added viewport/scissor reset in resize handler
  - Overlay menu recreation on resize events
  - Proper canvas scaling on orientation changes

## Changelog
- **Fixed:** Game Over screen layout for portrait mode
- **Fixed:** Black bar issue when locking/unlocking device
- **Improved:** Resize handling for better Android compatibility

---

**Full Changelog:** https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.3.0...v1.4.0

## [v1.3.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.3.0) - 2026-02-04

### CRT Shader Fix
- Added interactive CRT patch option during build
- When running `rebuild_game.py`, you will be asked if you want to apply the CRT patch
- This fixes the **black ellipse visual artifact** some users experience (Issue #3)

### How to Use
1. Run `python rebuild_game.py`
2. When asked about CRT patch:
   - Answer **yes** if you see a black ellipse on screen
   - Answer **no** if your game works fine
3. Run `python build_apk.py`

### Changelog
- Added CRT shader disable option during build
- Fixed black ellipse visual artifact on some devices
- Updated README with troubleshooting guide

## [v1.0.4-experimental](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.0.4-experimental) - 2026-02-04

This is a test build to fix issue #3 (black ellipse visual artifact).

### Changes
- Disabled CRT shader in portrait mode to fix black ellipse visual artifact

### Testing Needed
Please test and report if the visual artifact issue is resolved.

**Note:** This is an experimental build.

## [v1.2.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.2.0) - 2026-01-30

### Cross-Platform Support
-  **Windows Support**: Build scripts now work on Windows
-  **Linux Support**: Continues to work on Linux
-  **Auto-Detection**: Scripts automatically detect your OS

### New Features
-  Added `setup.py` for automated game file extraction
-  Added `requirements.txt` (stdlib only, no dependencies!)
-  Simplified README with unified instructions

### Build Script Fixes
-  Fixed JDK download (Windows .zip, Linux .tar.gz)
-  Fixed Java path detection (java.exe on Windows)
-  Fixed file extraction (zipfile on Windows, tarfile on Linux)

---

>  **Important**
> You need to own a legal copy of **Balatro** to use this mod.

See the [README](https://github.com/ShaggyLorean/balatro-portrait-mobile#readme) for build instructions.

**Full Changelog**: https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.1.0...v1.2.0

## [v1.1.0](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/v1.1.0) - 2026-01-11

### UI Changes
- ✅ Fixed black bar at top of screen
- ✅ Reduced blind panel icon size for portrait mode (~23% smaller)
- ✅ Repositioned deck, consumables, and jokers for better layout
- ✅ Improved HUD positioning

### Build Improvements
- 📦 Added `rebuild_game.py` for easy Game.love creation
- 📝 Created `game_original_files/` placeholder with clear instructions
- 📖 Updated README with step-by-step build guide
- 🔧 Better error handling in build scripts

### Bug Fixes
- 🐛 Fixed consumables and jokers overlapping
- 🐛 Fixed touch input handling for Android
- 🐛 Fixed portrait mode resize handling

---

## ⚠️ Important

You need to own a legal copy of **Balatro** to use this mod.

See the [README](https://github.com/ShaggyLorean/balatro-portrait-mobile#readme) for build instructions.

---

**Full Changelog**: https://github.com/ShaggyLorean/balatro-portrait-mobile/compare/v1.0.3...v1.1.0

## [1.0a](https://github.com/ShaggyLorean/balatro-portrait-mobile/releases/tag/1.0a) - 2026-01-02

First stable release with Left Stack Layout (Source Only).
