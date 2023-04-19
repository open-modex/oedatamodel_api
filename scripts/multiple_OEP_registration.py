import os
import pathlib

import requests
from dotenv import load_dotenv


load_dotenv()


path = pathlib.Path("Path to metadata")

create_table_url = os.getenv("create_table_url")

JSONS = list(path.iterdir())

for file in JSONS:
    response = requests.post(
        create_table_url,
        data={
            "user": os.getenv("OEP_USER"),
            "token": os.getenv("TOKEN"),
        },
        files=[("metadata_file", (pathlib.Path(file).name, open(file, "rb")))],
    )
    print(response)
