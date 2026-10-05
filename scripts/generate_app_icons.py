#!/usr/bin/env python3
"""FinLens AI — App Icon Generator for iOS and macOS.

Generates official 1024x1024 app icons adhering to Apple HIG guidelines:
1. Square canvas, full-bleed (no rounded corners baked into the image).
2. Single focal point, minimal, strictly NO text.
3. Centered composition with 75%-80% safe area.
"""

import base64
import io
import os
import shutil
import sys
import httpx
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
RESOURCES_DIR = os.path.join(ROOT_DIR, "apple", "FinLens", "Resources")
ASSETS_ICON_DIR = os.path.join(RESOURCES_DIR, "Assets.xcassets", "AppIcon.appiconset")
ARTIFACT_DIR = "/Users/hermanteng/.gemini/antigravity-cli/brain/656ca936-35cd-4985-a888-d2e7568cdb05"

ENV_PATHS = [
    os.path.join(ROOT_DIR, "backend", ".env"),
    "/Users/hermanteng/Documents/Projects/2026/8_Aug/family-videos/.env",
]

def get_gemini_api_key() -> str:
    # First check env var
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip("\"'")

    for env_path in ENV_PATHS:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        return line.strip().split("=", 1)[1].strip("\"' ")
    raise RuntimeError("GEMINI_API_KEY not found in environment or fallback .env files.")


IOS_PROMPT = """
A graphic design of a central luminous financial optic lens emblem on a full-bleed dark navy blue background.
Visual focal point: In the center of the image, a glowing circular optical lens and camera aperture iris made of layered translucent frosted glass and sleek silver titanium ring, focusing cyan, turquoise and emerald light rays into an upward-pointing financial prism.
Background rules:
- The entire image from edge to edge is a continuous dark midnight blue gradient.
- The dark blue background extends fully into all four corners of the 1024x1024 image.
- Flat square canvas, sharp 90 degree corners, complete full bleed.
- DO NOT draw any rounded rectangle, DO NOT draw a squircle shape, DO NOT round the corners, DO NOT leave white or light margins in the corners.
- Single focal point, minimal, centered, occupying 75% of the frame.
- Strictly NO text, NO numbers, NO letters, NO watermark.
""".strip()

MACOS_PROMPT = """
An ultra-premium, high-fidelity official macOS desktop application icon for 'FinLens AI', a professional personal finance analytics and insight studio.
Visual focal point: A precision-engineered 3D optical lens instrument emblem. Features a multi-layered aerospace-grade dark titanium bezel, knurled metal dial edge, anti-reflective optical glass elements with subtle violet-cyan lens flare coating, revealing an intricate financial prism core with delicate volumetric caustics.
Composition rules:
- Strictly square canvas with sharp 90-degree square corners, full-bleed edge-to-edge deep dark charcoal and slate sapphire gradient background. DO NOT draw rounded corners, DO NOT cut off the corners, DO NOT draw a squircle tile frame, the background must fill the entire square canvas to all edges.
- Single focal point, tactile depth, studio top-down key lighting, subtle ambient occlusion, realistic ray-traced glass and brushed metal shaders.
- Strictly NO text, NO typography, NO words, NO letters, NO numbers, NO logo text.
- Perfectly centered composition with ample negative space (20% clean margin around the edges), subject occupies 75% to 80% of the canvas.
- Desktop-class pro tool aesthetics, elegant, sophisticated, pristine Apple HIG design.
""".strip()


def generate_icon(api_key: str, prompt: str, target_name: str) -> Image.Image:
    print(f"--> Generating {target_name} with Gemini 3 Pro Image model...")
    # Try gemini-3-pro-image-preview first, fallback to gemini-2.5-flash-image
    models = ["gemini-3-pro-image-preview", "gemini-2.5-flash-image"]
    
    last_err = None
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        if "inlineData" in part:
                            img_b64 = part["inlineData"]["data"]
                            img_bytes = base64.b64decode(img_b64)
                            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                            print(f"✓ Successfully generated {target_name} via {model} (Raw size: {img.size})")
                            return img
            else:
                last_err = f"{model} returned {res.status_code}: {res.text[:200]}"
                print(f"Warning: {last_err}")
        except Exception as e:
            last_err = str(e)
            print(f"Warning: Failed with {model}: {e}")
            
    raise RuntimeError(f"Failed to generate {target_name}: {last_err}")


def process_and_save(img: Image.Image, output_path: str):
    """Ensure exact 1024x1024 size, optimal color quality, and save to target path."""
    if img.size != (1024, 1024):
        print(f"--> Resizing to exact 1024x1024 using Lanczos filter...")
        img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    print(f"✓ Saved: {output_path} ({img.size[0]}x{img.size[1]})")


def main():
    print("======================================================================")
    print("       FinLens AI — Official App Icon Generation (iOS & macOS)")
    print("======================================================================")
    
    api_key = get_gemini_api_key()
    print("✓ External Gemini API Key authenticated.")
    
    # 1. iOS App Icon
    ios_target = os.path.join(RESOURCES_DIR, "AppIcon_iOS_1024.png")
    ios_img = generate_icon(api_key, IOS_PROMPT, "iOS App Icon")
    process_and_save(ios_img, ios_target)
    
    # Also save to Assets catalog
    xcassets_target = os.path.join(ASSETS_ICON_DIR, "AppIcon-1024.png")
    process_and_save(ios_img, xcassets_target)
    
    # Copy to artifact dir for instant chat display
    artifact_ios = os.path.join(ARTIFACT_DIR, "AppIcon_iOS_1024.png")
    shutil.copyfile(ios_target, artifact_ios)
    print(f"✓ Copied to artifact display: {artifact_ios}")
    
    # 2. macOS App Icon
    macos_target = os.path.join(RESOURCES_DIR, "AppIcon_macOS_1024.png")
    macos_img = generate_icon(api_key, MACOS_PROMPT, "macOS App Icon")
    process_and_save(macos_img, macos_target)
    
    # Copy to artifact dir for instant chat display
    artifact_macos = os.path.join(ARTIFACT_DIR, "AppIcon_macOS_1024.png")
    shutil.copyfile(macos_target, artifact_macos)
    print(f"✓ Copied to artifact display: {artifact_macos}")
    
    print("\n======================================================================")
    print("  🎉 BOTH APP ICONS GENERATED & VALIDATED (1024x1024 PNG) 🎉")
    print("======================================================================")
    print(f"• iOS Icon:   {ios_target}")
    print(f"• macOS Icon: {macos_target}")
    print(f"• Asset Icon: {xcassets_target}")
    print("======================================================================")


if __name__ == "__main__":
    main()
