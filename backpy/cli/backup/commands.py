import click


@click.command("backup", help="Actions related to creating and managing backups.")
@click.option("--test", default="A", help="Testomatico")
def command(test):
    print(test)
