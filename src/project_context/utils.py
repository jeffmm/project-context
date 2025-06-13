import subprocess
from pathlib import Path


def is_file_tracked(path: str | Path) -> bool:
    """Checks if a file is tracked by Git.

    Args:
        path: The path to the file.

    Returns:
        True if the file is tracked, False otherwise.
    """
    try:
        path_obj = Path(path)
        # Determine working directory more safely
        if path_obj.is_file():
            work_dir = path_obj.parent
        elif path_obj.is_dir():
            work_dir = path_obj
        else:
            # Path doesn't exist, try parent directory
            work_dir = path_obj.parent

        # Check if working directory exists
        if not work_dir.exists():
            return False

        # Check if we're in a git repository first
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False

        # Get the repo root relative to the path's directory
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=work_dir,
            text=True,
        ).strip()

        # Make path relative to its git repo root
        relative_path = Path(path).resolve().relative_to(Path(repo_root).resolve())

        # Run git ls-files to check if the file is tracked
        subprocess.check_output(
            ["git", "ls-files", "--error-unmatch", str(relative_path)],
            cwd=repo_root,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, ValueError):
        return False


def is_path_gitignored(path: str | Path) -> bool:
    """Checks if a path is ignored by .gitignore.

    Args:
        path: The path to check.

    Returns:
        True if the path is ignored, False otherwise.
    """
    try:
        # Check if we're in a git repository first
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=Path(path).parent if Path(path).is_file() else path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False

        # Get repo root relative to the path's directory
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(path).parent if Path(path).is_file() else path,
            text=True,
        ).strip()

        relative_path = Path(path).resolve().relative_to(Path(repo_root).resolve())
        result_bytes = subprocess.run(
            ["git", "check-ignore", "--quiet", str(relative_path)],
            cwd=repo_root,
            capture_output=True,
        )
        return result_bytes.returncode == 0
    except (subprocess.CalledProcessError, ValueError):
        return False
