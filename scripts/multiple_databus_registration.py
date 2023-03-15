import os
import pathlib

import environ_setup

import requests

MODEX_URL = "https://modex.rl-institut.de/databus/"

path = pathlib.Path(
    "/home/local/RL-INSTITUT/felix.maurer/rli/Felix.Maurer/SEDOS/Python/data_adapter_oemof/tests/_files/tabular_datapackage_mininmal_example_collection/csvs"
)

CSVS = list(path.iterdir())

account = os.environ["account_name"]
api_key = os.environ["API_KEY"]
group = os.environ["group"]
version = os.environ["version"]

for file in CSVS:
    response = requests.post(
        MODEX_URL,
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
