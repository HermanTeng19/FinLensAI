#!/usr/bin/env python3
"""FinLens AI — Multiplatform App Icon Deployment Tool.

Configures Apple Asset Catalogs for iOS and macOS:
1. iOS: Deploys AppIcon_iOS_1024_green.png as the official iOS App Icon.
2. macOS: Deploys AppIcon_macOS_1024.png and generates all native resolution scales (16x16 through 1024x1024).
"""

import json
import os
import shutil
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
RESOURCES_DIR = os.path.join(ROOT_DIR, "apple", "FinLens", "Resources")
ASSETS_DIR = os.path.join(RESOURCES_DIR, "Assets.xcassets")

IOS_SOURCE = os.path.join(RESOURCES_DIR, "AppIcon_iOS_1024_green.png")
MACOS_SOURCE = os.path.join(RESOURCES_DIR, "AppIcon_macOS_1024.png")

# macOS icon resolution map (size_str, scale_str, pixel_size)
MACOS_SCALES = [
    ("16x16", "1x", 16),
    ("16x16", "2x", 32),
    ("32x32", "1x", 32),
    ("32x32", "2x", 64),
    ("128x128", "1x", 128),
    ("128x128", "2x", 256),
    ("256x256", "1x", 256),
    ("256x256", "2x", 512),
    ("512x512", "1x", 512),
    ("512x512", "2x", 1024),
]


def setup_ios_appiconset():
    ios_set_dir = os.path.join(ASSETS_DIR, "AppIcon-iOS.appiconset")
    os.makedirs(ios_set_dir, exist_ok=True)
    
    print("--> Deploying iOS App Icon (Emerald Green)...")
    img = Image.open(IOS_SOURCE).convert("RGB")
    dest_img = os.path.join(ios_set_dir, "AppIcon_iOS.png")
    img.save(dest_img, format="PNG", optimize=True)
    
    contents = {
        "images": [
            {
                "filename": "AppIcon_iOS.png",
                "idiom": "universal",
                "platform": "ios",
                "size": "1024x1024"
            }
        ],
        "info": {
            "author": "xcode",
            "version": 1
        }
    }
    
    with open(os.path.join(ios_set_dir, "Contents.json"), "w", encoding="utf-8") as f:
        json.dump(contents, f, indent=2)
    print("✓ AppIcon-iOS.appiconset configured successfully.")


def setup_macos_appiconset():
    macos_set_dir = os.path.join(ASSETS_DIR, "AppIcon-macOS.appiconset")
    os.makedirs(macos_set_dir, exist_ok=True)
    
    print("--> Deploying macOS App Icon (Sapphire & Titanium) with all resolutions...")
    src_img = Image.open(MACOS_SOURCE).convert("RGB")
    
    images_list = []
    for size_str, scale_str, px in MACOS_SCALES:
        filename = f"icon_{size_str}@{scale_str}.png" if scale_str == "2x" else f"icon_{size_str}.png"
        out_path = os.path.join(macos_set_dir, filename)
        resized = src_img.resize((px, px), Image.Resampling.LANCZOS)
        resized.save(out_path, format="PNG", optimize=True)
        
        images_list.append({
            "size": size_str,
            "idiom": "mac",
            "filename": filename,
            "scale": scale_str
        })
    
    contents = {
        "images": images_list,
        "info": {
            "author": "xcode",
            "version": 1
        }
    }
    
    with open(os.path.join(macos_set_dir, "Contents.json"), "w", encoding="utf-8") as f:
        json.dump(contents, f, indent=2)
    print("✓ AppIcon-macOS.appiconset configured successfully (10 scale assets generated).")


def setup_unified_appiconset():
    unified_dir = os.path.join(ASSETS_DIR, "AppIcon.appiconset")
    os.makedirs(unified_dir, exist_ok=True)
    
    print("--> Configuring fallback unified AppIcon.appiconset...")
    # 1. Copy iOS 1024
    ios_img = Image.open(IOS_SOURCE).convert("RGB")
    ios_dest = os.path.join(unified_dir, "AppIcon_iOS.png")
    ios_img.save(ios_dest, format="PNG", optimize=True)
    
    # 2. Copy macOS scales
    src_img = Image.open(MACOS_SOURCE).convert("RGB")
    images_list = [
        {
            "filename": "AppIcon_iOS.png",
            "idiom": "universal",
            "platform": "ios",
            "size": "1024x1024"
        }
    ]
    
    for size_str, scale_str, px in MACOS_SCALES:
        filename = f"icon_{size_str}@{scale_str}.png" if scale_str == "2x" else f"icon_{size_str}.png"
        out_path = os.path.join(unified_dir, filename)
        resized = src_img.resize((px, px), Image.Resampling.LANCZOS)
        resized.save(out_path, format="PNG", optimize=True)
        
        images_list.append({
            "size": size_str,
            "idiom": "mac",
            "filename": filename,
            "scale": scale_str
        })
        
    contents = {
        "images": images_list,
        "info": {
            "author": "xcode",
            "version": 1
        }
    }
    
    with open(os.path.join(unified_dir, "Contents.json"), "w", encoding="utf-8") as f:
        json.dump(contents, f, indent=2)
    print("✓ Unified AppIcon.appiconset configured successfully.")


def main():
    print("======================================================================")
    print("     FinLens AI — Multiplatform App Icon Deployment Tool")
    print("======================================================================")
    if not os.path.exists(IOS_SOURCE):
        raise FileNotFoundError(f"iOS source icon not found: {IOS_SOURCE}")
    if not os.path.exists(MACOS_SOURCE):
        raise FileNotFoundError(f"macOS source icon not found: {MACOS_SOURCE}")
        
    setup_ios_appiconset()
    setup_macos_appiconset()
    setup_unified_appiconset()
    print("======================================================================")
    print("  🎉 MULTIPLATFORM APP ICONS SUCCESSFULLY DEPLOYED TO XCODE ASSETS 🎉")
    print("======================================================================")


if __name__ == "__main__":
    main()
