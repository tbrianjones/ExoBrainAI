#!/usr/bin/env python3
"""
Simple Gemini API utility for image and text generation.

Usage:
    python scripts/gemini.py image "a sunset over mountains" --output sunset.png
    python scripts/gemini.py text "Explain quantum computing simply"
"""

import argparse
import os
import sys
import warnings
from pathlib import Path

# Suppress Python 3.9 deprecation warnings from google libraries
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*urllib3.*")

from dotenv import load_dotenv


def get_client():
    """Initialize and return the Gemini client."""
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("Error: GEMINI_API_KEY not set in .env file", file=sys.stderr)
        print("Get your API key from https://aistudio.google.com/app/apikey", file=sys.stderr)
        sys.exit(1)

    return genai.Client(api_key=api_key)


def generate_image(prompt: str, output_path: str, number_of_images: int = 1):
    """Generate an image using Imagen 4. Requires billing enabled."""
    from google.genai import types

    client = get_client()

    print(f"Generating image: {prompt[:50]}...")

    try:
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=number_of_images,
            )
        )
    except Exception as e:
        error_msg = str(e)
        if "billed users" in error_msg.lower() or "billing" in error_msg.lower():
            print("Error: Image generation requires billing to be enabled.", file=sys.stderr)
            print("Enable billing at: https://console.cloud.google.com/billing", file=sys.stderr)
            sys.exit(1)
        elif "quota" in error_msg.lower() or "limit: 0" in error_msg.lower():
            print("Error: Image generation requires billing (no free tier).", file=sys.stderr)
            print("Enable billing at: https://console.cloud.google.com/billing", file=sys.stderr)
            sys.exit(1)
        raise

    if not response.generated_images:
        print("Error: No images generated", file=sys.stderr)
        sys.exit(1)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    for i, image in enumerate(response.generated_images):
        if number_of_images == 1:
            save_path = output
        else:
            save_path = output.parent / f"{output.stem}_{i}{output.suffix}"

        image.image.save(str(save_path))
        print(f"Saved: {save_path}")


def generate_text(prompt: str, model: str = "gemini-2.5-flash-lite"):
    """Generate text using Gemini."""
    client = get_client()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    print(response.text)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Gemini API utility for image and text generation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Image subcommand
    image_parser = subparsers.add_parser("image", help="Generate an image")
    image_parser.add_argument("prompt", help="Image description prompt")
    image_parser.add_argument(
        "--output", "-o",
        default="output/generated.png",
        help="Output file path (default: output/generated.png)"
    )
    image_parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        help="Number of images to generate (default: 1)"
    )

    # Text subcommand
    text_parser = subparsers.add_parser("text", help="Generate text")
    text_parser.add_argument("prompt", help="Text prompt")
    text_parser.add_argument(
        "--model", "-m",
        default="gemini-2.5-flash-lite",
        help="Model to use (default: gemini-2.5-flash-lite)"
    )

    args = parser.parse_args()

    if args.command == "image":
        generate_image(args.prompt, args.output, args.count)
    elif args.command == "text":
        generate_text(args.prompt, args.model)


if __name__ == "__main__":
    main()
