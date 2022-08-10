import atexit
import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, AnyHttpUrl, parse_obj_as, validator, DirectoryPath, EmailStr


class ZerospeechBenchmarkSettings(BaseSettings):
    APP_DIR: Path = Path.home() / "zr-data"
    TMP_DIR: DirectoryPath = Path('/tmp')
    repo_origin: AnyHttpUrl = parse_obj_as(AnyHttpUrl, "https://download.zerospeech.com/repo.json")
    admin_email: EmailStr = parse_obj_as(EmailStr, "nicolas.hamilakis@ens.psl.eu")

    @validator('repo_origin', pre=True)
    def cast_url(cls, v):
        """ Cast strings to AnyHttpUrl """
        if isinstance(v, str):
            return parse_obj_as(AnyHttpUrl, v)
        return v

    @property
    def dataset_path(self) -> Path:
        return self.APP_DIR / "datasets"

    @property
    def repository_index(self) -> Path:
        return self.APP_DIR / 'repo.json'

    def mkdtemp(self) -> Path:
        tmp_loc = Path(tempfile.mkdtemp(prefix="zr", dir=self.TMP_DIR))

        def clean_tmp(d):
            shutil.rmtree(d)

        # create an auto-clean action
        atexit.register(clean_tmp, d=tmp_loc)

        return tmp_loc


@lru_cache()
def get_settings() -> ZerospeechBenchmarkSettings:
    """ Build & return global settings """
    env_file = os.environ.get('ZR_ENV', None)

    if env_file:
        return ZerospeechBenchmarkSettings(_env_file=env_file, _env_file_encoding='utf-8')
    return ZerospeechBenchmarkSettings()
