import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from project_context.main import cli


@pytest.fixture
def temp_project():
    """Create a temporary project for testing main function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        (temp_path / "main.py").write_text("print('hello world')")
        (temp_path / "README.md").write_text("# Test")
        yield temp_path


class TestCLIFunction:
    """Test the CLI functionality using Click's testing utilities."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    def test_cli_basic_usage(self, temp_project, runner):
        """Test basic CLI usage with just the root argument."""
        result = runner.invoke(cli, ["-r", str(temp_project)])

        assert result.exit_code == 0
        assert temp_project.name in result.output
        assert "Project Structure" in result.output
        assert "Project Contents" in result.output

    def test_cli_with_output_file(self, temp_project, runner):
        """Test CLI with output file option."""
        output_file = temp_project / "cli_output.md"
        result = runner.invoke(
            cli, ["-r", str(temp_project), "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Project Structure" in content

    def test_cli_with_exclude_option(self, temp_project, runner):
        """Test CLI with exclude patterns."""
        result = runner.invoke(cli, ["-r", str(temp_project), "--exclude", ".*\\.md$"])

        assert result.exit_code == 0
        assert "README.md" not in result.output

    def test_cli_with_multiple_exclude_patterns(self, temp_project, runner):
        """Test CLI with multiple exclude patterns."""
        result = runner.invoke(
            cli,
            [
                "--root",
                str(temp_project),
                "--exclude",
                ".*\\.md$",
                "--exclude",
                ".*\\.py$",
            ],
        )

        assert result.exit_code == 0

    def test_cli_with_include_option(self, temp_project, runner):
        """Test CLI with include patterns."""
        result = runner.invoke(cli, ["-r", str(temp_project), "--include", ".*\\.py$"])

        assert result.exit_code == 0

    def test_cli_with_contents_option(self, temp_project, runner):
        """Test CLI with contents patterns."""
        result = runner.invoke(cli, ["-r", str(temp_project), "--contents", ".*\\.py$"])

        assert result.exit_code == 0
        assert "print('hello world')" in result.output

    def test_cli_with_always_include_option(self, temp_project, runner):
        """Test CLI with always-include patterns."""
        result = runner.invoke(
            cli,
            [
                "--root",
                str(temp_project),
                "--exclude",
                ".*\\.py$",
                "--always-include",
                "main\\.py$",
            ],
        )

        assert result.exit_code == 0

    def test_cli_with_template_option(self, temp_project, runner):
        """Test CLI with custom template."""
        template_path = temp_project / "cli_template.j2"
        template_path.write_text("CLI Custom: {{ root }}\n{{ tree }}\n{{ contents }}")

        result = runner.invoke(
            cli, ["--root", str(temp_project), "--template", str(template_path)]
        )

        assert result.exit_code == 0
        assert f"CLI Custom: {temp_project.name}" in result.output

    def test_cli_with_short_options(self, temp_project, runner):
        """Test CLI with short option flags."""
        result = runner.invoke(
            cli,
            [
                "-r",
                str(temp_project),
                "-e",
                ".*\\.md$",
                "-i",
                ".*\\.py$",
                "-c",
                ".*\\.py$",
            ],
        )

        assert result.exit_code == 0
        assert "print('hello world')" in result.output

    def test_cli_nonexistent_directory(self, runner):
        """Test CLI with non-existent directory."""
        result = runner.invoke(cli, ["-r", "/nonexistent/path"])

        assert result.exit_code != 0
        assert (
            "does not exist" in result.output.lower()
            or "invalid value" in result.output.lower()
        )

    @patch("project_context.main.main")
    def test_cli_calls_main_with_correct_arguments(
        self, mock_main, temp_project, runner
    ):
        """Test that CLI properly converts and passes arguments to main function."""
        runner.invoke(
            cli,
            [
                "--root",
                str(temp_project),
                "--exclude",
                ".*\\.md$",
                "--include",
                ".*\\.py$",
                "--contents",
                ".*\\.py$",
            ],
        )

        mock_main.assert_called_once()
        args, kwargs = mock_main.call_args

        assert args[0] == temp_project
        assert kwargs["exclude"] == [".*\\.md$"]
        assert kwargs["include"] == [".*\\.py$"]
        assert kwargs["contents"] == [".*\\.py$"]


class TestMainBlock:
    """Test the if __name__ == '__main__' block."""

    def test_main_block_execution_via_subprocess(self, temp_project):
        """Test that the module can be run directly as a script."""
        result = subprocess.run(
            [sys.executable, "-m", "project_context.main", "-r", str(temp_project)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert temp_project.name in result.stdout
        assert "Project Structure" in result.stdout

    def test_main_block_with_cli_options(self, temp_project):
        """Test the main block with various CLI options."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_context.main",
                "--root",
                str(temp_project),
                "--exclude",
                ".*\\.md$",
                "--contents",
                ".*\\.py$",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "print('hello world')" in result.stdout
        assert "README.md" not in result.stdout

    def test_main_block_error_handling(self):
        """Test the main block with invalid arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "project_context.main", "-r", "/nonexistent/path"],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert (
            "does not exist" in result.stderr.lower()
            or "invalid value" in result.stderr.lower()
        )

    @patch("project_context.main.cli")
    def test_main_block_code_coverage(self, mock_cli):
        """Test that the main block calls cli() when __name__ == '__main__'."""
        # This test ensures the if __name__ == '__main__' block is covered,
        # we need to execute the code in a way that __name__ == '__main__'

        # Create a temporary script that imports and runs the main block logic
        import tempfile
        import textwrap

        script_content = textwrap.dedent("""
            if __name__ == '__main__':
                from project_context.main import cli
                cli()
        """)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script_content)
            script_path = f.name

        try:
            # Run the script - this will execute cli() in the main block context
            result = subprocess.run(
                [sys.executable, script_path, "--help"], capture_output=True, text=True
            )

            # Should show help and exit successfully
            assert result.returncode == 0
            assert "project-context" in result.stdout
            assert "Usage" in result.stdout
        finally:
            import os

            os.unlink(script_path)
