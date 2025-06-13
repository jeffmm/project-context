import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from project_context.tree import (
    ProjectPath,
    ProjectTree,
)


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

    def test_project_path_str_nested_structure(self):
        """Test string representation with multiple levels of nesting."""
        # Create a 3-level nested structure: root -> parent -> child
        root = ProjectPath("/project")
        parent = ProjectPath("/project/parent", parent=root, is_last=False)
        child = ProjectPath("/project/parent/child.py", parent=parent, is_last=True)

        with patch.object(Path, "is_dir", return_value=False):
            result = str(child)
            # Should contain the nested prefix structure
            assert "└── child.py" in result
            assert "│   " in result  # parent_prefix_last from the parent level

    def test_project_path_str_multiple_children(self):
        """Test string representation with multiple children at different levels."""
        root = ProjectPath("/project")
        parent1 = ProjectPath("/project/dir1", parent=root, is_last=False)
        child = ProjectPath("/project/dir1/file.py", parent=parent1, is_last=True)

        with patch.object(Path, "is_dir", return_value=False):
            result = str(child)
            # Should use parent_prefix (4 spaces) since parent1 is not last
            assert "│   └── file.py" in result

    @patch("project_context.tree.is_file_tracked")
    @patch("project_context.tree.is_path_gitignored")
    def test_default_inclusion_check_git_tracked_file(
        self, mock_gitignored, mock_tracked, temp_project
    ):
        """Test that git-tracked files are included when in a git repo."""
        # Mock git repo detection and file tracking
        mock_tracked.side_effect = (
            lambda path: str(path).endswith("tracked.py")
            if hasattr(path, "endswith")
            else True
        )
        mock_gitignored.return_value = False

        inclusion_check = ProjectTree._default_inclusion_check(temp_project)

        test_path = temp_project / "tracked.py"
        test_path.touch()

        # Should include git-tracked files
        assert inclusion_check(test_path) is True

    @patch("project_context.tree.is_file_tracked")
    @patch("project_context.tree.is_path_gitignored")
    def test_default_inclusion_check_dotfile_exclusion(
        self, mock_gitignored, mock_tracked, temp_project
    ):
        """Test that dotfiles are excluded when not git-tracked."""
        # Mock git repo but file is not tracked
        mock_tracked.side_effect = (
            lambda path: False if str(path).endswith(".hidden") else True
        )
        mock_gitignored.return_value = False

        inclusion_check = ProjectTree._default_inclusion_check(temp_project)

        # Test dotfile exclusion
        dotfile_path = temp_project / ".hidden"
        dotfile_path.touch()

        # Should exclude dotfiles that aren't git-tracked
        assert inclusion_check(dotfile_path) is False

    @patch("project_context.tree.is_file_tracked")
    @patch("project_context.tree.is_path_gitignored")
    def test_default_inclusion_check_gitignored_exclusion(
        self, mock_gitignored, mock_tracked, temp_project
    ):
        """Test that gitignored files are excluded."""

        # Mock git repo detection - root is a git repo, but ignored.py is not tracked
        def mock_tracked_side_effect(path):
            if str(path) == str(temp_project):
                return True  # Root is git repo
            elif str(path).endswith("ignored.py"):
                return False  # ignored.py is not tracked
            else:
                return True  # Other files are tracked

        mock_tracked.side_effect = mock_tracked_side_effect
        mock_gitignored.side_effect = lambda path: str(path).endswith("ignored.py")

        inclusion_check = ProjectTree._default_inclusion_check(temp_project)

        ignored_path = temp_project / "ignored.py"
        ignored_path.touch()

        # Should exclude gitignored files
        assert inclusion_check(ignored_path) is False
