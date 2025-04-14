# Firmware Repository

This directory contains all automatically built firmware binaries that have passed verification.

## File Naming Convention

Firmware files follow this naming format:
```
rev<version_number>-<git_commit_hash>.bin
```
Example:
```
rev1.0-efa805273c2e3dcc75291db4b8e685ad57a9b78d.bin
```

- `rev1.0`: Firmware version number
- `efa805...`: Full git commit hash used to build this firmware

## Important Notes

1. **Automatic Builds**: All firmware binaries are built automatically from the source code.
2. **Verified**: Each firmware has passed our verification process before being included here.
3. **Version Reference**: When requesting after-sales support, please provide only the version number (e.g., "rev1.0").
4. **No Support**: This repository itself does not provide any after-sales support or technical assistance.

## Usage

1. Download the appropriate firmware file
2. Flash the firmware using your device's standard update procedure
3. Refer to your device documentation for specific update instructions