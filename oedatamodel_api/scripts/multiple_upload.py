import os
import pathlib

import requests


MODEX_URL = "https://modex.rl-institut.de/upload_datapackage/"

CSVS = [
    "/home/local/RL-INSTITUT/hendrik.huyskens/Dokumente/RLI/oedatamodel_api/upload_data/ID19/oed_scalar.csv",
    "/home/local/RL-INSTITUT/hendrik.huyskens/Dokumente/RLI/oedatamodel_api/upload_data/ID19/datapackage.json"
]

TOKEN = os.environ["TOKEN"]


response = requests.post(
    MODEX_URL,
    data={"schema": "model_draft", "token": TOKEN},
    files=[
        ("datapackage_files", (pathlib.Path(file).name, open(file, "rb")))
        for file in CSVS
    ]
)
print(response)