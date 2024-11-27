"""This script creates a list of PNG files in the specified directory and saves it to a text file.

Usage of script: python create_image_list.py <directory> <output>
"""

import argparse
from pathlib import Path


def create_file_list(directory: Path, output_file: Path) -> None:
    """Create a list of PNG files in the directory and save to a text file."""
    image_files = sorted(directory.glob("*.png"))

    if not image_files:
        print("No PNG files found.")
        return
    print(f"Found {len(image_files)} PNG files")
    with output_file.open("w") as f:
        for file in image_files:
            f.write(f"{file.stem}\n")
    print(f"File list saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Create a list of PNG files in the specified directory")
    parser.add_argument("directory", type=Path, help="Directory containing the images")
    parser.add_argument("output", type=Path, help="Path where to save the file list")
    args = parser.parse_args()

    if not args.directory.exists():
        print(f"Error: Directory '{args.directory}' does not exist")
        return
    if not args.output.parent.exists():
        print(f"Error: Output directory '{args.output.parent}' does not exist")
        return
    if args.output.suffix != ".txt":
        print(f"Error: Output file '{args.output}' must have a .txt suffix")
        return

    create_file_list(args.directory, args.output)


if __name__ == "__main__":
    main()
