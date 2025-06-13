import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from project_context.main import main


class TestMainFunction:
    """Test the main function and CLI functionality."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing main function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "main.py").write_text("print('hello world')")
            (temp_path / "README.md").write_text("# Test")
            yield temp_path

    def test_main_function_basic_usage(self, temp_project, capsys):
        main(temp_project)
        captured = capsys.readouterr()

        assert temp_project.name in captured.out
        assert "Project Structure" in captured.out
        assert "Project Contents" in captured.out

    def test_main_function_with_output_file(self, temp_project):
        output_file = temp_project / "output.md"
        main(temp_project, output=output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "Project Structure" in content
        assert "Project Contents" in content

    @patch("project_context.main.Path")
    def test_main_function_without_root(self, mock_path, temp_project):
        output_file = temp_project / "output.md"
        mock_path.return_value = temp_project
        main(output=output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "Project Structure" in content
        assert "Project Contents" in content

    def test_main_function_with_filters(self, temp_project, capsys):
        main(temp_project, include=[".*\\.py$"], contents=[".*\\.py$"])
        captured = capsys.readouterr()

        assert "print('hello world')" in captured.out
        assert "# Test" not in captured.out

    def test_main_function_with_custom_template(self, temp_project):
        template_path = temp_project / "template.j2"
        template_path.write_text("Custom: {{ root }}\n{{ tree }}\n{{ contents }}")

        output_file = temp_project / "output.md"
        main(temp_project, template=template_path, output=output_file)

        content = output_file.read_text()
        assert content.startswith(f"Custom: {temp_project.name}")

    def test_main_function_with_exclude_patterns(self, temp_project, capsys):
        main(temp_project, exclude=[".*\\.md$"])
        captured = capsys.readouterr()

        # Should exclude markdown files from tree
        assert "README.md" not in captured.out

    @patch("project_context.main.sys.stdout")
    def test_main_function_stdout_writing(self, mock_stdout, temp_project):
        main(temp_project, contents=[".*\\.py$"])
        mock_stdout.write.assert_called()

        # Verify the content written to stdout
        written_content = "".join(
            call.args[0] for call in mock_stdout.write.call_args_list
        )
        assert "Project Structure" in written_content
