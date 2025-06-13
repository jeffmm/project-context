# Project Context

Generate LLM-friendly markdown from your project files.


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

Running `project-context .` would generate the following output:

````markdown
# hello-world-pkg

## Project structure

hello-world-pkg/
├── .gitignore
├── README.md
├── pyproject.toml
└── src/
    └── hello_world/
        ├── __init__.py
        └── main.py

## Project contents

### src/hello_world/main.py

```
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```


````

Explanation: By default, all files that are tracked by Git are included in the directory tree. Only the content of `src/hello_world/main.py` is included in the project contents section, since `.py` is the most common file type in this project.

### Customizing the Output

If you wanted both Python files and markdown files in the content section:

```bash
project-context . -m ".*\.py$" ".*\.md$" -o CONTEXT.md
```

This would generate the same tree structure but the contents of the README would also be included in the "Project contents" section, and additionally the output would be written to `CONTEXT.md` instead of printing to stdout.

This single markdown file now contains your entire project context in a format that's perfect for pasting into ChatGPT, Claude, or any other LLM when you need help with your code!

## Usage

### Installation

```bash
pip install project-context
```

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

### Advanced Usage Examples

**Include only Python files in the file contents:**

```bash
project-context . -m ".*\.py$" -o CONTEXT.md
```

**Exclude test directories but always include README files:**

```bash
project-context . -e "test.*" -a "README.*" -o CONTEXT.md
```

**Include only specific file types in the tree structure:**

```bash
project-context . -i ".*\.(py|md|yaml)$" -o CONTEXT.md
```

**Use a custom template:**

```bash
project-context . -t my_template.md.j2 -o CONTEXT.md
```

### Command Line Options

- `--exclude, -e`: Regex patterns to exclude paths from the tree
- `--include, -i`: Only include paths matching these regex patterns
- `--always-include, -a`: Always include these paths regardless of exclusion rules
- `--markdown, -m`: Regex patterns to include only paths matching these regex patterns in markdown contents
- `--output, -o`: Output file path (prints to stdout if not specified)
- `--template, -t`: Path to custom Jinja2 template file

### Pre-commit Hook Integration

Add this to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/your-username/project-context
    rev: main  # or specific version tag
    hooks:
      - id: project-context
        name: Generate LLM context from project contents
        args: [".", "-o", "CONTEXT.md"]  # defaults, feel free to customize filters/output here
```

**Important**: Consider adding `CONTEXT.md` to your `.gitignore` file if you don't want to track the generated context file in your repository, since it effectively duplicates your project contents.

The pre-commit hook will automatically regenerate the context file whenever you make a commit, ensuring your project context is always up-to-date for sharing with LLMs.

### Jinja2 Template Customization

For a well-documented project, the default template can work well on its own, but you can further customize the output format by providing a Jinja2 template file.

This can be useful for providing additional context or constraints that might improve the quality of AI responses.

For example, this template could add a header with some project-specific details:

```jinja2
<! -- my_template.md.j2 -->
# Your Project Name

<!-- Add a high-level overview of the project's purpose and goals -->
<!-- Add guidelines or constraints that might be useful for steering the LLM -->
<!-- e.g. "provides so-and-so service using FastAPI and pydantic" -->

## Project structure

{{ tree }}

## Project contents

{{ contents }}

```

Then simply run:

```bash
project-context . -t my_template.md.j2 -o CONTEXT.md
```

