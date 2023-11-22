import click

import bib_dedupe.debug


@click.group()
def main() -> None:
    """A simple CLI for bib_dedupe."""
    pass


@main.command()
@click.pass_context
def debug(ctx: click.Context) -> None:
    bib_dedupe.debug.debug()


if __name__ == "__main__":
    main()
