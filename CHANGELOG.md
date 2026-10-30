# Changelog

All notable changes to NX Control. Each release on the
[Releases](https://github.com/danialonso/nx-control/releases) page shows the notes of its version.

## [0.2.5] - unreleased

### Added
- **Phone notifications for time requests**, built in: choose one or more phones in
  **NX Control → Configure** (for example yours and your partner's). Each one gets
  "🎮 Dani asks for 15 min more" with **Approve** and **Deny** buttons. When someone answers, from a
  phone, the card or the console, the request disappears from every phone and the others are told
  who answered ("✅ Inma approved 15 min for Dani"). In your Home Assistant language.
  Tapping the notification opens the NX Control page (or the page chosen in the options).
- **Guided setup in Home Assistant**: after pairing, Home Assistant asks which phones get the time
  requests (and sends a test notification to check it arrives), explains the NX Control page in the
  sidebar, and ends with a summary that also explains how to add the card to any dashboard.
  **NX Control → Configure** can send a test notification too.
- **Diagnostics → Restart the NX Control service**: applies a new version copied to the SD card
  without restarting the console.
- Tested on console firmware **23.x**.
- **NX Control page in the Home Assistant sidebar**, added by the integration itself: the card, full
  screen, for every user. It can be turned off in **NX Control → Configure**.
- **NX Control icon for Home Assistant**: `nxc:family` can be chosen anywhere an icon is set, for
  example as the sidebar icon of a dashboard.
- This changelog. Release notes now list what changed in each version.
- The Home Assistant card tells you when a newer version is installed than the one the page is
  running ("NX Control x.y.z is installed: reload to use it"), with a **Reload** button. The Home
  Assistant app keeps pages open for days, so this used to go unnoticed.

### Changed
- **A new day starts in Home Assistant even with the console off.** At midnight, played time goes back
  to zero and the time left follows the weekly schedule (for example 1 h on weekdays, no play at
  weekends), with the allowed hours. "Blocked for today" and "No time limits until 0:00" end; the
  console lock stays. The console now sends its weekly schedule for this, and its own data takes
  over again when it is turned on.
- The card is also served from `/local/nx_control/` (a copy in `config/www/nx_control/`) and added to
  the dashboard resources by NX Control itself. Do not add or edit that resource by hand.
- The card writes its version in the browser console, which helps when reporting problems.

### Fixed
- Answering a time request that was already answered (from the console, another phone, or a second
  tap) no longer shows a technical "409 conflict" error: the request disappears from the card at once
  and, if needed, a clear message says it was already answered.
- The card could show **"Custom element doesn't exist: nx-control-card"** when the app opened a
  dashboard while Home Assistant was still starting. It now loads from the very start.
- The card could keep showing an **old version** (old logo) after updating, because of an old copy in
  the dashboard resources or a page left open in the app.

## [0.2.4] - 2026-10-26

Version 0.2.3 was never released; its changes are included here.

### Added
- **Six languages**: English, Spanish, French, German, Italian and Portuguese, in the app, the time
  bar, the quick panel, the Home Assistant integration and the dashboard card. The console follows
  the system language and Home Assistant follows your profile language.
- **Settings → Time bar**, to turn the on-screen time bar and its warning sound on or off.

### Changed
- The **time bar and its warning sound are on by default** and no longer experimental.
- The PIN is required to open NX Control; closing the PIN screen exits the app.

### Fixed
- Pressing **B** on the PIN screen at start-up opened the app without entering the PIN.
- The local network could stop answering ("connection refused") while sending game icons and
  avatars. It now checks itself and restarts on its own if it gets stuck.
- Home Assistant no longer keeps asking for an image that failed to load; it tries again an hour later.

## [0.2.2]

### Changed
- First release from the new public repository. NX Control is free for personal use (see
  [LICENSE](LICENSE)); the quick panel source code stays open (GPL).
- Releases are published here, and Home Assistant installs the integration from them through HACS.
