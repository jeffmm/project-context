import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from project_context.utils import (
    is_file_tracked,
    is_path_gitignored,
)


class TestGitUtilities:
    """Test Git-related utility functions."""

    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.subprocess.check_output")
    def test_is_file_tracked_returns_true_for_tracked_file(
        self, mock_check_output, mock_run
    ):
        # Mock the git rev-parse --git-dir call
        mock_run.return_value = MagicMock(returncode=0)

        mock_check_output.side_effect = [
            "/repo/root\n",  # git rev-parse --show-toplevel
            "file.py\n",  # git ls-files --error-unmatch
        ]

        with patch("project_context.utils.Path") as mock_path_class:
            # Create mock path objects
            mock_file_path = MagicMock()
            mock_file_path.is_file.return_value = True
            mock_file_path.is_dir.return_value = False

            # Create mock parent directory
            mock_parent_dir = MagicMock()
            mock_parent_dir.exists.return_value = True
            mock_file_path.parent = mock_parent_dir

            # Create mock resolved paths for relative_to calculation
            mock_resolved_file = MagicMock()
            mock_resolved_repo = MagicMock()
            mock_resolved_file.relative_to.return_value = Path("file.py")

            # Configure Path class mock to return appropriate objects
            def path_side_effect(path_str):
                if path_str == "/repo/root/file.py":
                    return mock_file_path
                elif path_str == "/repo/root":
                    mock_repo_path = MagicMock()
                    mock_repo_path.resolve.return_value = mock_resolved_repo
                    return mock_repo_path
                else:
                    # For any other Path creation, return a basic mock
                    mock_other = MagicMock()
                    mock_other.resolve.return_value = mock_resolved_file
                    return mock_other

            mock_path_class.side_effect = path_side_effect

            result = is_file_tracked("/repo/root/file.py")
            assert result is True

    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.subprocess.check_output")
    def test_is_file_tracked_returns_false_for_untracked_file(
        self, mock_check_output, mock_run
    ):
        # Mock the git rev-parse --git-dir call
        mock_run.return_value = MagicMock(returncode=0)

        mock_check_output.side_effect = [
            "/repo/root\n",  # git rev-parse --show-toplevel
            subprocess.CalledProcessError(1, "git ls-files"),  # git ls-files fails
        ]

        with patch("project_context.utils.Path") as mock_path:
            # Mock Path behavior
            mock_path_obj = MagicMock()
            mock_path_obj.is_file.return_value = True
            mock_path_obj.parent = Path("/repo/root")
            mock_path.return_value = mock_path_obj

            result = is_file_tracked("/repo/root/untracked.py")
            assert result is False

    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.subprocess.check_output")
    def test_is_file_tracked_returns_false_for_fake_file(
        self, mock_check_output, mock_run
    ):
        # Mock the git rev-parse --git-dir call
        mock_run.return_value = MagicMock(returncode=0)

        mock_check_output.side_effect = [
            "/repo/root\n",  # git rev-parse --show-toplevel
            subprocess.CalledProcessError(1, "git ls-files"),  # git ls-files fails
        ]
        result = is_file_tracked("/repo/root/untracked.py")
        assert result is False

    @patch("project_context.utils.subprocess.run")
    def test_is_file_tracked_handles_git_error(self, mock_run):
        # Mock the git rev-parse --git-dir call to fail (not in git repo)
        mock_run.return_value = MagicMock(returncode=1)

        result = is_file_tracked("/not/a/git/repo/file.py")
        assert result is False

    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.subprocess.check_output")
    def test_is_path_gitignored_returns_true_for_ignored_path(
        self, mock_check_output, mock_run_main
    ):
        # Mock the git rev-parse --git-dir call
        mock_run_main.return_value = MagicMock(returncode=0)

        mock_check_output.return_value = "/repo/root\n"

        # Mock the git check-ignore call
        with patch("project_context.utils.subprocess.run") as mock_run_check:
            with patch("project_context.utils.Path") as mock_path:
                # Mock Path behavior
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = True
                mock_path_obj.is_dir.return_value = False
                mock_path.return_value = mock_path_obj
                mock_run_check.return_value = MagicMock(returncode=0)
                result = is_path_gitignored("/repo/root/.env")
                assert result is True

    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.subprocess.check_output")
    def test_is_path_gitignored_returns_false_for_tracked_path(
        self, mock_check_output, mock_run_main
    ):
        # Mock the git rev-parse --git-dir call
        mock_run_main.return_value = MagicMock(returncode=0)

        mock_check_output.return_value = "/repo/root\n"

        # Mock the git check-ignore call to fail (file not ignored)
        with patch("project_context.utils.subprocess.run") as mock_run_check:
            mock_run_check.return_value = MagicMock(returncode=1)
            result = is_path_gitignored("/repo/root/file.py")
            assert result is False

    @patch("project_context.utils.subprocess.run")
    @patch("project_context.utils.subprocess.check_output")
    def test_is_path_gitignored_returns_true_for_fake_path(
        self, mock_check_output, mock_run_main
    ):
        # Mock the git rev-parse --git-dir call
        mock_run_main.return_value = MagicMock(returncode=0)

        mock_check_output.return_value = "/repo/root\n"

        # Mock the git check-ignore call
        with patch("project_context.utils.subprocess.run") as mock_run_check:
            mock_run_check.return_value = MagicMock(returncode=0)
            result = is_path_gitignored("/repo/root/.env")
            assert result is False
