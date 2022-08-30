import abc
from typing import Optional

from pydantic import BaseModel, DirectoryPath

from .leaderboard import LeaderboardEntry, PublicationEntry
from .meta_file import MetaFile


class ScoreDir(BaseModel, abc.ABC):
    location: DirectoryPath
    meta_file: Optional[MetaFile] = None

    @abc.abstractmethod
    def build_leaderboard(self) -> LeaderboardEntry:
        pass

    def get_publication_info(self) -> PublicationEntry:
        """ Build publication info """
        if self.meta_file is None:
            return PublicationEntry(
                institution=""
            )
        return self.meta_file.get_publication_info()
