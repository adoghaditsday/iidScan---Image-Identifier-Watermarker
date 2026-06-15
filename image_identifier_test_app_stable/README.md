# Image Identifier Test App v0.4

Local-only desktop test build for marking and scanning images with hidden identifier payloads.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## New in v0.4

- CustomTkinter interface.
- Simplified and Advanced view modes.
- Simplified mode shows only selected images, mark/scan status, and save location.
- Advanced mode keeps the action log and storage folders visible.
- Changeable save folder before, during, or after image selection.
- User dropdown menu with Sign Out and Close Program.
- Smokey-black interface with red, blue, and green button accents.

## Local storage

The app does not use online access. Accounts, logs, reports, snapshots, and marked images are stored locally.

Default folders:

- `storage/marked`
- `storage/snapshots`
- `storage/reports`
- `storage/user_logs`

You can change the image save folder inside the app. Account data and encoded user logs remain in the app's local `storage` folder.


## v0.4 updates
- Simplified scan now shows in-window confirmations.
- Marked scans offer Check Report, Ignore, or Remove from Selected.
- Unmarked scans require an in-app Ok confirmation.
- Thumbnail cards can be selected with mouse click and tab/focusable card buttons.
