
import logging
import requests

OEP_URL = 'https://openenergy-platform.org'


class ScenarioNotFoundError(Exception):
    """Is raised if scenario could not be found in OEP"""


def get_scenario_from_oep(scenario_id=None, scenario_name=None):
    if scenario_id is None and scenario_name is None:
        raise ValueError("You have to set either scenario ID or name")
    if scenario_id is not None and scenario_name is not None:
        raise ValueError("Scenario name and ID given.")
    if scenario_id is not None:
        where_clause = {
            "operands": [
                {
                    "type": "column",
                    "table": "s",
                    "column": "id",
                },
                scenario_id,
            ],
            "operator": "=",
            "type": "operator",
        }
    else:
        where_clause = {
            "operands": [
                {
                    "type": "column",
                    "table": "s",
                    "column": "scenario",
                },
                scenario_name,
            ],
            "operator": "=",
            "type": "operator",
        }
    join = {
        "from": {
            "type": "join",
            "left": {
                "type": "table",
                "table": "oed_scenario",
                "schema": "model_draft",
                "alias": "s",
            },
            "right": {
                "type": "join",
                "is_full": True,
                "left": {
                    "type": "join",
                    "is_full": True,
                    "left": {
                        "type": "table",
                        "table": "oed_data",
                        "schema": "model_draft",
                        "alias": "d",
                    },
                    "right": {
                        "type": "table",
                        "table": "oed_timeseries",
                        "schema": "model_draft",
                        "alias": "ts",
                    },
                    "on": {
                        "operands": [
                            {"type": "column", "column": "id", "table": "d"},
                            {"type": "column", "column": "id", "table": "ts"},
                        ],
                        "operator": "=",
                        "type": "operator",
                    },
                },
                "right": {
                    "type": "table",
                    "table": "oed_scalar",
                    "schema": "model_draft",
                    "alias": "sc",
                },
                "on": {
                    "operands": [
                        {"type": "column", "column": "id", "table": "d"},
                        {"type": "column", "column": "id", "table": "sc"},
                    ],
                    "operator": "=",
                    "type": "operator",
                },
            },
            "on": {
                "operands": [
                    {"type": "column", "column": "id", "table": "s"},
                    {"type": "column", "column": "scenario_id", "table": "d"},
                ],
                "operator": "=",
                "type": "operator",
            },
        },
        "where": where_clause,
    }
    data = {'query': join}
    response = requests.post(
        OEP_URL + '/api/v0/advanced/search',
        json=data,
    )
    if response.status_code != 200:
        logging.error("Error in scenario request to OEP", scenario_id, scenario_name, response.text)
        raise ConnectionError(response.text)
    json = response.json()
    if json["content"]["rowcount"] == 0:
        logging.warning("Could not get scenario from OEP", scenario_id, scenario_name, response.text)
        raise ScenarioNotFoundError("Scenario not found", scenario_id, scenario_name)
    return json
