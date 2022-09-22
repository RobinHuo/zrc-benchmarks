import argparse

from rich.table import Table

from .cli_lib import CMD
from ..model import datasets
from ..out import console, error_console


class DatasetCMD(CMD):
    """ Manipulate Datasets """
    COMMAND = "datasets"
    NAMESPACE = ""

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument("--local", action="store_true", help="List local datasets only")

    def run(self, argv: argparse.Namespace):
        datasets_dir = datasets.DatasetsDir.load()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("Origin")
        table.add_column("Size")
        table.add_column("Installed")

        if argv.local:
            dt_list = datasets_dir.items
        else:
            dt_list = datasets_dir.available_items

        for d in dt_list:
            dts = datasets_dir.get(d)
            table.add_row(
                dts.name, dts.origin.origin_host, dts.origin.size_label, f"{dts.installed}"
            )

        console.print(table)


class PullDatasetCMD(CMD):
    """ Download a dataset """
    COMMAND = "pull"
    NAMESPACE = "datasets"

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('name')
        parser.add_argument('-q', '--quiet', action='store_true', help='Suppress download info output')

    def run(self, argv: argparse.Namespace):
        datasets_dir = datasets.DatasetsDir.load()
        dataset = datasets_dir.get(argv.name, cls=datasets.Dataset)
        dataset.pull(quiet=argv.quiet, show_progress=True)


class RemoveDatasetCMD(CMD):
    """ Remove a dataset item """
    COMMAND = "rm"
    NAMESPACE = "datasets"

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('name')

    def run(self, argv: argparse.Namespace):
        dataset_dir = datasets.DatasetsDir.load()
        dts = dataset_dir.get(argv.name)
        if dts:
            dts.uninstall()
            console.log("[green] Dataset uninstalled successfully !")
        else:
            error_console.log(f"Failed to find dataset named :{argv.name}")
