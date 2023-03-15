import os
import pathlib

import environ_setup

import requests

MODEX_URL = "https://modex.rl-institut.de/create_table/"

path = pathlib.Path(
    "/home/local/RL-INSTITUT/felix.maurer/rli/Felix.Maurer/SEDOS/Python/data_adapter_oemof/tests/"
    "_files/tabular_datapackage_mininmal_example_collection/json"
)

JSONS = list(path.iterdir())

account = os.environ["account_name"]
api_key = os.environ["API_KEY"]
group = os.environ["group"]
version = os.environ["version"]

for file in JSONS:
    response = requests.post(
        MODEX_URL,
        data={
            "user": os.environ["OEP_USER"],
            "token": os.environ["TOKEN"],
        },
        files=[("metadata_file", (pathlib.Path(file).name, open(file, "rb")))],
    )
    print(response)
