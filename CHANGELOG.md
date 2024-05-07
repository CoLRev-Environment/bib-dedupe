# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0).

<!--
## Unreleased

### Added

### Changed

### Removed

### Fixed
-->

## 0.7.5 - 2024-05-07

- Require Python>=3.9
- Evaluation: Replace notebook with Python script
- Fix #25 (inconsistent behavior when `numexpr` is installed)

## 0.7.4 - 2024-04-29

- Add [ASySD](https://github.com/camaradesuk/ASySD) to the evaluation
- Update docs for evaluation
- Prevent SettingWithCopyWarning in maybe_cases and zero-division in precision

## 0.7.3 - 2024-04-16

- Load example datasets on demand to avoid large package size (potentially causes errors during installation [1](https://github.com/CoLRev-Environment/colrev/actions/runs/8711093539/job/23894441546))

## 0.7.2 - 2024-04-12

- block: prevent type/FutureWarning

## 0.7.1 - 2024-04-12

- Docs: add setup and installation instructions.
- Include example data (`load_example_data`)
- Implement version without multiprocessing (parallel computation)
- Docs: build from latest version (not PyPI release)

## 0.7.0 - 2024-01-22

- Performance improvements
- Codebase refactoring
- Documentation updated

## 0.6.0 - 2024-01-04

- Replaced methods with functions
- Refactoring and performance improvements

## 0.5.0 - 2023-12-13

- Fix return value in match()

## 0.4.0 - 2023-12-13

- Add dependencies

## 0.3.0 - 2023-12-13

- Include clustering

## 0.2.0 - 2023-12-13

- Extended matching conditions and preparation
- Updated data structure

## 0.1.0 - 2023-11-12

- Initial release.
