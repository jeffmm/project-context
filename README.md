# Project Context

Generate LLM-friendly markdown from your project files.

[![CI/CD](https://github.com/your-username/project-context/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/project-context/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-username/project-context/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/project-context)
[![PyPI version](https://badge.fury.io/py/project-context.svg)](https://badge.fury.io/py/project-context)
[![Python versions](https://img.shields.io/pypi/pyversions/project-context.svg)](https://pypi.org/project/project-context/)

## Project Context Generator

`project-context` is a Python tool that generates LLM-friendly markdown documentation of your entire project structure and contents. It creates a single markdown file containing both a visual tree representation of your project and the actual content of your source files, making it easy to share your codebase context with AI assistants.

### Key Features

- **Intelligent file filtering**: Automatically respects `.gitignore` files and Git tracking status
- **Flexible inclusion/exclusion**: Use regex patterns to precisely control which files are included or excluded
- **Customizable output**: Support for custom Jinja2 templates to format the output
- **Smart content selection**: Automatically includes the most common file type in your project for markdown output
- **Pre-commit integration**: Can automatically generate context files on every commit

### Example

Let's say you have a basic Python package with this structure:

```
hello-world-pkg/
├── .gitignore
├── README.md
├── pyproject.toml
└── src/
    └── hello_world/
        ├── __init__.py
        └── main.py
```

Where `src/hello_world/main.py` contains:

```python
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

Running `project-context .` in the project root would generate the following output to stdout:

````markdown
# hello-world-pkg

## Project Structure

hello-world-pkg/
├── .gitignore
├── README.md
├── pyproject.toml
└── src/
    └── hello_world/
        ├── __init__.py
        └── main.py

## Project Contents

### src/hello_world/main.py

```
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```
````

This single markdown file now contains your entire project context in a format that's perfect for pasting into ChatGPT, Claude, Gemini, or any other LLM when you need help with your code!

## Usage

### Installation

#### Using `uv` (recommended)

```bash
uv tool install project-context
```

Evoke using `uvx project-context`

#### Using `pip`

```bash
pip install project-context
```

Evoke using `project-context`

### Basic Usage

By default, all files tracked by Git are included in the directory tree.

Generate context for the current directory and write it to stdout:

```bash
project-context .
```

Save output to a file:

```bash
project-context . -o CONTEXT.md
```

### Customizing the Output

By default, all files that are tracked by Git are included in the directory tree in the `Project structure` section, and only the _most common file type_ is included as part of the `Project contents` section. In the above example, the only file included was `src/hello_world/main.py` since `.py` is the most common file type in this project (`__init__.py` was excluded since it was empty).

#### Command Line Options

| Flag | Description | Example |
|------|-------------|---------|
| `--exclude, -e` | Regex patterns to exclude paths from the tree | `-e 'test.*'` |
| `--include, -i` | Only include paths matching these regex patterns | `-i '.*\.py$' -i '.*\.y[a]?ml$` |
| `--always-include, -a` | Always include these paths regardless of exclusion rules | `-a 'README.*'` |
| `--contents, -c` | Regex patterns to include paths matching these patterns in contents section | `-c '.*\.py$' -c '^README\.*'` |
| `--output, -o` | Output file path (prints to stdout if not specified) | `-o CONTEXT.md` |
| `--template, -t` | Path to custom Jinja2 template file | `-t my_template.md.j2` |


**Important:** Be careful to escape your regex args properly. Notice the use of single quotes around regex patterns to avoid issues due to shell expansion.

All regex flags can be specified multiple times to include/exclude multiple patterns, and combined as needed.

For any file in the root directory, the inclusion/exclusion rules are applied in the following order:

#### Project Structure ("tree") Inclusion/Exclusion Rules

- **IF** the path matches any pattern in **always-include**, **THEN** it is included in the tree
- **ELSE IF** the path matches any pattern in **exclude**, **THEN** it is excluded from the tree
- **ELSE IF** there are **include** patterns **THEN**
    -  **IF** the path matches any pattern in **include**, **THEN** it is included in the tree
    -  **ELSE** it is excluded from the tree
- **ELSE IF** the path is a file tracked by Git, **THEN** it is included in the tree
- **ELSE IF** the path is a file that is ignored using a `.gitignore`, **THEN** it is excluded from the tree
- **ELSE IF** the path is a dot-file (ie its name starts with a `.`), **THEN** it is excluded from the tree
- **ELSE** the path is included in the tree

#### Project Contents Inclusion/Exclusion Rules

- **IF** the path is included in the tree, **THEN**
    - **IF** there are **contents** patterns, **THEN**
        - **IF** the path matches any patterns in **contents**, **THEN** its contents are included in the contents section
        - **ELSE** the path's contents are excluded from the contents section
    - **ELSE IF** the path suffix is the most common file type in the project, **THEN** its contents are included in the contents section
    - **ELSE** the path's contents are excluded from the contents section
- **ELSE** the path's contents are excluded from the contents section

### Advanced Usage Examples

**Write the context to a custom dot-file:**

```bash
project-context . -o .context.md
```

**Include Python files, YAML files, and markdown files in the content section:**

```bash

project-context . -c '.*\.(py|md|yaml)$'
```

**Exclude multiple patterns from the project context:**

```bash
project-context . -e '^\..*' -e '.*\.yaml$'
```

**Exclude all YAML files, except for your `.pre-commit-config.yaml`:**

```bash
project-context . -e '.*\.yaml$' -a '\.pre-commit-config\.yaml'
```

**Only include typescript files and README files:**

```bash
project-context . -i '.*\.ts$' -a 'README.*'
```

**Generate the output using a custom template and write to file:**

```bash
project-context . -t custom_template.md.j2 -o CONTEXT.md
```

### Pre-commit Hook Integration

For automated context generation on each commit, add this to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/your-username/project-context
    rev: main  # or specific version tag
    hooks:
      - id: project-context
        name: Generate LLM context from project contents
        args: ['.', '-o', 'CONTEXT.md']  # defaults, feel free to customize filters/output here
```

**Important**:
2. Consider adding `CONTEXT.md` to your `.gitignore` file if you don't want to track the generated context file in your repository, since it effectively duplicates your project contents.

The pre-commit hook will automatically regenerate the context file whenever you make a commit, ensuring your project context is always up-to-date for sharing with LLMs.

### Jinja2 Template Customization

The default output template is:

```jinja2
# {{ root }}

## Project Structure

{{ tree }}

## Project Contents

{{ contents }}
```

For a well-documented project, the default can work well enough on its own, but you can further customize the output format by providing your own Jinja2 template file. This can be useful for providing additional context or constraints that might improve the quality of AI responses.

`project-context` defines three variables for rendering the output: `root`, `tree`, and `contents`.

For example, using a template like this would add a header to the context with some project-specific details that can help steer the LLM to produce output that's more aligned to your project's needs:

```jinja2
{# custom_template.md.j2 #}
# {{ root }}

## Project Description

### High-level Overview:
Here is a brief description of the project and its purpose...

### Project Roadmap
Here is the planned roadmap for the project...

### Developer Guidelines
Here are some guidelines and constraints on how the project should be maintained...

## Project Structure

{{ tree }}

## Project Contents

{{ contents }}

```

Then you can generate the context using your custom template like this:

```bash
project-context . -t custom_template.md.j2 -o CONTEXT.md
```
