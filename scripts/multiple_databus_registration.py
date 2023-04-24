import os
import pathlib
from dotenv import load_dotenv
import requests

load_dotenv()


def multiple_databus_registration(
    path: str,
    account: str = None,
    api_key: str = None,
    group: str = None,
    version: str = None,
    databus_url: str = "https://modex.rl-institut.de/databus/",
):
    path = pathlib.Path("Path to CSVs")
    CSVS = list(path.iterdir())

    if not account:
        account = os.getenv("account")
    if not api_key:
        api_key = os.getenv("api_key")
    if not group:
        group = os.getenv("group")
    if not version:
        version = os.getenv("version")

    for file in CSVS:
        response = requests.post(
            databus_url,
            data={
                "schema": "model_draft",
                "account": account,
                "api_key": api_key,
                "group": group,
                "table": pathlib.Path(file).name.split(".")[0],
                "version": version,
            },
        )
        print(response)
