# Coding Standards and Conventions for COSMOS

## Overview
To maintain high-quality code and ensure consistency across the entire COSMOS project, we have established coding standards and conventions. This document outlines the key standards and practices that all contributors are expected to follow. Adhering to these guidelines helps us to achieve a codebase that appears as if it were written by a single entity, regardless of the number of contributors.

## Coding Standards

### Formatting Standards
- **Line Length**: Maximum of 120 characters per line to ensure readability across various environments.
- **Code Formatting**: Utilize tools like Black for Python code to ensure consistent formatting across the entire codebase.
- **Import Ordering**: Follow a consistent import order:
  - Standard library imports.
  - Third-party imports.
  - Application-specific imports.

### Naming Conventions
- **Variables and Functions**: Use `snake_case`.
- **Classes and Exceptions**: Use `CamelCase`.
- **Constants**: Use `UPPER_CASE`.

### Commenting
- Inline comments should be used sparingly and only when necessary to explain "why" something is done, not "what" is done.
- All public methods, classes, and modules should include docstrings that follow the [Google style guide](https://google.github.io/styleguide/pyguide.html).

### Error Handling
- Explicit is better than implicit. Raise exceptions rather than returning None or any error codes.
- Use custom exceptions over generic exceptions when possible to make error handling more predictive.

## Tool Configurations and Pre-commit Hooks

To automate and enforce these standards, the following tools are configured with pre-commit hooks in our development process:

### Pre-commit Hooks Setup

To ensure that these tools are run automatically on every commit, contributors must set up pre-commit hooks locally. Run the following commands to install and configure pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

The following pre-commit hooks are configured:

- trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict, debug-statements: Checks for common formatting issues.
- pyupgrade: Automatically upgrades syntax for newer versions of the language.
- black: Formats Python code to ensure consistent styling.
- isort: Sorts imports alphabetically and automatically separated into sections.
- flake8: Lints code to catch styling errors and potential bugs.
- mypy: Checks type annotations to catch potential bugs.
- bandit: Scans code for common security issues.
- gitleaks: Prevents secrets from being committed to the repository.
- hadolint: Lints Dockerfiles to ensure best practices and common conventions are followed.

## Continuous Integration (CI)
When a commit is pushed to a branch that is part of a Pull Request, our Continuous Integration (CI) pipeline automatically runs specified tools to check code quality, style, security and other standards. If these checks fail, the PR cannot be merged until all issues are resolved.

## Quality Standards Enforcement
- PRs must pass all checks from the configured pre-commit hooks and CI pipeline to be eligible for merging.
- Code reviews additionally focus on logical errors and code quality beyond what automated tools can detect.

## Conclusion
By adhering to these standards and utilizing the tools set up, we maintain the high quality and consistency of our codebase, making it easier for developers to collaborate effectively.