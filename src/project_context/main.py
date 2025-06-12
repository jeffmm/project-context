import sys
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

from .tree import ProjectTree


def main(
    root: str | Path,
    exclude: list[str] | None = None,
    include: list[str] | None = None,
    include_always: list[str] | None = None,
    markdown: list[str] | None = None,
    output: str | Path | None = None,
    template: str | Path | None = None,
) -> None:
    """Generates a markdown file of project context to be consumed by LLMs.

    Args:
        root: The root directory to start the tree from.
        exclude: A tuple of regex patterns to exclude paths.
        include: A tuple of regex patterns to include only matching paths.
        include_always: A tuple of regex patterns to include paths regardless
            of exclusion rules.
        markdown: A tuple of regex patterns to include only matching paths for
            markdown output.
        output: An optional output file to write the tree structure. If not
            provided, the output is printed to stdout.
        template: An optional path to a Jinja template file to use for
            rendering the output. If not provided, a default template is used.
    """

    root = Path(root).resolve()
    if template:
        env = Environment(loader=FileSystemLoader(str(Path(template).parent)))
        jinja_template = env.get_template(str(template))
    else:
        # If no template is provided, use a string default template
        env = Environment()
        jinja_template = env.from_string(
            f"# {root.name}\n\n## Project structure\n\n"
            "{{ tree }}\n\n## Project contents\n\n{{ markdown }}"
        )
    tree = ProjectTree(
        root,
        exclude=exclude,
        include=include,
        include_always=include_always,
    )
    output_content = jinja_template.render(
        tree=str(tree), markdown=(tree.to_markdown(include=markdown))
    )
    if output:
        with open(output, "w") as f:
            f.write(output_content)
    else:
        sys.stdout.write(output_content)


@click.command("project-context")
@click.argument("root", type=click.Path(exists=True, file_okay=False, path_type=Path))  # type: ignore
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Regex patterns to exclude paths.",
)
@click.option(
    "--only-include",
    "-i",
    multiple=True,
    help="Regex patterns to include only matching paths.",
)
@click.option(
    "--always-include",
    "-a",
    multiple=True,
    help="Regex patterns to include paths regardless of exclusion rules.",
)
@click.option(
    "--markdown",
    "-m",
    multiple=True,
    help="Regex patterns to include only matching paths for markdown output.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),  # type: ignore
    help="Output file to write the tree structure. Defaults to stdout.",
)
@click.option(
    "--template",
    "-t",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),  # type: ignore
    help=(
        "Optional Jinja template to use for rendering the "
        "output. Uses `tree` and `markdown` as context variables."
    ),
)
def cli(
    root: Path,
    exclude: tuple[str],
    only_include: tuple[str] | None = None,
    always_include: tuple[str] | None = None,
    markdown: tuple[str] | None = None,
    output: Path | None = None,
    template: Path | None = None,
):
    """Prints a tree structure of the files in the given ROOT directory."""
    main(
        root,
        list(exclude) if exclude else None,
        list(only_include) if only_include else None,
        list(always_include) if always_include else None,
        list(markdown) if markdown else None,
        output=output,
        template=template,
    )


if __name__ == "__main__":
    cli()
