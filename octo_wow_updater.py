"""
OctoWoW Updater

Copyright (c) 2026 rebazed

This project is open for personal use, modification, and redistribution.

You must retain credit to the original author in any distributed or modified versions.

The software is provided "as is", without warranty of any kind.
"""

import json
import hashlib
import os
import urllib.request
import shutil
import struct
import time
import math
from pathlib import Path

UPDATER_VERSION = "1.1"
SERVER = "https://octowow.st"
DOWNLOAD_VERSION = "latest"
OUT_DIR = "OctoWoW"
UA = f"OctoWoWUpdater/{UPDATER_VERSION}"
DOWNLOAD_RETRY_COUNT = 3


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def safe_remove(path):
    if os.path.exists(path):
        print(f"  Removing: {path}")
        os.remove(path)


def download(url, dest, size):
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    tmp = dest + ".tmp"

    for attempt in range(1, DOWNLOAD_RETRY_COUNT + 1):
        try:
            print(f"  Downloading ({size // 1024 // 1024} MB)...")
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req) as r:
                with open(tmp, "wb") as f:
                    downloaded = 0
                    while True:
                        chunk_size = 1024 * 1024  # 1 MB
                        chunk = r.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        print(
                            f"\r  {downloaded // 1024 // 1024} / {size // 1024 // 1024} MB",
                            end="",
                            flush=True,
                        )
                    print()

            # atomic replace
            shutil.move(tmp, dest)
            return

        except Exception as e:
            print(f"  Download failed: {e}")
            if os.path.exists(tmp):
                os.remove(tmp)
            time.sleep(1)

    raise Exception(f"Failed to download after {DOWNLOAD_RETRY_COUNT} attempts: {url}")


def already_updated(dest, expected_hash):
    if not os.path.exists(dest):
        return False
    try:
        return sha1(dest) == expected_hash
    except:
        return False


def traverse(node, path_parts):
    t = node["type"]
    name = node["name"]
    
    # Reject any names containing slashes or directory traversal characters
    if any(c in name for c in ['/', '\\']) or name in ['.', '..']:
        print(f"SECURITY ALERT: Rejected invalid file/folder name: {name}")
        return

    current = path_parts + [name]
    rel_path = os.path.join(*current)
    
    # Ensure the absolute path of the destination strictly stays inside OUT_DIR
    out_dir_abs = os.path.abspath(OUT_DIR)
    dest_abs = os.path.abspath(os.path.join(OUT_DIR, rel_path))
    
    # The commonpath of the root directory and target must be the root directory
    if os.path.commonpath([out_dir_abs, dest_abs]) != out_dir_abs:
        print(f"SECURITY ALERT: Path traversal attempt blocked: {rel_path}")
        return
    
    # If safe, proceed with the original logic
    dest = dest_abs
    rel_url = "/".join(current)
    url = f"{SERVER}/client/{DOWNLOAD_VERSION}/{rel_url}"

    if t == "dir":
        for child in node.get("files", []):
            traverse(child, current)

    elif t == "file":
        print(f"[file] {rel_path}")

        if already_updated(dest, node["hash"]):
            print("  Already up to date.")
            return

        download(url, dest, node["size"])

        # verify after download
        if sha1(dest) != node["hash"]:
            print("  Hash mismatch -> re-downloading")
            safe_remove(dest)
            download(url, dest, node["size"])

    elif t == "mpq":
        mpq_name = name + ".mpq"
        current_mpq = path_parts + [mpq_name]

        rel_path = os.path.join(*current_mpq)
        dest = os.path.join(OUT_DIR, rel_path)
        url = f"{SERVER}/client/{DOWNLOAD_VERSION}/{'/'.join(current_mpq)}"

        print(f"[mpq] {rel_path}")

        if already_updated(dest, node["hash"]):
            print("  Already up to date.")
            return

        download(url, dest, node["size"])

        if sha1(dest) != node["hash"]:
            print("  Hash mismatch -> re-downloading")
            safe_remove(dest)
            download(url, dest, node["size"])

    elif t == "del":
        print(f"[del] {rel_path}")
        safe_remove(dest)


# TODO: rewrite this
def build_tweaks(buf):
    DEFAULT_FOV_DEGREES = 90  # for 16:9 screen ratio
    fov_radians = DEFAULT_FOV_DEGREES * (math.pi / 180.0)

    # largeAddress: set IMAGE_FILE_LARGE_ADDRESS_AWARE flag in PE header
    current_flags = struct.unpack_from("<H", buf, 0x126)[0]
    large_address_value = current_flags | 0x20

    # fmt: off
    return [
        # (label, type, offset, value)
        ("largeAddress",          "uint16", 0x126,     large_address_value),
        ("fieldOfView",           "float",  0x4089b4,  fov_radians),
        ("cameraDistance",        "float",  0x4089a4,  50.0),  # WoW default
        ("farClip",               "float",  0x40fed8,  777.0), # WoW default
        ("frillDistance",         "float",  0x467958,  70.0),  # WoW default
        ("nameplateRange",        "float",  0x40c448,  20.0),  # WoW default
        ("soundInBackground",     "int8",   0x3a4869,  0x27),  # enabled (0x14 = disabled)
        ("alwaysAutoLoot",        "bytes",  None, [
            (0x0c1ecf, bytes([0x75])),
            (0x0c2b25, bytes([0x75])),
        ]),
        ("crossFactionResurrect", "bytes",  None, [
            (0x006e5fb8, bytes([0x006e5fb9 & 0xff])),
            (0x006e62a8, bytes([0x006e62a9 & 0xff])),
        ]),
        ("cameraSkipFix",         "bytes",  None, [
            (0x02ccd0, bytes([
                0x55, 0x8b, 0x05, 0x48, 0x4e, 0x88, 0x00, 0x8b, 0x0d, 0x44, 0x4e, 0x88, 0x00, 0xe9, 0x33, 0x90,
                0x32, 0x00, 0x83, 0xc0, 0x32, 0x83, 0xc1, 0x32, 0x3b, 0x0d, 0xa8, 0xeb, 0xc4, 0x00, 0x7e, 0x03,
                0x83, 0xe9, 0x01, 0x3b, 0x05, 0xac, 0xeb, 0xc4, 0x00, 0x7e, 0x03, 0x83, 0xe8, 0x01, 0x83, 0xe9,
                0x32, 0x83, 0xe8, 0x32, 0x89, 0x05, 0x48, 0x4e, 0x88, 0x00, 0x89, 0x0d, 0x44, 0x4e, 0x88, 0x00,
                0x5d, 0xeb, 0x0d,
            ])),
            (0x02d326, bytes([0xe9, 0xb1, 0x8a, 0x32, 0x00])),
            (0x02d334, bytes([0x8b, 0x35, 0x48, 0x4e, 0x88, 0x00])),
            (0x355d15, bytes([
                0x83, 0xf8, 0x32, 0x7d, 0x03, 0x83, 0xc0, 0x01, 0x83, 0xf9, 0x32,
                0x7d, 0x03, 0x83, 0xc1, 0x01, 0xe9, 0xb8, 0x6f, 0xcd, 0xff,
            ])),
            (0x355ddc, bytes([
                0x8d, 0x4d, 0xf0, 0x51,
                0xff, 0x35, 0x00, 0x4e, 0x88, 0x00, 0xff, 0x15, 0x50, 0xf6, 0x7f, 0x00, 0x8b, 0x45, 0xf0, 0x8b,
                0x15, 0x44, 0x4e, 0x88, 0x00, 0xe9, 0x35, 0x75, 0xcd, 0xff,
            ])),
        ]),
        ("skillUiGateHijack",     "bytes",  None, [
            (0x002ddf90, bytes([
                0x55, 0x8b, 0xec, 0x83, 0xec, 0x08, 0x53, 0x56,
                0x57, 0x8b, 0x3d, 0x60, 0xab, 0xce, 0x00, 0x83,
                0xff, 0xff, 0x89, 0x55, 0xfc, 0x89, 0x4d, 0xf8,
                0x74, 0x79, 0x8b, 0x75, 0x08, 0x8b, 0x15, 0x58,
                0xab, 0xce, 0x00, 0x8b, 0xc7, 0x23, 0xc6, 0x8d,
                0x04, 0x40, 0x8b, 0x4c, 0x82, 0x08, 0xf6, 0xc1,
                0x01, 0x8d, 0x44, 0x82, 0x04, 0x75, 0x04, 0x85,
                0xc9, 0x75, 0x05, 0x33, 0xc9, 0x8d, 0x49, 0x00,
                0xf6, 0xc1, 0x01, 0x75, 0x4e, 0x85, 0xc9, 0x74,
                0x4a, 0x39, 0x31, 0x74, 0x13, 0x8b, 0xc7, 0x23,
                0xc6, 0x8d, 0x04, 0x40, 0x8d, 0x04, 0x82, 0x8b,
                0x00, 0x03, 0xc1, 0x8b, 0x48, 0x04, 0xeb, 0xe0,
                0x8b, 0x59, 0x1c, 0x8b, 0x71, 0x18, 0x33, 0xff,
                0x85, 0xdb, 0x7e, 0x27, 0x8d, 0x64, 0x24, 0x00,
                0x8b, 0x4e, 0x0c, 0x8b, 0x56, 0x08, 0x6a, 0x00,
                0x6a, 0x00, 0x51, 0x8b, 0x4d, 0xf8, 0x52, 0x8b,
                0x55, 0xfc, 0xe8, 0xb9, 0xfd, 0xff, 0xff, 0x84,
                0xc0, 0x75, 0x13, 0x47, 0x83, 0xc6, 0x20, 0x3b,
                0xfb, 0x7c, 0xdd, 0x5f, 0x5e, 0x33, 0xc0, 0x5b,
                0x8b, 0xe5, 0x5d, 0xc2, 0x04, 0x00, 0x5f, 0x8b,
                0xc6, 0x5e, 0x5b, 0x8b, 0xe5, 0x5d, 0xc2, 0x04,
                0x00, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90,
            ])),
        ]),
    ]
    # fmt: on


def patch_exe():
    exe_path = os.path.join(OUT_DIR, "WoW.exe")
    if not os.path.exists(exe_path):
        raise Exception(f"{exe_path} is not found\n")

    print("\nApplying tweaks to WoW.exe...\n")

    with open(exe_path, "rb") as f:
        buf = bytearray(f.read())

    for label, kind, offset, value in build_tweaks(buf):
        print(f"  Applying: {label}")
        if kind == "float":
            struct.pack_into("<f", buf, offset, value)
        elif kind == "int8":
            struct.pack_into("<b", buf, offset, value)
        elif kind == "uint16":
            struct.pack_into("<H", buf, offset, value)
        elif kind == "bytes":
            for off, data in value:
                buf[off : off + len(data)] = data

    with open(exe_path, "wb") as f:
        f.write(buf)

    print("\nWoW.exe patched successfully!")


def get_display_info():
    import ctypes

    ENUM_CURRENT_SETTINGS = -1

    class DEVMODE(ctypes.Structure):
        _fields_ = [
            ("dmDeviceName", ctypes.c_wchar * 32),
            ("dmSpecVersion", ctypes.c_ushort),
            ("dmDriverVersion", ctypes.c_ushort),
            ("dmSize", ctypes.c_ushort),
            ("dmDriverExtra", ctypes.c_ushort),
            ("dmFields", ctypes.c_ulong),
            ("dmPositionX", ctypes.c_long),
            ("dmPositionY", ctypes.c_long),
            ("dmDisplayOrientation", ctypes.c_ulong),
            ("dmDisplayFixedOutput", ctypes.c_ulong),
            ("dmColor", ctypes.c_short),
            ("dmDuplex", ctypes.c_short),
            ("dmYResolution", ctypes.c_short),
            ("dmTTOption", ctypes.c_short),
            ("dmCollate", ctypes.c_short),
            ("dmFormName", ctypes.c_wchar * 32),
            ("dmLogPixels", ctypes.c_ushort),
            ("dmBitsPerPel", ctypes.c_ulong),
            ("dmPelsWidth", ctypes.c_ulong),
            ("dmPelsHeight", ctypes.c_ulong),
            ("dmDisplayFlags", ctypes.c_ulong),
            ("dmDisplayFrequency", ctypes.c_ulong),
        ]

    devmode = DEVMODE()
    devmode.dmSize = ctypes.sizeof(DEVMODE)

    ctypes.windll.user32.EnumDisplaySettingsW(
        None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)
    )

    return {
        "width": devmode.dmPelsWidth,
        "height": devmode.dmPelsHeight,
        "refresh_rate": devmode.dmDisplayFrequency,
    }


def patch_config():
    config_dir = os.path.join(OUT_DIR, "WTF")
    ensure_dir(config_dir)

    print("\nApplying Config.wtf variables...")

    config_path = os.path.join(config_dir, "Config.wtf")
    if os.path.exists(config_path):
        print("\nConfig.wtf already exists, skipping.")
        return

    display_info = get_display_info()
    server_name = "octowow.st"

    variables = {
        "realmList": server_name,
        "patchList": server_name,
        "scriptMemory": 512000,
        "gxResolution": f"{display_info['width']}x{display_info['height']}",
        "gxVSync": 0,
        "gxColorBits": 24,
        "gxDepthBits": 24,
        "gxRefresh": display_info["refresh_rate"],
        "gxMultisampleQuality": 0,
        "gxMultisample": 2,
        "gxWindow": 1,
        "gxMaximize": 1,
        "anisotropic": 16,
        "trilinear": 1,
        "specular": 1,
        "shadowLevel": 0,
        "lod": 0,
        "hwDetect": 0,
        "pixelShaders": 1,
        "M2UsePixelShaders": 1,
        "particleDensity": 1,
        "unitDrawDist": 300,
        "weatherDensity": 3,
        "movieSubtitle": 1,
        "CameraDistanceMax": 50,
        "farClip": 777,
        "frillDensity": 48,
        "fullAlpha": 1,
        "SmallCull": 0.01,
        "DistCull": 888.8,
        "minimapZoom": 0,
        "minimapInsideZoom": 0,
        "SoundZoneMusicNoDelay": 1,
        "SoundMaxHardwareChannels": 64,
        "SoundSoftwareChannels": 64,
        "readTOS": 1,
        "readEULA": 1,
    }

    with open(config_path, "w", encoding="utf-8") as f:
        for k, v in variables.items():
            if v is not None:
                f.write(f'SET {k} "{v}"\n')

    print("\nConfig.wtf variables applied successfully!")


def fetch_manifest():
    print("\nFetching manifest.json...")

    req = urllib.request.Request(
        f"{SERVER}/api/file/{DOWNLOAD_VERSION}/manifest.json",
        headers={"User-Agent": UA},
    )

    with urllib.request.urlopen(req) as r:
        manifest = json.load(r)

    print("\nmanifest.json fetched successfully!")
    return manifest


def download_client(manifest):
    print("\nStarting OctoWoW client update...\n")

    root = manifest["root"]
    for child in root.get("files", []):
        traverse(child, [])

    print("\nOctoWoW client update completed successfully!")


def apply_patcher():
    patch_exe()
    patch_config()


# main entry point

print(f"OctoWoW Updater {UPDATER_VERSION}")
print(
    "\nFor questions or support, contact me on Discord: rebazed (discord.com/users/287467238573867018)"
)  # please credit the original author

manifest = fetch_manifest()
download_client(manifest)
apply_patcher()

print("\nEverything is ready! You can close this window.")
input()
