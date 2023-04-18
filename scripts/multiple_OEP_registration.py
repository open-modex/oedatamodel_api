import os
import pathlib

import requests
from dotenv import load_dotenv


environ_setup.setup()


path = pathlib.Path(
    "Path to folder with metadata"
)

create_table_url = os.getenv("create_table_url")

JSONS = list(path.iterdir())

for file in JSONS:
    response = requests.post(
        create_table_url,
        data={
            "user": os.environ["OEP_USER"],
            "token": os.environ["TOKEN"],
        },
        files=[("metadata_file", (pathlib.Path(file).name, open(file, "rb")))],
    )
    print(response)
