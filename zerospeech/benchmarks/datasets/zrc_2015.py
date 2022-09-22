import functools
from typing import Optional

from ...model import m_datasets


class ZRC2015Dataset(m_datasets.Dataset):
    """ Class interfacing usage of the ZRC 2019 test dataset """

    @classmethod
    @functools.lru_cache
    def load(cls, load_index: bool = True) -> Optional["ZRC2015Dataset"]:
        """ Loads the dataset """
        dataset = m_datasets.DatasetsDir.load().get("zrc2015-dataset", cls=cls)

        if dataset is None:
            raise m_datasets.DatasetNotFoundError(f"The zrc2015-dataset does not exist")

        if not dataset.installed:
            raise m_datasets.DatasetNotInstalledError("The zrc2015-dataset is not installed locally")

        if load_index:
            dataset.load_index()
            # convert all paths to absolute paths
            dataset.index.make_absolute()

        return dataset
