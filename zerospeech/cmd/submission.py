import argparse
import sys
from pathlib import Path

from .cli_lib import CMD
from ..benchmarks import BenchmarkList
from ..data_loaders import zip_zippable
from ..model import m_benchmark, m_meta_file
from ..out import error_console, warning_console, console as std_console


class Submission(CMD):
    """ Submission manager subcommand """
    COMMAND = "submission"
    NAMESPACE = ""

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.print_help()

    def run(self, argv: argparse.Namespace):
        pass


class SubmissionInit(CMD):
    """ Initialise a directory for a specific benchmark """
    COMMAND = "init"
    NAMESPACE = "submission"

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument("name")
        parser.add_argument("location")

    def run(self, argv: argparse.Namespace):
        try:
            bench = BenchmarkList(argv.name)
        except ValueError:
            error_console.log(f"Specified benchmark ({argv.name}) does not exist !!!!")
            warning_console.log(f"Use one of the following : {','.join(b for b in BenchmarkList)}")
            sys.exit(1)

        location = Path(argv.location)
        if location.is_dir():
            error_console.log(f"Location specified already exists !!!")
            sys.exit(2)

        with std_console.status("Initialising submission dir"):
            bench.submission.init_dir(location)

        std_console.print(f"Submission directory created @ {location}", style="green bold")


class BenchmarkParamsCMD(CMD):
    """ Create template params.yaml """
    COMMAND = "params"
    NAMESPACE = "submission"

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument("submission_dir")
        parser.add_argument('-r', '--reset', action="store_true", help="Reset params.yaml to default values")

    def run(self, argv: argparse.Namespace):
        location = Path(argv.submission_dir)
        if not location.is_dir():
            error_console(f"Location specified does not exist !!!")
            sys.exit(2)

        benchmark_name = None
        try:
            benchmark_name = m_meta_file.MetaFile.benchmark_from_submission(location)
            if benchmark_name is None:
                raise TypeError("benchmark not found")

            bench = BenchmarkList(benchmark_name)
        except TypeError:
            error_console.log(f"Specified submission does not have a valid {m_meta_file.MetaFile.file_stem}"
                              f"\nCannot find benchmark type")
            sys.exit(1)
        except ValueError:
            error_console.log(f"Specified benchmark ({benchmark_name}) does not exist !!!!")
            warning_console.log(f"Use one of the following : {','.join(b for b in BenchmarkList)}")
            sys.exit(1)

        if argv.reset:
            # remove old params file if exists
            (location / m_benchmark.BenchmarkParameters.file_stem).unlink(missing_ok=True)

        submission = bench.submission.load(path=location)
        if argv.reset:
            self.console.log(f"Params file created/reset at @ {submission.params_file}")

        self.console.print(submission.params)


class SubmissionVerify(CMD):
    """ Verify the validity of a submission """
    COMMAND = "verify"
    NAMESPACE = "submission"

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument("location")

    def run(self, argv: argparse.Namespace):
        location = Path(argv.location)
        if not location.is_dir():
            error_console(f"Location specified does not exist !!!")
            sys.exit(2)

        benchmark_name = None
        try:
            benchmark_name = m_meta_file.MetaFile.benchmark_from_submission(location)
            if benchmark_name is None:
                raise TypeError("benchmark not found")

            bench = BenchmarkList(benchmark_name)
        except TypeError:
            error_console.log(f"Specified submission does not have a valid {m_meta_file.MetaFile.file_stem}"
                              f"\nCannot find benchmark type")
            sys.exit(1)
        except ValueError:
            error_console.log(f"Specified benchmark ({benchmark_name}) does not exist !!!!")
            warning_console.log(f"Use one of the following : {','.join(b for b in BenchmarkList)}")
            sys.exit(1)

        submission = bench.submission.load(location)
        with std_console.status(f"Validating submission @ {location}"):
            _ = submission.valid

        if submission.valid:
            std_console.print(f"Submission @ {location} is a valid submission for {bench} :heavy_check_mark:",
                              style='bold green')
        else:
            m_benchmark.show_errors(submission.validation_output)


class SubmissionZip(CMD):
    """ Create a zip archive of a submission """
    COMMAND = "zip"
    NAMESPACE = "submission"

    def init_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument("name")
        parser.add_argument("submission_location")
        parser.add_argument("archive_path")

    def run(self, argv: argparse.Namespace):
        try:
            bench = BenchmarkList(argv.name)
        except ValueError:
            error_console.log(f"Specified benchmark ({argv.name}) does not exist !!!!")
            warning_console.log(f"Use one of the following : {','.join(b for b in BenchmarkList)}")
            sys.exit(1)

        submission_location = Path(argv.submission_location)
        if not submission_location.is_dir():
            error_console(f"Submission location specified does not exist !!!")
            sys.exit(2)

        archive_file = Path(argv.archive_path)
        if archive_file.is_file():
            error_console(f"Given archive file already exists !!!")
            sys.exit(3)

        submission = bench.submission.load(submission_location)
        with std_console.status("Compressing files..."):
            zip_zippable(submission, archive_file)

        std_console.print(f":pencil: Successfully written submission to archive {archive_file.name}")


class SubmissionUpload(CMD):
    """ Upload a submission to zerospeech.com """
    COMMAND = "upload"
    NAMESPACE = "submission"

    def init_parser(self, parser: argparse.ArgumentParser):
        pass

    def run(self, argv: argparse.Namespace):
        std_console.print("Functionality not yet implemented !", style="bold orange_red1")
