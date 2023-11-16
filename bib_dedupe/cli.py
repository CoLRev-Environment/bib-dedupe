import click

import bib_dedupe.bib_dedupe


@click.group()
def main():
    """A simple CLI for bib_dedupe."""
    pass


@main.command()
@click.pass_context
def debug(
    ctx,
) -> None:
    bib_dedupe.bib_dedupe.debug()


if __name__ == "__main__":
    main()
