import enum

from ..model import m_benchmark, m_score_dir
from . import sLM_21, abx_LS


class BenchmarkList(str, enum.Enum):
    """ Simplified enum """

    def __new__(
            cls,
            label, benchmark, submission: m_benchmark.Submission,
            score_dir: m_score_dir.ScoreDir
    ):
        """ Allow setting parameters on enum """
        obj = str.__new__(cls, label)
        obj._value_ = label
        obj.benchmark = benchmark
        obj.submission = submission
        obj.score_dir = score_dir
        return obj

    sLM21 = 'sLM21', sLM_21.SLM21Benchmark, \
            sLM_21.SLM21Submission, sLM_21.SLM21ScoreDir
    abx_LS = 'abx-LS', abx_LS.AbxLSBenchmark, \
             abx_LS.AbxLSSubmission, abx_LS.ABXLSScoreDir
