import json

from .settings import get_settings
from .out import console, error_console
from .datasets import RepositoryIndex

import requests
from pydantic import ValidationError

st = get_settings()


def update_repo_index():
    """ Updates the repositories index """
    r = requests.get(st.repo_origin)
    data = r.json()
    try:
        _ = RepositoryIndex(**data)
    except ValidationError:
        error_console.log(f"The given repository @ {st.repository_index} is not valid")
        error_console.log(f"Please contact the administrator to resolve this issue...")

    with st.repository_index.open('w') as fp:
        json.dump(data, fp)
        console.log("RepositoryIndex has been updated successfully !!")

