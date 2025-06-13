import sys
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

from .tree import ProjectTree


def main(
    root: str | Path,
    exclude: list[str] | None = None,
    include: list[str] | None = None,
    always_include: list[str] | None = None,
    contents: list[str] | None = None,
    output: str | Path | None = None,
    template: str | Path | None = None,
) -> None:
    """Generates a markdown file of project context to be consumed by LLMs.
    Args:
        root: The root directory to start the tree from.
        exclude: A tuple of regex patterns to exclude paths.
        include: A tuple of regex patterns to include only matching paths.
        always_include: A tuple of regex patterns to include paths regardless
            of exclusion rules.
        contents: A tuple of regex patterns to include only matching paths for
            project content output.
        output: An optional output file to write the tree structure. If not
            provided, the output is printed to stdout.
        template: An optional path to a Jinja template file to use for
            rendering the output. If not provided, a default template is used.
    """

    root = Path(root).resolve()
    if template:
        template_path = Path(template)
        env = Environment(loader=FileSystemLoader(str(template_path.parent)))
        jinja_template = env.get_template(
            template_path.name
        )  # Use .name instead of str(template)
    else:
        # If no template is provided, use a string default template
        env = Environment()
        jinja_template = env.from_string(
            "# {{ root }}\n\n"
            "## Project Structure\n\n{{ tree }}\n\n"
            "## Project Contents\n\n{{ contents }}"
        )

    tree = ProjectTree(
        root,
        exclude=exclude,
        include=include,
        always_include=always_include,
    )
    output_content = jinja_template.render(
        root=root.name, tree=str(tree), contents=(tree.to_markdown(include=contents))
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
    "--include",
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
    "--contents",
    "-c",
    multiple=True,
    help="Regex patterns to include only matching paths for content output.",
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
        "output. Uses `tree` and `contents` as context variables."
    ),
)
def cli(
    root: Path,
    exclude: tuple[str],
    include: tuple[str] | None = None,
    always_include: tuple[str] | None = None,
    contents: tuple[str] | None = None,
    output: Path | None = None,
    template: Path | None = None,
):
    """Prints a tree structure of the files in the given ROOT directory."""
    main(
        root,
        list(exclude) if exclude else None,
        list(include) if include else None,
        list(always_include) if always_include else None,
        list(contents) if contents else None,
        output=output,
        template=template,
    )


if __name__ == "__main__":
    cli()
