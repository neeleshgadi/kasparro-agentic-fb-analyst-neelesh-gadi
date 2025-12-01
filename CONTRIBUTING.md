# Contributing to Kasparro

Thank you for your interest in contributing to Kasparro! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/kasparro-agentic-fb-analyst-neelesh-gadi.git`
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment
5. Install dependencies: `pip install -r requirements.txt`
6. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Workflow

### Making Changes

1. Make your changes in your feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `pytest tests/`
4. Update documentation as needed
5. Commit your changes with clear, descriptive messages

### Commit Message Guidelines

Use clear and descriptive commit messages:

- `feat: Add new creative generation algorithm`
- `fix: Correct ROAS calculation in data agent`
- `docs: Update README with new configuration options`
- `test: Add property tests for evaluator agent`
- `refactor: Simplify insight agent logic`

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

### Testing

All new features must include tests:

- **Unit tests**: Test individual functions and methods
- **Property tests**: Use Hypothesis for property-based testing
- **Integration tests**: Test agent interactions and workflows

Run tests before submitting:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_properties_data_agent.py
```

### Documentation

Update documentation when adding features:

- Update README.md with new usage examples
- Add docstrings to new functions
- Update agent_graph.md if workflow changes
- Document new configuration options

## Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Push your branch to your fork
4. Open a Pull Request against the main repository
5. Describe your changes clearly in the PR description
6. Link any related issues

### PR Checklist

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] Commit messages are clear
- [ ] No merge conflicts

## Code Review

All submissions require review. We aim to:

- Provide feedback within 48 hours
- Be constructive and respectful
- Focus on code quality and maintainability

## Questions?

If you have questions, please:

- Check existing documentation
- Search closed issues
- Open a new issue with the "question" label

Thank you for contributing to Kasparro!
