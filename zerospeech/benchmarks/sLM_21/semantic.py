import enum
import functools
from pathlib import Path
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd
import scipy.spatial
import scipy.stats

from .data import SLM21Task, SLM21Submission, SLM21Dataset
from ...data_items import FileListItem, FileItem
from ...data_loaders import load_dataframe, load_numpy_array

# using metrics from scipy.spatial.distance.cdist
_SciPyMetrics = ['braycurtis', 'canberra', 'chebyshev', 'cityblock', 'correlation', 'cosine', 'dice',
                 'euclidean', 'hamming', 'jaccard', 'jensenshannon', 'kulczynski1', 'mahalanobis',
                 'matching', 'minkowski', 'rogerstanimoto', 'russellrao', 'seuclidean',
                 'sokalmichener', 'sokalsneath', 'sqeuclidean', 'yule']

# Enumeration of metrics used for semantics benchmark
SemanticMetrics = enum.Enum('SemanticMetrics', {f"{k}": k for k in _SciPyMetrics})


class SemanticPooling(str, enum.Enum):
    min = 'min'
    max = 'max'
    mean = 'mean'
    sum = 'sum'
    last = 'last'
    lastlast = 'lastlast'
    off = 'off'

    @property
    def fn(self):
        if self == self.max:
            return functools.partial(np.max, axis=0)
        elif self == self.min:
            return functools.partial(np.min, axis=0)
        elif self == self.mean:
            return functools.partial(np.mean, axis=0)
        elif self == self.sum:
            return functools.partial(np.sum, axis=0)
        elif self == self.last:
            return lambda x: x[-1]
        elif self == self.lastlast:
            return lambda x: x[-2]
        elif self == self.off:
            return lambda x: x
        else:
            raise ValueError(
                f'pooling method must be {",".join([f.value for f in self])}'
            )


class SemanticTask(SLM21Task):
    _name = "semantic"
    metric: SemanticMetrics = SemanticMetrics('euclidean')
    pooling: SemanticPooling = SemanticPooling.mean
    synthetic: bool = True
    librispeech: bool = True
    correlations: bool = True
    n_jobs: int = 1
    sets = ('dev', 'test')
    # todo make filename simpler with flat dict & property fn
    result_filenames = dict(
        dev=[
            'score_semantic_dev_pairs.csv', 'score_semantic_dev_correlation.csv'
        ],
        test=[
            'score_semantic_test_pairs.csv', 'score_semantic_test_correlation.csv'
        ]
    )

    def compute_correlation(self, pairs: pd.DataFrame) -> Optional[pd.DataFrame]:
        """"Returns the Spearman's correlation between human and machine scores"""
        if not self.correlations:
            return None

        def _correlation(df):
            # choose 'similarity' or 'relatedness' column (the one with no NaN)
            human = df.similarity if df.relatedness.hasnans else df.relatedness
            # return spearman correlation. Humans score are similarity (high when
            # close) so we take the opposite to have a quantity close to a distance
            # (low when close)
            return 100 * scipy.stats.spearmanr(  # noqa: bad __init__ in scipy ?
                - human.to_numpy(), df.score.to_numpy())[0]

        # for each (type/dataset) combination, compute spearman correlation
        series = pairs.groupby([pairs['type'], pairs['dataset']]).apply(_correlation)
        # transform raw result in a usable dataframe
        return series.to_frame().rename(columns={0: 'correlation'}).reset_index()

    def compute_distance(self, pairs_row: pd.Series, gold_df: pd.DataFrame, pool: pd.DataFrame):
        # keep only current type in gold
        gold_df = gold_df[gold_df['type'] == pairs_row['type']]

        if pairs_row['type'] == 'librispeech':
            # get the list of tokens corresponding to the given pair of words
            tokens_1 = gold_df['filename'][gold_df['word'] == pairs_row['word_1']]
            tokens_2 = gold_df['filename'][gold_df['word'] == pairs_row['word_2']]
            assert 0 < len(tokens_1) <= 10 and 0 < len(tokens_2) <= 10

            x = np.asarray(pool[pool['filename'].isin(tokens_1)]['pooling'].tolist())
            y = np.asarray(pool[pool['filename'].isin(tokens_2)]['pooling'].tolist())

            # compute the mean distance across all pairs of tokens after pooling
            return scipy.spatial.distance.cdist(  # noqa: bad __init__ for scipy.spatial ??
                x, y, metric=self.metric.value).mean()
        elif pairs_row['type'] == 'synthetic':
            # get the list of tokens corresponding to the given pair of words
            tokens_1 = gold_df[['filename', 'voice']][gold_df['word'] == pairs_row['word_1']]
            tokens_2 = gold_df[['filename', 'voice']][gold_df['word'] == pairs_row['word_2']]
            tokens = tokens_1.merge(tokens_2, on='voice').drop(['voice'], axis=1)

            # compute the mean of distances within a given voice
            dist = 0
            for _, (filename_x, filename_y) in tokens.iterrows():
                x = pool[pool['filename'] == filename_x]['pooling'].item()
                y = pool[pool['filename'] == filename_y]['pooling'].item()
                dist += scipy.spatial.distance.cdist(  # noqa: bad __init__ for scipy.spatial ??
                    np.atleast_2d(x), np.atleast_2d(y), metric=str(self.metric))[0][0]

            return dist / len(tokens)

    def build_file_index(self, synthetic: FileListItem, librispeech: FileListItem) -> Dict[str, Dict[str, Path]]:
        file_index = {}
        if self.librispeech:
            file_index['librispeech'] = {
                f"{p.stem}": p
                for p in librispeech
            }
        if self.synthetic:
            file_index['synthetic'] = {
                f"{p.stem}": p
                for p in synthetic
            }

        return file_index

    def semantic_eval(self, file_index: Dict[str, Dict[str, Path]],
                      gold: FileItem, pairs: FileItem):
        """ Semantically evaluate a subset """
        pairs_df = load_dataframe(pairs, header=0)
        gold_df = load_dataframe(gold, header=0)

        if not self.synthetic:
            gold_df = gold_df.drop(gold_df[gold_df['type'] == 'synthetic'].index)
            pairs_df = pairs_df.drop(pairs_df[pairs_df['type'] == 'synthetic'].index)

        if not self.librispeech:
            gold_df = gold_df.drop(gold_df[gold_df['type'] == 'librispeech'].index)
            pairs_df = pairs_df.drop(pairs_df[pairs_df['type'] == 'librispeech'].index)

        def compute(_row: pd.Series):
            """ Compute pooling from submission array """
            fname = file_index.get(_row[0], {}).get(_row[1], None)
            if fname is None:
                return _row[1], _row[0], None
            data = load_numpy_array(fname)
            # values
            return _row[1], _row[0], self.pooling.fn(data)

        # compute pooling from g
        res = joblib.Parallel(n_jobs=self.n_jobs)(joblib.delayed(compute)(x) for _, x in gold_df.iterrows())
        pool = pd.DataFrame(res, columns=['filename', 'type', 'pooling'])

        pairs_df['score'] = [
            self.compute_distance(pairs_row, gold_df, pool)
            for _, pairs_row in pairs_df.iterrows()
        ]

        correlation = self.compute_correlation(pairs_df)

        return pairs_df, correlation

    def eval(self, submission: SLM21Submission, dataset: SLM21Dataset):
        """ Run the selected semantic evaluations & write results """
        outputs_dir = submission.score_dir
        self.sets = submission.sets

        if 'dev' in self.sets:
            gold = dataset.index.subsets.semantic_dev.items.gold
            pairs = dataset.index.subsets.semantic_dev.items.pairs
            file_index = self.build_file_index(
                synthetic=submission.items.semantic_dev_synthetic,
                librispeech=submission.items.semantic_dev_librispeech
            )
            res_pairs, correlation = self.semantic_eval(file_index, gold, pairs)

            filename = outputs_dir / self.result_filenames['dev'][0]
            res_pairs.to_csv(filename, index=False, float_format='%.4f')

            if self.correlations and correlation:
                filename = outputs_dir / self.result_filenames['dev'][1]
                correlation.to_csv(filename, index=False, float_format='%.4f')

        if 'test' in self.sets:
            gold = dataset.index.subsets.semantic_test.items.gold
            pairs = dataset.index.subsets.semantic_test.items.pairs
            file_index = self.build_file_index(
                synthetic=submission.items.semantic_test_synthetic,
                librispeech=submission.items.semantic_test_librispeech
            )
            res_pairs, correlation = self.semantic_eval(file_index, gold, pairs)

            filename = outputs_dir / self.result_filenames['test'][0]
            res_pairs.to_csv(filename, index=False, float_format='%.4f')

            if self.correlations and correlation:
                filename = outputs_dir / self.result_filenames['test'][1]
                correlation.to_csv(filename, index=False, float_format='%.4f')

