import re
from collections import Counter
from pathlib import Path
from typing import Callable, Generator

from .utils import is_file_tracked, is_path_gitignored


class ProjectPath:
    """Represents a path in a project tree."""

    project_root: Path
    depth: int
    is_last: bool  # Used internally for representing the last item of a tree
    path_prefix = "├──"
    parent_prefix = "    "
    path_prefix_last = "└──"
    parent_prefix_last = "│   "

    def __init__(
        self,
        path: str | Path,
        parent: "ProjectPath | None" = None,
        is_last: bool = False,
    ):
        """Initializes a ProjectPath."""
        self.project_root = parent.project_root if parent else Path(path)
        self.path = Path(str(path))
        self.parent = parent
        self.is_last = is_last
        self.depth = self.parent.depth + 1 if self.parent else 0

    @classmethod
    def generate(
        cls,
        root: str | Path,
        inclusion_check: Callable[[Path], bool],
        parent: "ProjectPath | None" = None,
        is_last: bool = False,
    ) -> Generator["ProjectPath", None, None]:
        """Recursively yield paths that pass the inclusion_check."""
        current = Path(root)
        project_path = cls(current, parent, is_last)
        yield project_path

        children = sorted(
            list(path for path in current.iterdir() if inclusion_check(path))
        )
        for ix, path in enumerate(children):
            is_last = ix == len(children) - 1
            if path.is_dir():
                yield from cls.generate(
                    path,
                    inclusion_check,
                    parent=project_path,
                    is_last=is_last,
                )
            else:
                yield cls(path, project_path, is_last)

    @property
    def name(self):
        if self.path.is_dir():
            return self.path.absolute().name + "/"
        return self.path.absolute().name

    def __repr__(self):
        """Returns a string representation of the ProjectPath."""
        return f"ProjectPath(path={self.path}, parent={self.parent}, is_last={self.is_last})"

    def __str__(self):
        """Displays the project path as its component of a directory tree."""
        if self.parent is None:
            return self.name

        path_prefix = self.path_prefix_last if self.is_last else self.path_prefix

        # Build the prefixes needed to display the current path in the tree
        prefixes = [f"{path_prefix} {self.name}"]
        parent = self.parent
        while parent and parent.parent:
            prefixes.append(
                self.parent_prefix if parent.is_last else self.parent_prefix_last
            )
            parent = parent.parent

        return "".join(prefixes[::-1])

    def to_markdown(self) -> str:
        if self.path.is_dir():
            return ""
        with open(self.path, "r") as f:
            content = f.read()
        if not content:
            return ""
        return (
            f"### {self.path.relative_to(self.project_root)}\n\n```\n{content}\n```\n\n"
        )


class ProjectTree:
    """A class representing a tree structure of paths.

    Args:
        root: The root directory to start the tree from.
        exclude: A list of regex patterns to exclude paths. If provided,
            paths matched by this list are excluded unless they match a regex
            in the always_include list. By default, paths matching a
            .gitignore in the root directory or paths starting with a dot
            are always excluded unless they are in the include lists.
        include: A list of regex patterns to include paths. If provided,
            paths not in this list are excluded unless they are in the
            always_include list.
        always_include: A list of regex patterns to include paths, which takes
            precedence over other inclusion_check, allowing for exceptions to
            the exclude list.
        inclusion_check: A callable that takes a Path and returns True if the path
            should be included. If provided, all includes/excludes lists
            are ignored.
    """

    root: Path
    tree: list[ProjectPath]

    def __init__(
        self,
        root: str | Path,
        exclude: list[str] | None = None,
        include: list[str] | None = None,
        always_include: list[str] | None = None,
        inclusion_check: Callable[[Path], bool] | None = None,
    ):
        """Initialize ProjectPaths to be included in the context.

        Args:
            root: The root of the project to build the project context from.
            exclude: A list of regex patterns to exclude paths. If provided,
                paths matched by this list are excluded unless they match a regex
                in the always_include list. By default, paths matching a
                .gitignore in the root directory or paths starting with a dot
                are always excluded unless they are in the include lists.
            include: A list of regex patterns to include paths. If provided,
                paths not in this list are excluded unless they are in the
                always_include list.
            always_include: A list of regex patterns to include paths, which takes
                precedence over other inclusion_check, allowing for exceptions to
                the exclude list.
            inclusion_check: A callable that takes a Path and returns True if the path
                should be included. If provided, its logic takes precedence and
                all include/exclude lists are ignored.

        """

        inclusion_check = inclusion_check or self._default_inclusion_check(
            root, exclude, include, always_include
        )

        self.root = Path(str(root))
        self.tree = list(ProjectPath.generate(root, inclusion_check))

    def __iter__(self):
        return iter(self.tree)

    def __len__(self) -> int:
        return len(self.tree)

    def __getitem__(self, item: int) -> ProjectPath:
        return self.tree[item]

    def __repr__(self) -> str:
        return (
            f"ProjectTree(root={self.root}, tree={[repr(path) for path in self.tree]})"
        )

    def __str__(self) -> str:
        return "\n".join(str(path) for path in self.tree)

    def to_markdown(
        self,
        include: list[str] | None = None,
        inclusion_check: Callable[[Path], bool] | None = None,
    ) -> str:
        """Generates a markdown-friendly string representing the contents of the files in the tree.

        Only files that matched the original inclusion_check when the
        ProjectTree was instantiated can be included. The `include` and
        `inclusion_check` parameters will only be applied as additional
        filters.

        For safety reasons, the default behavior of this method is to only
        include the most common file type in the project based on the suffixes
        available in the tree, unless additional criteria are provided via the
        `include` or `inclusion_check` parameters.

        Args:
            include: A list of regex patterns to include paths. If provided,
                paths not in this list are excluded unless they are in the
                always_include list. By default only the files with most common
                suffix in the project will be included.
            inclusion_check: A callable that takes a Path and returns True if the path
                should be included. If provided, the include list is ignored.
        """
        if include is None:
            counter: Counter = Counter()
            for path in self.tree:
                if path.path.is_file() and path.path.suffix:
                    counter[path.path.suffix] += 1
            if counter:
                most_common_suffix, _ = counter.most_common(1)[0]
                include = [rf".*{most_common_suffix}$"]

        inclusion_check = inclusion_check or self._default_inclusion_check(
            self.root, include=include
        )

        return "".join(
            [path.to_markdown() for path in self.tree if inclusion_check(path.path)]
        )

    @classmethod
    def _default_inclusion_check(
        cls,
        root_path: str | Path,
        exclude: list[str] | None = None,
        include: list[str] | None = None,
        always_include: list[str] | None = None,
    ) -> Callable[[Path], bool]:
        """Default inclusion_check for filtering paths in the tree.

        Filters paths based on the following rules, from highest to lowest
        priority order:
            - Paths that match any pattern in `always_include` are included.
            - Paths that match any pattern in `exclude` are excluded.
            - Paths that do not match any pattern in `include` are excluded.
            - If the project is a git repository, Paths that are being tracked
              by git are included.
            - Paths that start with a dot (.) are excluded.
            - If the project is a git repository with a `.gitignore`, paths
              that would be ignored by it are excluded.

        Args:
            root_path: The root directory path to check for `.gitignore`.
            exclude: A list of regex patterns to exclude paths.
            include: A list of regex patterns to include only matching paths.
            always_include: A list of regex patterns to include paths
                regardless of exclusion rules.
        """
        is_git_repo = is_file_tracked(root_path)
        exclude = exclude or []
        always_include = always_include or []
        include = include or []

        def check_inclusion_criteria(path: Path) -> bool:
            for incl in always_include:
                if re.match(incl, path.name):
                    return True
            for excl in exclude:
                if re.match(excl, path.name):
                    return False
            if include:
                # If include is specified, we must match at least one pattern
                # to include the path.
                for incl in include:
                    if re.match(incl, path.name):
                        return True
                return False
            if is_git_repo and is_file_tracked(path):
                return True
            elif path.name.startswith("."):
                # Exclude any path starting with a dot if it's not being tracked by git
                return False
            if is_git_repo and is_path_gitignored(path):
                return False
            return True

        return check_inclusion_criteria
