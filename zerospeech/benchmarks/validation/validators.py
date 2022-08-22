from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from .generics import ValidationOK, ValidationError, ValidationResponse
from ...data_items import FileListItem, FileItem, FileTypes
from ...data_loaders import load_dataframe


def list_checker(given: List[str], expected: List[str]):
    """ Check a list of strings to find if expected items are in it """
    given = set(given)
    expected = set(expected)

    if given != expected:
        has_less_files = expected - given
        has_more_files = given - expected

        if len(has_more_files) > 0:
            return [ValidationError(
                "more files found",
                data=has_more_files
            )]

        if len(has_less_files) > 0:
            return [ValidationError(
                "missing files",
                data=has_less_files
            )]
    else:
        return [ValidationOK('expected files found')]


def file_list_checker(item: FileListItem, expected: List[Path]) -> List[ValidationResponse]:
    """ Check if a file list has expected files in it """
    file_names = [f.stem for f in item.files_list]
    expected_names = [f.stem for f in expected]
    return list_checker(file_names, expected_names)


return_type = Tuple[List[ValidationResponse], Optional[pd.DataFrame]]


def dataframe_check(item: FileItem, expected_columns: Optional[List[str]] = None, **kwargs) -> return_type:
    if item.file_type not in FileTypes.dataframe_types():
        return [ValidationError(f'file type {item.file_type} cannot be converted into a dataframe',
                                data=item.file)], None

    try:
        df = load_dataframe(item, **kwargs)
    except Exception as e:  # noqa: broad exception is on purpose
        return [ValidationError(f'{e}', data=item.file)], None

    columns = list(df.columns)

    if columns != expected_columns:
        return [ValidationError(f'columns are not expected '
                                f'expected: {expected_columns}, found: {columns}')], None

    return [ValidationOK('dataframe validates tests')], df
