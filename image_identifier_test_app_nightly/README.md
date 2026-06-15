# Image Identifier Test App v0.6

Local-only desktop test build for marking and scanning images with hidden identifier payloads.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Core features

- Local sign-up/sign-in.
- Hidden identifier marking for selected image files.
- Scan reports for marked or unmarked images.
- Snapshot creation for mark and scan actions.
- Simplified and Advanced view modes.
- In-app confirmations instead of detached Windows dialog prompts.
- Changeable save folder before, during, or after image selection.
- Encoded local user action logs.

## New in v0.6

- External Workflow tab in Advanced mode.
- Watch Folder support for exports from other editing applications.
- New file actions:
  - Ask Each Time
  - Scan Only
  - Mark Automatically
- Companion script generator for Photoshop-style handoff.
- Lightroom Classic / Luminar Neo export-folder workflow guide.
- Settings saved locally in `storage/settings.json`.

## External workflow concept

Start the app, sign in, switch to **Advanced**, open **External Workflow**, choose a watch folder, then click **Start Watching**.

When another app exports an image into that folder, Image Identifier imports it into the current selection and either asks what to do, scans it, or marks it automatically depending on the selected action mode.

Recommended testing mode:

```text
Ask Each Time
```

Recommended production-like mode for review:

```text
Scan Only
```

Use **Mark Automatically** only after you trust the workflow.

## Photoshop handoff

Inside the app, click **Install / Refresh Companion Scripts**. Then open the generated `companion_scripts` folder and use:

```text
Send_To_Image_Identifier_Photoshop.jsx
```

In Photoshop:

```text
File > Scripts > Browse...
```

Select the JSX script. It exports the active document into the Image Identifier watch folder.

## Lightroom Classic / Luminar Neo

For these, the cleanest test workflow is export-to-folder:

1. Create an export preset.
2. Set the export destination to the watch folder shown in Image Identifier.
3. Start Watch Folder in Image Identifier.
4. Export selected images from Lightroom/Luminar.

## Local storage

The app does not use online access. Accounts, logs, settings, reports, snapshots, and marked images are stored locally.

Default folders:

- `storage/marked`
- `storage/snapshots`
- `storage/reports`
- `storage/user_logs`
- `storage/external_inbox`

You can change the image save folder inside the app. Account data and encoded user logs remain in the app's local `storage` folder.
