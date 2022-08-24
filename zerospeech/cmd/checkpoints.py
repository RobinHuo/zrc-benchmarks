import argparse

from rich.table import Table

from .cli_lib import CMD
from ..model import checkpoints
from ..out import console, error_console


class CheckpointsCMD(CMD):
    """Manipulate Checkpoints """
    COMMAND = "checkpoints"
    NAMESPACE = ""

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument("--local", action="store_true", help="List local checkpoint only")

    def run(self, argv: argparse.Namespace):
        checkpoints_dir = checkpoints.CheckpointDir.load()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("Origin")
        table.add_column("Size")
        table.add_column("Installed")

        if argv.local:
            dt_list = checkpoints_dir.items
        else:
            dt_list = checkpoints_dir.available_items

        for d in dt_list:
            dts = checkpoints_dir.get(d)
            table.add_row(
                dts.name, dts.origin.origin_host, dts.origin.size_label, f"{dts.installed}"
            )

        console.print(table)


class PullCheckpointCMD(CMD):
    """ Download a checkpoint item """
    COMMAND = "pull"
    NAMESPACE = "checkpoints"

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('name')
        parser.add_argument('-q', '--quiet', action='store_true', help='Suppress download info output')

    def run(self, argv: argparse.Namespace):
        datasets = checkpoints.CheckpointDir.load()
        dataset = datasets.get(argv.name)
        dataset.pull(quiet=argv.quiet, show_progress=True)


class RemoveCheckpointCMD(CMD):
    """ Remove a checkpoint item """
    COMMAND = "rm"
    NAMESPACE = "checkpoints"

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('name')

    def run(self, argv: argparse.Namespace):
        checkpoints_dir = checkpoints.CheckpointDir.load()
        cpt = checkpoints_dir.get(argv.name)
        if cpt:
            cpt.uninstall()
            console.log("[green] Checkpoint uninstalled successfully !")
        else:
            error_console.log(f"Failed to find checkpoint named :{argv.name}")
