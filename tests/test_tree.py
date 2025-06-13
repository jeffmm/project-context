import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from project_context.tree import (
    ProjectPath,
    ProjectTree,
)
from project_context.main import main


class TestProjectPath:
    """Test ProjectPath class functionality."""

    def test_project_path_initialization(self):
        path = ProjectPath("/test/path")
        assert path.path == Path("/test/path")
        assert path.parent is None
        assert path.depth == 0
        assert path.is_last is False

    def test_project_path_with_parent(self):
        parent = ProjectPath("/test")
        child = ProjectPath("/test/child", parent=parent, is_last=True)

        assert child.parent == parent
        assert child.depth == 1
        assert child.is_last is True

    def test_project_path_name_property(self):
        # Test file
        file_path = ProjectPath("/test/file.py")
        with patch.object(Path, "is_dir", return_value=False):
            assert file_path.name == "file.py"

        # Test directory
        dir_path = ProjectPath("/test/dir")
        with patch.object(Path, "is_dir", return_value=True):
            assert dir_path.name == "dir/"

    def test_project_path_str_root(self):
        path = ProjectPath("/test")
        with patch.object(Path, "is_dir", return_value=True):
            assert str(path) == "test/"

    @patch("builtins.open", new_callable=mock_open, read_data="test content")
    def test_project_path_to_markdown(self, mock_file):
        root = ProjectPath("/project")
        file_path = ProjectPath("/project/test.py", parent=root)

        with patch.object(Path, "is_dir", return_value=False):
            result = file_path.to_markdown()
            expected = "### test.py\n\n```\ntest content\n```\n\n"
            assert result == expected

    def test_project_path_to_markdown_empty_file(self):
        with patch("builtins.open", mock_open(read_data="")):
            path = ProjectPath("/test/empty.py")
            with patch.object(Path, "is_dir", return_value=False):
                assert path.to_markdown() == ""

    def test_project_path_to_markdown_directory(self):
        path = ProjectPath("/test/dir")
        with patch.object(Path, "is_dir", return_value=True):
            assert path.to_markdown() == ""


class TestProjectTree:
    """Test ProjectTree class functionality."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "file1.py").write_text("print('hello')")
            (temp_path / "file2.py").write_text("print('world')")
            (temp_path / "README.md").write_text("# Test Project")
            (temp_path / "config.yaml").write_text("key: value")

            # Create subdirectory
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "nested.py").write_text("def func(): pass")

            yield temp_path

    def test_project_tree_initialization(self, temp_project):
        def mock_inclusion_check(path):
            return path.suffix in [".py", ".md"]

        tree = ProjectTree(temp_project, inclusion_check=mock_inclusion_check)
        assert tree.root == temp_project
        assert len(tree.tree) > 0

    def test_project_tree_exclude_patterns(self, temp_project):
        tree = ProjectTree(temp_project, exclude=[".*\\.yaml$"])
        # Should exclude .yaml files
        yaml_files = [path for path in tree if path.path.suffix == ".yaml"]
        assert len(yaml_files) == 0

    def test_project_tree_include_patterns(self, temp_project):
        tree = ProjectTree(temp_project, include=[".*\\.py$"])
        # Should only include .py files
        for path in tree:
            if path.path.is_file():
                assert path.path.suffix == ".py"

    def test_project_tree_always_include_patterns(self, temp_project):
        tree = ProjectTree(
            temp_project, exclude=[".*\\.md$"], always_include=["README\\.md$"]
        )
        # Should exclude .md files except README.md
        readme_files = [path for path in tree if path.path.name == "README.md"]
        assert len(readme_files) > 0

    def test_project_tree_str_representation(self, temp_project):
        tree = ProjectTree(temp_project, include=[".*\\.py$"])
        result = str(tree)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_project_tree_to_markdown_most_common_suffix(self, temp_project):
        tree = ProjectTree(temp_project, include=[".*\\.(py|md)$"])
        markdown = tree.to_markdown()

        # Should automatically include .py files (most common)
        assert "```" in markdown
        assert "print(" in markdown

    def test_project_tree_to_markdown_with_include_filter(self, temp_project):
        tree = ProjectTree(temp_project, include=[".*\\.(py|md)$"])
        markdown = tree.to_markdown(include=[".*\\.md$"])

        # Should only include .md files
        assert "# Test Project" in markdown
        assert "print(" not in markdown

    def test_project_tree_iteration(self, temp_project):
        tree = ProjectTree(temp_project, include=[".*\\.py$"])
        paths = list(tree)
        assert len(paths) > 0
        assert all(isinstance(path, ProjectPath) for path in paths)

    def test_project_tree_indexing(self, temp_project):
        tree = ProjectTree(temp_project, include=[".*\\.py$"])
        if len(tree) > 0:
            first_path = tree[0]
            assert isinstance(first_path, ProjectPath)


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
