import subprocess
from pathlib import Path


def get_root_paths(path: Path) -> tuple[Path | None, Path | None]:
    """Returns the root path of the Git repository and the relative path from the root.

    If the path is not in a Git repository, returns (None, None).

    Args:
        path: The path to check.

    Returns:
        A tuple containing the root path of the Git repository and the relative path from the root.
        If the path is not in a Git repository, returns (None, None).
    """
    try:
        if not path.exists():
            return None, None

        # Never use .git directory as cwd
        if path.name == ".git" and path.is_dir():
            return None, None

        # Set the current working directory to the path's parent if it's a file
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path if path.is_dir() else path.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None, None

        # Get the repo root relative to the path's directory
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path if path.is_dir() else path.parent,
            stderr=subprocess.DEVNULL,  # Suppress error output
            text=True,
        ).strip()
        return Path(repo_root).resolve(), path.resolve().relative_to(
            Path(repo_root).resolve()
        )

    except (subprocess.CalledProcessError, ValueError):
        return None, None


def is_file_tracked(path: str | Path) -> bool:
    """Checks if a file is tracked by Git.

    Args:
        path: The path to the file.

    Returns:
        True if the file is tracked, False otherwise.
    """
    try:
        path = Path(path)
        # First check whether we're in a git repository
        repo_root, relative_path = get_root_paths(path)
        if not repo_root:
            return False

        # Run git ls-files to check if the file is tracked
        subprocess.check_output(
            ["git", "ls-files", "--error-unmatch", str(relative_path)],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,  # Suppress error output
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
        path = Path(path)
        # First check whether we're in a git repository
        repo_root, relative_path = get_root_paths(path)
        if not repo_root:
            return False

        result = subprocess.run(
            ["git", "check-ignore", "--quiet", str(relative_path)],
            cwd=repo_root,
            capture_output=True,
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, ValueError):
        return False
