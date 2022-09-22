from pydantic import Field

from ...model import m_benchmark
from ..datasets import AbxLSDataset
from .data_model import AbxLSSubmission, AbxLSTask


class AbxLSBenchmark(m_benchmark.Benchmark):
    """abx-LS is a benchmark on acoustic Units using the ABX metric.

    This benchmark has 2 sub-tasks :

    - clean
    - other

    Each task has two subsets:  dev, test

    For more information visit: https://version2.zerospeech.com/tasks/task_1/benchmarks_datasets/#abx-ls
    For ABX measuring we use this module : https://github.com/zerospeech/libri-light-abx
    """
    _name = "abx-LS"
    dataset: AbxLSDataset = Field(default_factory=lambda: AbxLSDataset.load())

    def run(self, submission: AbxLSSubmission):
        """ Run abx-LS tasks """
        params = submission.params
        self.console.print(f'Running {self.name} benchmark on {submission.location.name}')

        # create output dir
        submission.score_dir.mkdir(exist_ok=True, parents=True)
        task = AbxLSTask(**params.get_task())
        task.eval(submission, self.dataset)

        # todo leaderboard entry ...
        self.console.print(f'[green]:heavy_check_mark:[/green]Evaluation of benchmark completed successfully ')
        self.console.print(f"Scores can be found @ {submission.score_dir}")

