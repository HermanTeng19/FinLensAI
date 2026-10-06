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


# iOS icon resolution map (idiom, size_str, scale_str, pixel_size)
IOS_SCALES = [
    # iPhone
    ("iphone", "20x20", "2x", 40),
    ("iphone", "20x20", "3x", 60),
    ("iphone", "29x29", "2x", 58),
    ("iphone", "29x29", "3x", 87),
    ("iphone", "40x40", "2x", 80),
    ("iphone", "40x40", "3x", 120),
    ("iphone", "60x60", "2x", 120),
    ("iphone", "60x60", "3x", 180),
    # iPad
    ("ipad", "20x20", "1x", 20),
    ("ipad", "20x20", "2x", 40),
    ("ipad", "29x29", "1x", 29),
    ("ipad", "29x29", "2x", 58),
    ("ipad", "40x40", "1x", 40),
    ("ipad", "40x40", "2x", 80),
    ("ipad", "76x76", "1x", 76),
    ("ipad", "76x76", "2x", 152),
    ("ipad", "83.5x83.5", "2x", 167),
    # App Store / Marketing
    ("ios-marketing", "1024x1024", "1x", 1024),
]


def setup_ios_appiconset():
    ios_set_dir = os.path.join(ASSETS_DIR, "AppIcon-iOS.appiconset")
    os.makedirs(ios_set_dir, exist_ok=True)
    
    print("--> Deploying iOS & iPadOS App Icon (Emerald Green) across all native resolutions...")
    src_img = Image.open(IOS_SOURCE).convert("RGB")
    
    images_list = []
    for idiom, size_str, scale_str, px in IOS_SCALES:
        filename = f"icon_{idiom}_{size_str}@{scale_str}.png"
        out_path = os.path.join(ios_set_dir, filename)
        resized = src_img.resize((px, px), Image.Resampling.LANCZOS)
        resized.save(out_path, format="PNG", optimize=True)
        
        images_list.append({
            "size": size_str,
            "idiom": idiom,
            "filename": filename,
            "scale": scale_str
        })
    
    # Also include universal 1024x1024 for modern Xcode 15+ compatibility
    universal_dest = os.path.join(ios_set_dir, "AppIcon_iOS_universal.png")
    src_img.save(universal_dest, format="PNG", optimize=True)
    images_list.append({
        "size": "1024x1024",
        "idiom": "universal",
        "platform": "ios",
        "filename": "AppIcon_iOS_universal.png"
    })
    
    contents = {
        "images": images_list,
        "info": {
            "author": "xcode",
            "version": 1
        }
    }
    
    with open(os.path.join(ios_set_dir, "Contents.json"), "w", encoding="utf-8") as f:
        json.dump(contents, f, indent=2)
    print(f"✓ AppIcon-iOS.appiconset configured successfully ({len(images_list)} scales generated).")


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
    
    print("--> Configuring fallback unified AppIcon.appiconset with all platforms & scales...")
    images_list = []

    # 1. iOS & iPadOS scales
    ios_src_img = Image.open(IOS_SOURCE).convert("RGB")
    for idiom, size_str, scale_str, px in IOS_SCALES:
        filename = f"icon_{idiom}_{size_str}@{scale_str}.png"
        out_path = os.path.join(unified_dir, filename)
        resized = ios_src_img.resize((px, px), Image.Resampling.LANCZOS)
        resized.save(out_path, format="PNG", optimize=True)
        
        images_list.append({
            "size": size_str,
            "idiom": idiom,
            "filename": filename,
            "scale": scale_str
        })
    
    # Universal iOS
    universal_dest = os.path.join(unified_dir, "AppIcon_iOS_universal.png")
    ios_src_img.save(universal_dest, format="PNG", optimize=True)
    images_list.append({
        "size": "1024x1024",
        "idiom": "universal",
        "platform": "ios",
        "filename": "AppIcon_iOS_universal.png"
    })
    
    # 2. macOS scales
    mac_src_img = Image.open(MACOS_SOURCE).convert("RGB")
    for size_str, scale_str, px in MACOS_SCALES:
        filename = f"icon_mac_{size_str}@{scale_str}.png" if scale_str == "2x" else f"icon_mac_{size_str}.png"
        out_path = os.path.join(unified_dir, filename)
        resized = mac_src_img.resize((px, px), Image.Resampling.LANCZOS)
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
    print(f"✓ Unified AppIcon.appiconset configured successfully ({len(images_list)} scales generated).")


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
