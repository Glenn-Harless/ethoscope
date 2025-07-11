#!/usr/bin/env python3
"""
Clean and format code to pass pre-commit hooks.

This script runs Ruff to format and fix code issues,
ensuring all files pass pre-commit checks before committing.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> tuple[int, str, str]:
    """Run a command and return the result."""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"


def find_python_files() -> list[Path]:
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
    print("🧹 Starting code cleanup process with Ruff...")

    # Check if we're in a poetry environment
    in_poetry = subprocess.run(["poetry", "env", "info"], capture_output=True).returncode == 0

    prefix = ["poetry", "run"] if in_poetry else []

    # Track if any step fails
    has_errors = False

    # 1. Remove trailing whitespace and ensure files end with newline
    print("\n📝 Fixing file endings...")
    python_files = find_python_files()
    for file in python_files:
        try:
            with open(file) as f:
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

    # 2. Run ruff check with auto-fix for linting issues
    returncode, stdout, stderr = run_command(
        prefix + ["ruff", "check", "--fix", "backend", "scripts", "tests", "alembic"],
        "Running Ruff linter with auto-fix",
    )
    if returncode != 0:
        print(f"  ⚠️  Ruff found issues that couldn't be auto-fixed:\n{stdout}")
        has_errors = True
    else:
        print("  ✅ Linting issues fixed")

    # 3. Run ruff format for code formatting
    returncode, stdout, stderr = run_command(
        prefix + ["ruff", "format", "backend", "scripts", "tests", "alembic"],
        "Formatting code with Ruff",
    )
    if returncode != 0:
        print(f"  ❌ Ruff format failed: {stderr}")
        has_errors = True
    else:
        print("  ✅ Code formatted")

    # 4. Check if there are any remaining issues
    returncode, stdout, stderr = run_command(
        prefix + ["ruff", "check", "backend", "scripts", "tests", "alembic"],
        "Final Ruff check",
    )
    if returncode != 0:
        print(f"  ⚠️  Remaining Ruff issues:\n{stdout}")
        has_errors = True

    # 5. Fix common import issues in special files
    print("\n🔨 Fixing special file imports...")
    files_with_model_imports = [
        Path("alembic/env.py"),
    ]

    for file in files_with_model_imports:
        if file.exists():
            try:
                with open(file) as f:
                    content = f.read()

                # Add noqa comments to model imports if not already present
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if "from backend.models.metrics import" in line and "noqa" not in line:
                        lines[i] = line.rstrip() + "  # noqa: F401"
                    elif "from backend.etl.config import settings" in line and "noqa" not in line:
                        lines[i] = line.rstrip() + "  # noqa: E402"
                    elif "from backend.models.database import Base" in line and "noqa" not in line:
                        lines[i] = line.rstrip() + "  # noqa: E402"

                with open(file, "w") as f:
                    f.write("\n".join(lines) + "\n")
            except Exception as e:
                print(f"  ⚠️  Error fixing {file}: {e}")

    # 6. Run mypy for type checking (informational only)
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

    # 7. Final check with pre-commit
    print("\n🏁 Running pre-commit hooks...")
    returncode, stdout, stderr = run_command(
        prefix + ["pre-commit", "run", "--all-files"], "Final pre-commit check"
    )
    if returncode != 0:
        print(f"  ⚠️  Some pre-commit hooks failed:\n{stdout}")
        print("\n  Attempting to auto-fix remaining issues...")
        # Run pre-commit again with auto-fix
        returncode2, stdout2, stderr2 = run_command(
            prefix + ["pre-commit", "run", "--all-files"],
            "Second pre-commit run",
        )
        if returncode2 != 0:
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
