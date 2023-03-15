import os
import pathlib

import environ_setup
import requests

environ_setup.setup()

MODEX_URL = "https://modex.rl-institut.de/upload/"

path = pathlib.Path(
    "/home/local/RL-INSTITUT/felix.maurer/rli/Felix.Maurer/SEDOS/Python/data_adapter_oemof/tests/"
    "_files/tabular_datapackage_mininmal_example_collection/csvs"
)

CSVS = list(path.iterdir())

TOKEN = os.environ["TOKEN"]


for file in CSVS:
    response = requests.post(
        MODEX_URL,
        data={
            "schema": "model_draft",
            "token": TOKEN,
            "table": pathlib.Path(file).name.split(".")[0],
        },
        files=[("csv_file", (pathlib.Path(file).name, open(file, "rb")))],
    )
    print(response)
