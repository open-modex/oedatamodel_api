import json
from collections import namedtuple

import pandas as pd

from oedatamodel_api.settings import APP_DIR

Link = namedtuple("Link", ("source", "target", "value"))


STRUCTURE_FILE = APP_DIR / "structure" / "structure.csv"

Sector = namedtuple("Sector", ("name", "color"))

SECTORS = {
    "pow": Sector("Electricity", "#FFFF00"),
    "ind": Sector("Industry", "#ED7D31"),
    "hea": Sector("Heat", "#EE0056"),
    "x2x": Sector("X2X", "#ED7DD7"),
    "mob": Sector("Mobility", "#9CD4C3"),
}


def get_energy_structure():
    process_parameter_in_out = pd.read_csv(
        filepath_or_buffer=STRUCTURE_FILE,
        delimiter=";",
        encoding="utf-8",
        usecols=["parameter", "process", "inputs", "outputs"],
    )

    # create ES_STRUCTURE dict from process_parameter_in_out
    list_dic = process_parameter_in_out.to_dict(orient="records")

    es_structure = {}

    for dic in list_dic:
        dic_para = {}

        if isinstance(dic.get("inputs"), str):
            inputs = {"inputs": dic.get("inputs").replace(" ", "").split(",")}
        else:
            inputs = {"inputs": []}
        if isinstance(dic.get("outputs"), str):
            outputs = {"outputs": dic.get("outputs").replace(" ", "").split(",")}
        else:
            outputs = {"outputs": []}

        dic_para[dic.get("parameter")] = inputs | outputs

        if dic.get("process") not in es_structure:
            es_structure[dic.get("process")] = dic_para
        else:
            es_structure[dic.get("process")] = (
                es_structure[dic.get("process")] | dic_para
            )

    return es_structure


def create_structure_chart_options(structure: dict) -> dict:
    base_structure_options_filename = APP_DIR / "structure" / "structure.json"
    with base_structure_options_filename.open(
        "r", encoding="utf-8"
    ) as base_structure_options_file:
        structure_options = json.load(base_structure_options_file)

    # Create processes and busses:
    processes = list(structure)
    busses = []
    links = []
    for process, parameters in structure.items():
        for parameter, in_out in parameters.items():
            links += [
                {
                    "label": {
                        "formatter": "{c}" if parameter != "default" else "",
                        "show": True,
                    },
                    "source": input_,
                    "target": process,
                    "value": parameter,
                }
                for input_ in in_out["inputs"]
            ]
            links += [
                {
                    "label": {
                        "formatter": "{c}" if parameter != "default" else "",
                        "show": True,
                    },
                    "source": process,
                    "target": input_,
                    "value": parameter,
                }
                for input_ in in_out["outputs"]
            ]
            busses += in_out["inputs"]
            busses += in_out["outputs"]
    busses = list(set(busses))
    structure_options["series"][0]["data"] = [
        {"name": process, "itemStyle": {"color": get_process_color(process)}}
        for process in processes
    ]
    structure_options["series"][0]["data"] += [{"name": item} for item in busses]
    structure_options["series"][0]["links"] = links
    return structure_options


def get_process_color(process: str) -> str:
    sector_name = process[:3]
    if sector_name not in SECTORS:
        return "grey"
    return SECTORS[sector_name].color
