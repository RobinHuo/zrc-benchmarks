import pandas as pd

from .data import SLM21Task, SLM21Submission, SLM21Dataset
from ...data_items import FileItem
from ...data_loaders import load_dataframe


class LexicalTask(SLM21Task):
    _name = "lexical"
    by_pair: bool = True
    by_length: bool = True
    by_frequency: bool = True
    # todo make filename simpler with flat dict & property fn
    result_filenames = dict(
        dev=[
            'score_lexical_dev_by_pair.csv', 'score_lexical_dev_by_frequency.csv', 'score_lexical_dev_by_length.csv'],
        test=[
            'score_lexical_test_by_pair.csv', 'score_lexical_test_by_frequency.csv', 'score_lexical_test_by_length.csv']
    )

    @staticmethod
    def load_and_format(lexical_item: FileItem, gold_item: FileItem):
        """ Loads & formats submission data and gold data """
        gold_values = load_dataframe(gold_item, header=0, index_col='filename').astype(
            {'frequency': pd.Int64Dtype()})

        lexical_values = load_dataframe(lexical_item, sep=' ', header=None,
                                        names=['filename', 'score'], index_col='filename')

        # merge the gold and score using filenames, then remove the columns
        # 'phones' and 'filename' as we don't use them for evaluation
        data = pd.merge(gold_values, lexical_values, on='filename', how='inner')
        data.reset_index(inplace=True)

        # if all non-words have their textual version set to NaN, we take their phonemic version instead.
        if data[data.correct == 0]['word'].isnull().sum() == len(data[data.correct == 0]):
            data['word'] = data['phones']
        data.drop(columns=['phones', 'filename'], inplace=True)

        # going from a word per line to a pair (word, non word) per line
        words = data.loc[data['correct'] == 1].reset_index().rename(lambda x: 'w_' + x, axis=1)
        non_words = data.loc[data['correct'] == 0].reset_index().rename(lambda x: 'nw_' + x, axis=1)
        data = pd.merge(words, non_words, left_on=['w_voice', 'w_id'], right_on=['nw_voice', 'nw_id'])

        data.drop(
            ['w_index', 'nw_index', 'nw_voice', 'nw_frequency',
             'w_correct', 'nw_correct', 'nw_id', 'nw_length'],
            axis=1, inplace=True)
        data.rename(
            {'w_id': 'id', 'w_voice': 'voice', 'w_frequency': 'frequency',
             'w_word': 'word', 'nw_word': 'non word', 'w_length': 'length',
             'w_score': 'score word', 'nw_score': 'score non word'},
            axis=1, inplace=True)
        return data

    @staticmethod
    def eval_by_pair(data: pd.DataFrame) -> pd.DataFrame:
        """Returns a data frame with the computed scores by (word, non word) pair

            Parameters
            ----------
            data : pandas.DataFrame
                The result of `load_data`

            Returns
            -------
            by_pair : pandas.DataFrame
                The evaluated (word, non word) pairs, the data frame has the columns:
                'word', 'non word' 'frequency', 'length' and 'score'.

            """
        # compute the score for each pair in an additional 'score' column, then
        # delete the 'score word' and 'score non word' columns that become useless
        score = data.loc[:, ['score word', 'score non word']].to_numpy()
        data['score'] = (
                0.5 * (score[:, 0] == score[:, 1])
                + (score[:, 0] > score[:, 1]))
        data.drop(columns=['score word', 'score non word'], inplace=True)

        # finally get the mean score across voices for all pairs
        score = data.groupby('id').apply(lambda x: (
            x.iat[0, 3],  # word
            x.iat[0, 5],  # non word
            x.iat[0, 2],  # frequency
            x.iat[0, 4],  # length
            x['score'].mean()))
        return pd.DataFrame(
            score.to_list(),
            columns=['word', 'non word', 'frequency', 'length', 'score'])

    @staticmethod
    def eval_by_frequency(data: pd.DataFrame) -> pd.DataFrame:
        """Returns a data frame with mean scores by frequency bands

            The frequency is defined as the number of occurrences of the word in the
            LibriSpeech dataset. The following frequency bands are considered : oov,
            1-5, 6-20, 21-100 and >100.

            Parameters
            ----------
            data: pandas.DataFrame
                The output of `evaluate_by_pair`

            Returns
            -------
            by_frequency : pandas.DataFrame
                The score collapsed on frequency bands, the data frame has the
                following columns: 'frequency', 'score'.

            """
        bands = pd.cut(
            data.frequency,
            [0, 1, 5, 20, 100, float('inf')],
            labels=['oov', '1-5', '6-20', '21-100', '>100'],
            right=False)

        return data.score.groupby(bands).agg(
            n='count', score='mean', std='std').reset_index()

    @staticmethod
    def eval_by_length(data: pd.DataFrame) -> pd.DataFrame:
        """Returns a data frame with mean scores by word length

        Parameters
        ----------
        data: pandas.DataFrame
            The output of `evaluate_by_pair`

        Returns
        -------
        by_length : pandas.DataFrame
            The score collapsed on word length, the data frame has the
            following columns: 'length', 'score'.

        """
        return data.score.groupby(data.length).agg(
            n='count', score='mean', std='std').reset_index()

    def run_lexical_eval(self, lexical_item: FileItem, gold_item: FileItem):
        print(f"{type(lexical_item)=}, {type(lexical_item)=}")
        data = self.load_and_format(lexical_item, gold_item)
        by_pair, by_frequency, by_length = None, None, None
        by_pair = self.eval_by_pair(data)

        if self.by_frequency:
            by_frequency = self.eval_by_frequency(by_pair)

        if self.by_length:
            by_length = self.eval_by_length(by_pair)

        if self.by_pair:
            by_pair.drop(['frequency', 'length'], axis=1, inplace=True)
        else:
            by_pair = None

        return by_pair, by_frequency, by_length

    def eval(self, submission: SLM21Submission, dataset: SLM21Dataset):
        """ Run the selected lexical evaluations & write results """
        output_dir = submission.score_dir
        sets = submission.sets

        if 'dev' in sets:
            sub = submission.items.lexical_dev
            gold = dataset.index.subsets.lexical_dev.items.gold
            results = self.run_lexical_eval(sub, gold)

            for i, res in enumerate(results):
                if res is not None:
                    filename = output_dir / f"{self.result_filenames['dev'][i]}"
                    res.to_csv(filename, index=False, float_format='%.4f')

        if 'test' in sets:
            sub = submission.items.lexical_test
            data = dataset.index.subsets.lexical_test
            results = self.run_lexical_eval(sub, data)
            for i, res in enumerate(results):
                if res is not None:
                    filename = output_dir / f"{self.result_filenames['test'][i]}"
                    res.to_csv(filename, index=False, float_format='%.4f')
