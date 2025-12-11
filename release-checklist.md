# Release checklist

For all releases:

- Collect release notes and update the `CHANGELOG.md`.
- Update the version in `pyproject.toml`. Check whether other parts of the `pyproject.toml` need to be updated. Check whether dependencies can be removed.
- Commit the changes (`release 0.10.0`).
- Push to Github. Check whether the installation, tests, and pre-commit hooks pass.
- Run `git tag -s $VERSION` (format: "0.9.1").
- Run `pip3 install -e .` locally (before testing upgrade in local repositories).
- Check whether the tests pass locally (``pytest tests``).
- Run `git push --atomic origin main $VERSION`.

- Create [new release on Github](https://github.com/CoLRev-Environment/bib-dedupe/releases/new)
    - Select new tag
    - Enter the release notes
    - Publish the release
    - The PyPI version is published through a [github action](https://github.com/CoLRev-Environment/bib-dedupe/actions/workflows/publish.yml):  ![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/CoLRev-Ecosystem/bib-dedupe/publish.yml)
