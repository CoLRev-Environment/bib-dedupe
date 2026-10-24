# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report duplicate error (FP or FN)

Provide the case in the following format, allowing us to add it to the `tests/test_cases.json`:

```json
{
    "id": "abrahao_parigi_gupta_cook_2017_pnas_short_vs_full",
    "note": "Same paper; record_b uses abbreviated author formatting and omits venue fields; record_a includes DOI.",

    "record_a": {
        "ENTRYTYPE": "article",
        "ID": "1",
        "doi": "10.1073/PNAS.1604234114",
        "author": "Abrahao, Bruno and Parigi, Paolo and Gupta, Alok and Cook, Karen S.",
        "title": "Reputation offsets trust judgments based on social biases among Airbnb users",
        "journal": "Proceedings of the National Academy of Sciences",
        "number": "37",
        "pages": "9848--9853",
        "volume": "114",
        "year": "2017"
    },
    "record_b": {
        "ENTRYTYPE": "article",
        "ID": "2",
        "author": "B. Abrahao; P. Parigi; A. Gupta; K. S. Cook",
        "year": "2017",
        "title": "Reputation offsets trust judgments based on social biases among Airbnb users"
    },

"expected_duplicate": true
}
```

### Fixing duplicate errors

All changes to deduplication logic (`prep`, `sim`, `match`) should be accompanied with a test case in the pull request.

TODO:
- before merging, the ldd-full tests should be run to determine how the changes affect overall performance. (TBD: locally? how will it be triggered? how do we ensure that the right version/branch is tested? How are results added in the pull request? Do we want to consider performance implications?)
- consider possiblity of schema inconsistency

### Report Bugs

Report bugs at https://github.com/CoLRev-Environment/bib-dedupe/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

BibDedupe could always use more documentation, whether as part of the
official BibDedupe docs, in docstrings, or even on the web in blog posts,
articles, and such.

#### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/CoLRev-Environment/bib-dedupe/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up BibDedupe for local development.

1. Fork the `bib-dedupe` repo on GitHub.
2. Clone your fork locally:

    ```sh
    git clone git@github.com:your_name_here/bib-dedupe.git
    ```

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development:

    ```sh
    mkvirtualenv bib-dedupe
    cd bib-dedupe/
    pip3 install poetry
    poetry install
    ```

4. Create a branch for local development:

    ```sh
    git checkout -b name-of-your-bugfix-or-feature
    ```

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass the
   tests and pre-commit hooks:

    ```sh
    pytest
    pre-commit run -a
    ```

6. Commit your changes and push your branch to GitHub:

    ```sh
    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature
    ```

7. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for the Python versions specified in the `pyproject.toml`.
   Make sure that the tests pass for all supported Python versions.

## Coding standards

- Named parameters are preferred over positional parameters to avoid ambiguity and facilitate code refactoring.
- Variable names should help to avoid ambiguities and indicate their type if necessary.
- All tests and code linters (pre-commit-hooks) should pass.

## Release

See [release checklist](release-checklist.md).
