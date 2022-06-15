import csv
import json
import pathlib
import zipfile
from enum import Enum
from io import BytesIO, StringIO

from fastapi import HTTPException
from fastapi.responses import StreamingResponse


class OutputFormat(str, Enum):
    """Supplied output formats."""

    json = "json"
    csv = "csv"


def format_data(data, output_format):
    if output_format == OutputFormat.json:
        return data
    elif output_format == OutputFormat.csv:
        if isinstance(data, dict):
            return create_zip_csv(data)
        elif isinstance(data, list) or not all(
            isinstance(v, (dict, list)) for v in data.values()
        ):
            return create_csv(data)
    else:
        raise HTTPException(
            status_code=404, detail=f"Unknown output format '{output_format}'."
        )


def create_zip_csv(json_data):
    zipped_file = BytesIO()
    root_dir = pathlib.Path()
    with zipfile.ZipFile(zipped_file, "a", zipfile.ZIP_DEFLATED) as zipped:
        __iterate_zip_dirs(zipped, json_data, root_dir)
    zipped_file.seek(0)
    response = StreamingResponse(zipped_file, media_type="application/x-zip-compressed")
    response.headers["Content-Disposition"] = "attachment; filename=scenario.zip"
    return response


def create_csv(json_data):
    csv_file = __write_csv(json_data)
    csv_file.seek(0)
    response = StreamingResponse(csv_file, media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=scenario.csv"
    return response


def __iterate_zip_dirs(zipped, json_data, current_dir):
    for name, data in json_data.items():
        # Check if current node is directory or data for csv:
        if isinstance(data, list) or not all(
            isinstance(v, (dict, list)) for v in data.values()
        ):
            csv_data = __write_csv(data)
            csv_data.seek(0)
            csv_buffer = csv_data.read()
            if current_dir == pathlib.Path():
                zipped.writestr(f"{name}.csv", csv_buffer)
            else:
                zipped.writestr(f"{current_dir}/{name}.csv", csv_buffer)
        else:
            __iterate_zip_dirs(zipped, data, current_dir / name)


def __write_csv(data):
    csv_data = StringIO()
    writer = csv.writer(
        csv_data, delimiter=";", quotechar="'", quoting=csv.QUOTE_MINIMAL
    )
    if isinstance(data, dict):
        writer.writerow(data.keys())
        writer.writerow(map(json.dumps, data.values()))
    elif isinstance(data, list):
        if data and isinstance(data[0], dict):
            writer.writerow(data[0].keys())
            for row in data:
                writer.writerow(map(json.dumps, row.values()))
        else:
            for value in data:
                writer.writerow([json.dumps(value)])
    else:
        raise TypeError("Unknown type to create csv from")
    return csv_data
