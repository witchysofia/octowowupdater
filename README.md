# OctoWoW Client Updater

A lightweight, automated Python script to download, verify, update, and patch the **OctoWoW** client. It ensures your game files are up to date by performing hash verification, applying client tweaks, and configuring optimal settings based on your display.

> [!NOTE]  
> **Credit:** This script was created by [rebazed](http://discord.com/users/287467238573867018).

---

## Features

- **Smart Updates:** Scans your existing files and uses SHA-1 hashes to only download files that are missing, corrupted, or out of date.
- **Client Performance Tweaks:** Automatically patches `WoW.exe` with modern client enhancements:
  - **Large Address Aware (LAA):** Allows the 32-bit client to utilize up to 4GB of RAM (preventing Out-of-Memory crashes).
  - **Field of View (FoV) Adjustment:** Sets default FoV optimized for 16:9 widescreen resolutions.
  - **Camera Fixes:** Increases default camera max distance and fixes camera skipping issues.
  - **Quality of Life patches:** Enables always-auto-loot, background sound, and cross-faction resurrect features.
- **Auto-Config Generation:** Reads your primary monitor's resolution and refresh rate, then automatically writes an optimized `WTF/Config.wtf` file for a borderless windowed, high-performance experience.

---

## Step-by-Step Installation Guide

Follow these steps to set up Python and run the updater on your system.

### Step 1: Install Python
If you do not have Python installed on your computer, follow these instructions:

1. **Download Python:**
   - Go to the official Python website: [python.org/downloads](https://www.python.org/downloads/)
   - Click the yellow **Download Python 3.xx.x** button to download the installer for Windows.

2. **Run the Installer:**
   - Open the downloaded `.exe` file.
   - **CRITICAL:** At the bottom of the installation window, check the box that says **"Add python.exe to PATH"**. If you miss this step, your computer won't recognize Python commands!
   - Click **Install Now** and wait for the installation to finish.
   - Click **Close** when done.

3. **Verify Installation:**
   - Open your command prompt (press `Win + R`, type `cmd`, and press Enter).
   - Type the following command and press Enter:
     ```cmd
     python --version
     ```
   - You should see `Python 3.xx.x` displayed. If so, Python is successfully installed!

---

## How to Use the Updater

Depending on whether you want a clean installation or to update your existing game files, follow the instructions below:

### Option A: Clean Installation (Downloading the game from scratch)

1. Put the `octo_wow_updater.py` script into the folder where you want your game directory to be created (e.g., `D:\Games\`).
2. Run the updater by doing either of the following:
   - **Double-click** the `octo_wow_updater.py` file.
   - **Or** open a Command Prompt/PowerShell window in that directory and run:
     ```cmd
     python octo_wow_updater.py
     ```
3. A command window will appear and start downloading the manifest and client files. A folder named `OctoWoW` will be created automatically inside the directory containing the script.
4. Once completed, you will see a message: `"Everything is ready! You can close this window."` Open the new `OctoWoW` folder and run `WoW.exe` to play.

---

### Option B: Updating Existing Game/Client Files

If you already have client files downloaded and want to verify, update, or patch them without downloading the entire game again, follow these steps:

1. Locate the folder where your existing client files are saved.
2. Rename that existing game directory exactly to **`OctoWoW`** (case-sensitive).
3. Place the `octo_wow_updater.py` script in the folder **sitting directly alongside** (in the same parent directory as) your renamed `OctoWoW` folder.
   
   **Your folder structure should look like this:**
   ```text
   📂 Games (or any parent folder)
    ┣ 📜 octo_wow_updater.py
    ┗ 📂 OctoWoW (Your renamed client folder containing WoW.exe, Data, etc.)
   ```
4. Run the script by double-clicking `octo_wow_updater.py` or by opening a terminal and running:
   ```cmd
   python octo_wow_updater.py
   ```
5. The updater will automatically:
   - Identify the existing `OctoWoW` directory.
   - Fetch the latest file manifest.
   - Scan all your existing files, comparing their hashes.
   - Skip files that are already matching, only downloading missing or outdated ones (saving you time and bandwidth!).
   - Apply the executable patches and create an optimized config.
6. Once it completes, you can safely launch the game.

---

## Troubleshooting & FAQ

#### The download gets interrupted or fails
The updater retries downloading files up to 3 times before giving up. If your connection drops and the script closes:
- Simply **run the script again**. The updater will scan what is already downloaded, verify the hashes, and resume downloading right where it left off.

#### "python" is not recognized as an internal or external command
This means Python was installed, but the **"Add python.exe to PATH"** checkbox was not selected during setup.
- Re-run the Python installer, select **Modify**, and make sure the "Add to PATH" option is checked. Alternatively, uninstall Python and reinstall it, ensuring you check that box.

---

## Credits & Support

- **Script Author:** Created by [rebazed](http://discord.com/users/287467238573867018). Please retain credit to the original author in any distributed or modified versions.
- **Support:** For any questions or support regarding this script, contact the author directly via Discord.
