# Contributing to fleXRP

First off, thank you for considering contributing to fleXRP! It's people like you that make fleXRP such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct (to be created).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible

### Suggesting Enhancements

If you have a suggestion for the project, we'd love to hear it. Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* A clear and descriptive title
* A detailed description of the proposed enhancement
* Examples of how the enhancement would be used
* Any potential drawbacks or considerations

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue the pull request

## Development Process

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git commit -m "Description of changes"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/garotconklin/fleXRP.git
   cd fleXRP
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Run tests:
   ```bash
   pytest
   ```

## Style Guide

* Follow PEP 8 style guide for Python code
* Use meaningful variable names
* Write docstrings for functions and classes
* Comment your code when necessary
* Keep functions focused and concise

## Testing

* Write unit tests for new features
* Ensure all tests pass before submitting PR
* Aim for good test coverage
* Include both positive and negative test cases

## Documentation

* Update README.md if needed
* Document new features
* Keep API documentation up to date
* Include docstrings in code

## Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

## Additional Notes

### Issue and Pull Request Labels

* `bug` - Something isn't working
* `enhancement` - New feature or request
* `documentation` - Documentation only changes
* `help-wanted` - Extra attention is needed
* `work-in-progress` - Still under development

## Questions?

Feel free to contact the project maintainers if you have any questions:
* @garotconklin
* @theusc6

Thank you for contributing to fleXRP!
