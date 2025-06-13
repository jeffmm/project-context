import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from project_context.utils import (
    get_root_paths,
    is_file_tracked,
    is_path_gitignored,
)


@pytest.fixture
def git_repo(tmp_path):
    """Create a git repository with tracked, untracked, and ignored files."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )

    # Create and track a file
    tracked_file = tmp_path / "tracked.py"
    tracked_file.write_text("# tracked file")
    subprocess.run(["git", "add", "tracked.py"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create .gitignore first
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\nignored.py\n")

    # Create a subdirectory with tracked files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    tracked_sub = subdir / "tracked_sub.py"
    tracked_sub.write_text("# tracked in subdir")

    # Add gitignore and subdir files
    subprocess.run(["git", "add", ".gitignore", "subdir/"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "add more files"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create untracked and ignored files AFTER commits
    untracked_file = tmp_path / "untracked.py"
    untracked_file.write_text("# untracked file")

    ignored_file = tmp_path / "ignored.py"
    ignored_file.write_text("# ignored file")

    return tmp_path


class TestGitUtilities:
    """Test Git-related utility functions."""

    def test_get_root_paths_returns_none_specifically_for_git_directory(self, git_repo):
        """Test that get_root_paths returns (None, None) specifically because path is .git directory."""
        # Test with the .git directory - should return (None, None)
        git_dir = git_repo / ".git"
        result_git = get_root_paths(git_dir)
        assert result_git == (None, None)

        # Test with a regular directory in the same repo - should succeed
        regular_dir = git_repo / "subdir"
        result_regular = get_root_paths(regular_dir)
        assert result_regular != (None, None)
        assert result_regular[0] == git_repo

    def test_get_root_paths_with_nonexistent_path(self, tmp_path):
        """Test get_root_paths with non-existent path."""
        nonexistent = tmp_path / "does_not_exist"
        result = get_root_paths(nonexistent)
        assert result == (None, None)

    def test_get_root_paths_outside_git_repo(self, tmp_path):
        """Test get_root_paths outside a git repository."""
        regular_dir = tmp_path / "not_git"
        regular_dir.mkdir()
        result = get_root_paths(regular_dir)
        assert result == (None, None)

    def test_is_file_tracked_with_tracked_file(self, git_repo):
        """Test is_file_tracked returns True for tracked files."""
        tracked_file = git_repo / "tracked.py"
        assert is_file_tracked(tracked_file) is True

        # Test with file in subdirectory
        tracked_sub = git_repo / "subdir" / "tracked_sub.py"
        assert is_file_tracked(tracked_sub) is True

    def test_is_file_tracked_with_untracked_file(self, git_repo):
        """Test is_file_tracked returns False for untracked files."""
        untracked_file = git_repo / "untracked.py"
        assert is_file_tracked(untracked_file) is False

    def test_is_file_tracked_outside_git_repo(self, tmp_path):
        """Test is_file_tracked returns False outside git repository."""
        regular_file = tmp_path / "file.py"
        regular_file.write_text("content")
        assert is_file_tracked(regular_file) is False

    def test_is_path_gitignored_with_ignored_file(self, git_repo):
        """Test is_path_gitignored returns True for ignored files."""
        ignored_file = git_repo / "ignored.py"
        assert is_path_gitignored(ignored_file) is True

        # Test with pattern match
        log_file = git_repo / "debug.log"
        log_file.write_text("log content")
        assert is_path_gitignored(log_file) is True

    def test_is_path_gitignored_with_tracked_file(self, git_repo):
        """Test is_path_gitignored returns False for tracked files."""
        tracked_file = git_repo / "tracked.py"
        assert is_path_gitignored(tracked_file) is False

    def test_is_path_gitignored_outside_git_repo(self, tmp_path):
        """Test is_path_gitignored returns False outside git repository."""
        regular_file = tmp_path / "file.py"
        regular_file.write_text("content")
        assert is_path_gitignored(regular_file) is False

    @patch("project_context.utils.subprocess.check_output")
    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.Path")
    def test_get_root_paths_handles_subprocess_error(
        self, mock_path_class, mock_run, mock_check_output
    ):
        """Test get_root_paths returns (None, None) when subprocess.CalledProcessError is raised."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.name = "regular_dir"
        mock_path.is_dir.return_value = True
        mock_path_class.return_value = mock_path

        # First subprocess call succeeds, second fails
        mock_run.return_value = MagicMock(returncode=0)
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")

        result = get_root_paths("/some/path")
        assert result == (None, None)

    @patch("project_context.utils.subprocess.check_output")
    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.Path")
    def test_get_root_paths_handles_value_error(
        self, mock_path_class, mock_run, mock_check_output
    ):
        """Test get_root_paths returns (None, None) when ValueError is raised."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.name = "regular_dir"
        mock_path.is_dir.return_value = True
        mock_path_class.return_value = mock_path

        mock_run.return_value = MagicMock(returncode=0)
        mock_check_output.return_value = "/repo/root\n"

        # Make relative_to raise ValueError
        mock_path.relative_to.side_effect = ValueError("Not a relative path")

        result = get_root_paths("/some/path")
        assert result == (None, None)

    @patch("project_context.utils.get_root_paths")
    @patch("project_context.utils.subprocess.check_output")
    @patch("project_context.utils.Path")
    def test_is_file_tracked_handles_value_error(
        self, mock_path_class, mock_check_output, mock_get_root_paths
    ):
        """Test is_file_tracked returns False when ValueError is raised."""
        mock_path = MagicMock()
        mock_path_class.return_value = mock_path

        # get_root_paths succeeds
        mock_get_root_paths.return_value = (Path("/repo"), Path("file.py"))

        # But subprocess.check_output raises ValueError
        mock_check_output.side_effect = ValueError("Invalid path")

        result = is_file_tracked("/repo/file.py")
        assert result is False

    @patch("project_context.utils.get_root_paths")
    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.Path")
    def test_is_path_gitignored_handles_subprocess_error(
        self, mock_path_class, mock_run, mock_get_root_paths
    ):
        """Test is_path_gitignored returns False when subprocess.CalledProcessError is raised."""
        mock_path = MagicMock()
        mock_path_class.return_value = mock_path

        # get_root_paths succeeds
        mock_get_root_paths.return_value = (Path("/repo"), Path("file.py"))

        # But subprocess.run raises CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = is_path_gitignored("/repo/file.py")
        assert result is False

    @patch("project_context.utils.get_root_paths")
    @patch("project_context.utils.Path")
    def test_is_path_gitignored_handles_value_error(
        self, mock_path_class, mock_get_root_paths
    ):
        """Test is_path_gitignored returns False when ValueError is raised."""
        mock_path = MagicMock()
        mock_path_class.return_value = mock_path

        # get_root_paths raises ValueError
        mock_get_root_paths.side_effect = ValueError("Invalid path operation")

        result = is_path_gitignored("/repo/file.py")
        assert result is False
