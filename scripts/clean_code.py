#!/usr/bin/env python3
"""
Clean and format code to pass pre-commit hooks.

This script runs various code formatters and linters to ensure
all files pass pre-commit checks before committing.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], description: str) -> Tuple[int, str, str]:
    """Run a command and return the result."""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"


def find_python_files() -> List[Path]:
    """Find all Python files in the project."""
    root = Path(__file__).parent.parent
    python_files = []

    # Directories to search
    dirs_to_search = ["backend", "scripts", "tests"]

    for dir_name in dirs_to_search:
        dir_path = root / dir_name
        if dir_path.exists():
            python_files.extend(dir_path.rglob("*.py"))

    # Also check root directory Python files
    python_files.extend(root.glob("*.py"))

    return python_files


def main():
    """Main cleaning function."""
    print("🧹 Starting code cleanup process...")

    # Check if we're in a poetry environment
    in_poetry = (
        subprocess.run(["poetry", "env", "info"], capture_output=True).returncode == 0
    )

    prefix = ["poetry", "run"] if in_poetry else []

    # Track if any step fails
    has_errors = False

    # 1. Remove trailing whitespace
    print("\n📝 Removing trailing whitespace...")
    python_files = find_python_files()
    for file in python_files:
        try:
            with open(file, "r") as f:
                content = f.read()

            # Remove trailing whitespace from each line
            cleaned = "\n".join(line.rstrip() for line in content.splitlines())

            # Ensure file ends with newline
            if cleaned and not cleaned.endswith("\n"):
                cleaned += "\n"

            with open(file, "w") as f:
                f.write(cleaned)
        except Exception as e:
            print(f"  ⚠️  Error processing {file}: {e}")

    # 2. Run isort to sort imports
    returncode, stdout, stderr = run_command(
        prefix + ["isort", "--profile", "black", "backend", "scripts", "tests"],
        "Sorting imports with isort",
    )
    if returncode != 0:
        print(f"  ⚠️  isort warnings: {stderr}")
    else:
        print("  ✅ Imports sorted")

    # 3. Run black for formatting
    returncode, stdout, stderr = run_command(
        prefix + ["black", "backend", "scripts", "tests"], "Formatting code with black"
    )
    if returncode != 0:
        print(f"  ❌ Black failed: {stderr}")
        has_errors = True
    else:
        print("  ✅ Code formatted")

    # 4. Run autoflake to remove unused imports
    returncode, stdout, stderr = run_command(
        prefix
        + [
            "autoflake",
            "--in-place",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--recursive",
            "backend",
            "scripts",
            "tests",
        ],
        "Removing unused imports with autoflake",
    )
    if returncode == 127:  # Command not found
        print("  ℹ️  autoflake not installed, installing...")
        run_command(
            ["poetry", "add", "--group", "dev", "autoflake"], "Installing autoflake"
        )
        # Retry after installation
        returncode, stdout, stderr = run_command(
            prefix
            + [
                "autoflake",
                "--in-place",
                "--remove-all-unused-imports",
                "--remove-unused-variables",
                "--recursive",
                "backend",
                "scripts",
                "tests",
            ],
            "Retrying autoflake",
        )

    if returncode != 0 and returncode != 127:
        print(f"  ⚠️  autoflake warnings: {stderr}")
    else:
        print("  ✅ Unused imports removed")

    # 5. Run flake8 to check for issues
    returncode, stdout, stderr = run_command(
        prefix + ["flake8", "backend", "scripts", "tests"],
        "Checking code style with flake8",
    )
    if returncode != 0:
        print(f"  ⚠️  flake8 found issues:\n{stdout}")
        has_errors = True
    else:
        print("  ✅ Code style check passed")

    # 6. Fix common flake8 issues
    if has_errors:
        print("\n🔨 Attempting to fix common issues...")

        # Add noqa comments for specific imports that need to be kept
        files_with_model_imports = [
            Path("alembic/env.py"),
        ]

        for file in files_with_model_imports:
            if file.exists():
                try:
                    with open(file, "r") as f:
                        content = f.read()

                    # Add noqa comments to model imports if not already present
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if (
                            "from backend.models.metrics import" in line
                            and "noqa" not in line
                        ):
                            lines[i] = line.rstrip() + "  # noqa: F401"
                        elif (
                            "from backend.etl.config import settings" in line
                            and "noqa" not in line
                        ):
                            lines[i] = line.rstrip() + "  # noqa: E402"
                        elif (
                            "from backend.models.database import Base" in line
                            and "noqa" not in line
                        ):
                            lines[i] = line.rstrip() + "  # noqa: E402"

                    with open(file, "w") as f:
                        f.write("\n".join(lines) + "\n")
                except Exception as e:
                    print(f"  ⚠️  Error fixing {file}: {e}")

    # 7. Run mypy for type checking (informational only)
    print("\n📊 Running type checker (informational)...")
    returncode, stdout, stderr = run_command(
        prefix + ["mypy", "--ignore-missing-imports", "backend"],
        "Type checking with mypy",
    )
    if returncode != 0:
        print("  ℹ️  Type checking found issues (not blocking):")
        print(f"{stdout}")
    else:
        print("  ✅ Type checking passed")

    # 8. Final check with pre-commit
    print("\n🏁 Running pre-commit hooks...")
    returncode, stdout, stderr = run_command(
        prefix + ["pre-commit", "run", "--all-files"], "Final pre-commit check"
    )
    if returncode != 0:
        print(f"  ⚠️  Some pre-commit hooks failed:\n{stdout}")
        has_errors = True
    else:
        print("  ✅ All pre-commit hooks passed!")

    # Summary
    print("\n" + "=" * 50)
    if has_errors:
        print("⚠️  Some issues remain. Run 'make lint' to see details.")
        print("You may need to fix these manually before committing.")
        sys.exit(1)
    else:
        print("✅ Code is clean and ready to commit!")
        print("\nYou can now run:")
        print("  git add .")
        print("  git commit -m 'Your commit message'")
        sys.exit(0)


if __name__ == "__main__":
    main()
