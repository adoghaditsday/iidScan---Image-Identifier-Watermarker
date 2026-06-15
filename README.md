# Image Identifier Studio

<img width="1024" height="1024" alt="iidScan_logo1" src="https://github.com/user-attachments/assets/93e30251-ffe9-4b47-a161-f67e0bd1d53b" />

Local-only image identifier/watermark test project.

This repository package contains two separately maintained builds:

- `stable-main/image_identifier_test_app` — v0.5 stable/main build.
- `nightly-experimental/image_identifier_test_app` — v0.6 nightly/experimental build with external workflow/watch-folder features.

## Stable v0.5: build Windows EXE

From the repository root on Windows:

```bat
scripts\build_stable_v05_exe.bat
```

Output will be placed in:

```text
stable-main\image_identifier_test_app\dist\ImageIdentifierStudio_v0_5\
```

Run:

```text
ImageIdentifierStudio_v0_5.exe
```

## Nightly v0.6: run/dev launcher

From the repository root on Windows:

```bat
scripts\run_nightly_v06.bat
```

This creates/uses a local virtual environment, installs requirements, and launches the v0.6 app.

## Manual run

```bash
cd stable-main/image_identifier_test_app
pip install -r requirements.txt
python main.py
```

or:

```bash
cd nightly-experimental/image_identifier_test_app
pip install -r requirements.txt
python main.py
```

## Local storage note

The app stores local account/database/report/log data inside its app data folders. Do not commit generated runtime folders, databases, logs, reports, snapshots, or marked image outputs.
