# BibDedupe

<!-- [![License](https://img.shields.io/github/license/CoLRev-Ecosystem/bib-dedupe.svg)](https://github.com/CoLRev-Environment/bib-dedupe/releases/) -->
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bib-dedupe)


## Overview

BibDedupe is an open-source **Python library for deduplication of bibliographic records**, tailored for literature reviews.
Unlike traditional deduplication methods, BibDedupe focuses on entity resolution, linking duplicate records instead of simply deleting them.

## Features

- **Automated Duplicate Linking with Zero False Positives**: BibDedupe automates the duplicate linking process with a focus on eliminating false positives.
- **Preprocessing Approach**: BibDedupe uses a preprocessing approach that reflects the unique error generation process in academic databases, such as author re-formatting, journal abbreviation or translations.
- **Entity Resolution**: BibDedupe does not simply delete duplicates, but it links duplicates to resolve the entitity and integrates the data. This allows for validation, and undo operations.
- **Programmatic Access**: BibDedupe is designed for seamless integration into existing research workflows, providing programmatic access for easy incorporation into scripts and applications.
- **Transparent and Reproducible Rules**: BibDedupe's blocking and matching rules are transparent and easily reproducible to promote reproducibility in deduplication processes.
- **Continuous Benchmarking**: Continuous integration tests running on GitHub Actions ensure ongoing benchmarking, maintaining the library's reliability and performance across datasets.
- **Efficient and Parallel Computation**: BibDedupe implements computations efficiently and in parallel, using appropriate data structures and functions for optimal performance.

## Documentation

Explore the [official documentation](https://colrev-environment.github.io/bib-dedupe/) for comprehensive information on installation, usage, and customization of BibDedupe.

## Citation

If you use BibDedupe in your research, please cite it as follows:

Wagner, G. (2024) BibDedupe - An open-source Python library for deduplication of bibliographic records. Available at https://github.com/CoLRev-Environment/bib-dedupe.


## Contribution Guidelines

We welcome contributions from the community to enhance and expand BibDedupe. If you would like to contribute, please follow our [contribution guidelines](CONTRIBUTING.md).

## License

BibDedupe is released under the [MIT License](LICENSE), allowing free and open use and modification.

## Contact

For any questions, issues, or feedback, please open an [issue](https://github.com/CoLRev-Environment/bib-dedupe/issues) on our GitHub repository.

Happy deduplicating with BibDedupe!
