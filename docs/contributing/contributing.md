# Contributing

First, thanks for contributing 🎉🎉🎉

**Before you get started:** 

- We require contributors to sign a Contributor License Agreement (CLA). We know legal agreements aren't the most exciting part of contributing, so we've put together a short explanation of why we need one, what it means for you, and the full CLA for you to read. You can find everything [here](cla.md).
  
- Interested in contributing? Great! Once you've had a look at the [CLA](cla.md), please email *tobias.rohrer@ise.fraunhofer.de*. We'll provide you with an editable copy and sort out the signing process with you.

Contributions fall into two categories:

1. You propose a new feature or report a bug:
   - Create an [Issue](Issue) and we discuss the design and implementation. 
      Once it's all agreed, one can go ahead and implement it 
2. You want to work on an outstanding issue:
   - Outstanding issues are here: [help wanted](help wanted)
   - Pick the issue or feature and comment on the task you want to work on. Ask for more information in the issue if needed.

Once you finish implementation, sent a pull request to [link-to-repo](link-to-repo)

If you are not familiar with creating a pull request, here are some guides:

- [https://stackoverflow.com/questions/14680711/how-to-do-a-github-pull-request](https://stackoverflow.com/questions/14680711/how-to-do-a-github-pull-request)
- [https://help.github.com/articles/creating-a-pull-request/](https://help.github.com/articles/creating-a-pull-request/)


# Development

To develop *NRGISE Open* on your machine:

1. Clone a copy of NRGISE from source:

```bash
git clone link
cd link/
```

2. Install NRGISE in development mode:

```bash
pip install -e '.[dev]'
```

# Codestyle, Typing and Code Documentation

We aim to maintain a high level of code quality and readability throughout NRGISE. Before committing your changes, please run:

```bash
sh scripts/validate_code.sh
```

This runs the relevant code quality checks and tests, including:

1. **Code style with [Ruff](https://docs.astral.sh/ruff/)**  
   We use Ruff to enforce consistent Python code style. Ruff can also be integrated into editors such as VS Code and PyCharm. To run it manually:
   ```bash
   ruff check .
   ```

2. **Type checking with [mypy](https://mypy.readthedocs.io/)**  
   NRGISE uses Python type annotations. New code should be properly typed and pass mypy's static type checks. To run it:
   ```bash
   mypy nrgise tests
   ```

3. **Tests with [pytest](https://docs.pytest.org/)**  
   To run the test suite:
   ```bash
   pytest
   ```

These checks are also part of our CI pipeline and must pass before a contribution can be merged.

Please also document each public function and method using Google-style docstrings:
```python

def my_function(arg1: type1, arg2: type2) -> returntype:
    """
    Short description

    Args:
        arg1: what is arg1?
        arg2: what is arg2?

    Returns:
        describe what is returned
    """
    ...
    return my_variable
```

# Tests

All new features and changes must be tested. Please add or update the corresponding tests in `/tests`.

# Documentation

- We use `mkdocs` to document our code. 
- You can start the local documentation server by running: `mkdocs serve`.
- Change the documentation (located at `/docs`) if necessary. 
- Code documentation should be done in google style (see above).

# Pull Request (PR)

If all tests and style checks pass, you can create a pull request. Each PR will be reviewed by at least one of the maintainers (@tobirohrer, @ricardasgithubuser, @nilsgithubuser).

# Other

Note: This contribution guide was inspired by the one from [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3/blob/master/CONTRIBUTING.md).