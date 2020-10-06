import csv
import zipfile
from enum import Enum
from io import BytesIO, StringIO


class OutputFormat(str, Enum):
    """Supplied output formats."""
    json = 'json'
    csv = 'csv'


def create_zip_csv(data):
    zipped_file = BytesIO()
    with zipfile.ZipFile(zipped_file, 'a', zipfile.ZIP_DEFLATED) as zipped:
        for name, data in data.items():
            csv_data = StringIO()
            writer = csv.writer(csv_data, delimiter=',')
            if isinstance(data, dict):
                writer.writerow(data.keys())
                writer.writerow(data.values())
            elif isinstance(data, list):
                writer.writerow(data[0].keys())
                for row in data:
                    writer.writerow(row.values())
            else:
                raise TypeError('Unknown type to create csv from')
            csv_data.seek(0)
            csv_buffer = csv_data.read()
            zipped.writestr(f'{name}.csv', csv_buffer)
    zipped_file.seek(0)
    return zipped_file
