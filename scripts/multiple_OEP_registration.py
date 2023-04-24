import os
import pathlib

import requests
from dotenv import load_dotenv


load_dotenv()


def multiple_OEP_registration(
    path: str,
    create_table_url: str = "https://modex.rl-institut.de/create_table/",
    TOKEN: str = None,
    USER: str = None,
):
    path = pathlib.Path("Path to metadata")
    create_table_url = os.getenv("create_table_url")
    JSONS = list(path.iterdir())

    if not TOKEN:
        TOKEN = os.getenv("TOKEN")
    if not USER:
        USER = os.getenv("OEP_USER")

    for file in JSONS:
        response = requests.post(
            create_table_url,
            data={"user": USER, "token": TOKEN},
            files=[("metadata_file", (pathlib.Path(file).name, open(file, "rb")))],
        )
        print(response)
