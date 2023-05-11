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


def create_structure_chart_options(
    structure: dict, sector: str = None, bus: str = None
) -> dict:
    """
    Create chart options from structure. Filtering by sector or bus is possible

    Parameters
    ----------
    structure: dict
        ES structure (used in SEDOS data_adapter)
    sector: str
        Filter for processes used in given sector
    bus: str
        Filter energy structure by given bus

    Returns
    -------
    dict
        Options dict used by echarts
    """
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
        show_process = bus is None  # If bus is None, processes are not filtered
        if sector and process[:3] != sector:
            continue
        for parameter, in_out in parameters.items():
            for input_ in in_out["inputs"]:
                if bus and input_ != bus:
                    continue
                links.append(
                    {
                        "label": {
                            "formatter": "{c}" if parameter != "default" else "",
                            "show": True,
                        },
                        "source": input_,
                        "target": process,
                        "value": parameter,
                    }
                )
                busses.append(input_)
                show_process = True  # Show process if at least one bus (input or output) is connected
            for output in in_out["outputs"]:
                if bus and output != bus:
                    continue
                links.append(
                    {
                        "label": {
                            "formatter": "{c}" if parameter != "default" else "",
                            "show": True,
                        },
                        "source": process,
                        "target": output,
                        "value": parameter,
                    }
                )
                busses.append(output)
                show_process = True  # Show process if at least one bus (input or output) is connected

        if not show_process:
            processes.remove(process)

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
