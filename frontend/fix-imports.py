#!/usr/bin/env python3
"""
Fix import paths in frontend/app/[locale]/ folder
This script systematically fixes import paths based on file structure
"""

import os
import re
import sys
from pathlib import Path


def get_relative_path_to_app(file_path):
    """Calculate relative path from file to app directory"""
    file_dir = os.path.dirname(file_path)
    # Navigate from [locale]/folder/subfolder/file -> app/
    # We need to go up to [locale] then up to app
    path_parts = Path(file_dir).parts
    locale_index = -1

    for i, part in enumerate(path_parts):
        if part == "[locale]":
            locale_index = i
            break

    if locale_index == -1:
        return "./"  # fallback

    # Count directories after [locale]
    depth_after_locale = len(path_parts) - locale_index - 1

    if depth_after_locale == 0:
        return "./"
    else:
        return "../" * depth_after_locale


def get_relative_path_to_frontend_components(file_path):
    """Calculate relative path from file to frontend/components directory"""
    file_dir = os.path.dirname(file_path)
    components_dir = os.path.join(
        os.path.dirname(os.path.dirname(file_path)), "components"
    )

    relative = os.path.relpath(components_dir, file_dir)
    return (
        relative.replace("\\", "/") + "/"
        if not relative.endswith("/")
        else relative.replace("\\", "/")
    )


def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        new_content = content

        # Get relative paths
        path_to_app = get_relative_path_to_app(file_path)
        path_to_components = get_relative_path_to_frontend_components(file_path)

        # Manual string replacement for common patterns
        lines = new_content.split("\n")
        fixed_lines = []

        for line in lines:
            fixed_line = line

            # Fix context imports
            if re.search(r'from\s+[\'"](\.\.?\/)*context\/', fixed_line):
                fixed_line = re.sub(
                    r'from\s+[\'"](\.\.?\/)*context\/([^\'"]+)[\'"]',
                    f"from '{path_to_app}context/\\2'",
                    fixed_line,
                )

            # Fix lib imports
            if re.search(r'from\s+[\'"](\.\.?\/)*lib\/', fixed_line):
                fixed_line = re.sub(
                    r'from\s+[\'"](\.\.?\/)*lib\/([^\'"]+)[\'"]',
                    f"from '{path_to_app}lib/\\2'",
                    fixed_line,
                )

            # Fix utils imports
            if re.search(r'from\s+[\'"](\.\.?\/)*utils\/', fixed_line):
                fixed_line = re.sub(
                    r'from\s+[\'"](\.\.?\/)*utils\/([^\'"]+)[\'"]',
                    f"from '{path_to_app}utils/\\2'",
                    fixed_line,
                )

            # Fix components/ui imports
            if re.search(r'from\s+[\'"](\.\.?\/)*components\/ui\/', fixed_line):
                fixed_line = re.sub(
                    r'from\s+[\'"](\.\.?\/)*components\/ui\/([^\'"]+)[\'"]',
                    f"from '{path_to_app}components/ui/\\2'",
                    fixed_line,
                )

            # Fix other components imports
            if re.search(
                r'from\s+[\'"](\.\.?\/)*components\/[^\/\"]+[\'"]', fixed_line
            ):
                fixed_line = re.sub(
                    r'from\s+[\'"](\.\.?\/)*components\/([^\'"/]+)[\'"]',
                    f"from '{path_to_app}components/\\1'",
                    fixed_line,
                )

            # Fix frontend/components imports (../../components/)
            if re.search(r'from\s+[\'"]\.\.?\/\.\.?\/components\/', fixed_line):
                fixed_line = re.sub(
                    r'from\s+[\'"]\.\.?\/\.\.?\/components\/([^\'"]+)[\'"]',
                    f"from '{path_to_components}\\1'",
                    fixed_line,
                )

            fixed_lines.append(fixed_line)

        new_content = "\n".join(fixed_lines)

        # Normalize path separators to forward slashes
        new_content = new_content.replace("\\", "/")

        # Write back if changed
        if new_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True

        return False

    except Exception as e:
        print(f"    Error: {e}")
        return False


def main():
    """Main function"""
    frontend_dir = Path(__file__).parent
    locale_dir = frontend_dir / "app" / "[locale]"

    if not locale_dir.exists():
        print(f"Directory not found: {locale_dir}")
        return 1

    print("Fixing import paths in frontend/app/[locale]/...")
    print()

    # Find all TypeScript files
    files = []
    for ext in ["*.ts", "*.tsx"]:
        files.extend(locale_dir.rglob(ext))

    print(f"Found {len(files)} TypeScript files")
    print()

    fixed_count = 0
    error_count = 0

    # Process each file
    for file_path in sorted(files):
        relative_path = file_path.relative_to(frontend_dir)
        print(f"Processing: {relative_path}")

        try:
            was_fixed = fix_imports_in_file(file_path)
            if was_fixed:
                print(f"    Fixed")
                fixed_count += 1
            else:
                print(f"    No changes needed")
        except Exception as e:
            print(f"    Error: {e}")
            error_count += 1
        print()

    # Summary
    print("Summary:")
    print(f"   Fixed: {fixed_count} files")
    print(f"   No changes: {len(files) - fixed_count - error_count} files")
    if error_count > 0:
        print(f"   Errors: {error_count} files")
    print()
    print("Import path fixing complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
