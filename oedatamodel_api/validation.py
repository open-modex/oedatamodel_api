
import os
import sys
import csv
import logging
from frictionless import Package, validate_resource, Report, FrictionlessException

from oedatamodel_api.settings import ZIP_UPLOAD_FILEPATH

# Increase max cell size (in order to successfully load timeseries.series)
# avoid error: The data source has not supported or has inconsistent contents: field larger than field limit (131072)
csv.field_size_limit(sys.maxsize)

logger = logging.getLogger("uvicorn.error")


class DatapackageNotValid(Exception):
    """Exception is raised if datapackage is not valid"""


def create_and_validate_datapackage(zip_file):
    # Save and load zip datapackage (remove saved zipfile afterwards)
    with open(ZIP_UPLOAD_FILEPATH, "wb+") as file_object:
        file_object.write(zip_file.file.read())
    logger.debug("Successfully unzipped datapackage to temp folder")
    try:
        package = Package.from_zip(ZIP_UPLOAD_FILEPATH)
    except FrictionlessException as fe:
        raise DatapackageNotValid(str(fe))
    logger.debug("Successfully loaded datapackage")
    os.remove(ZIP_UPLOAD_FILEPATH)
    report = create_report(package)
    if report.valid:
        return package
    else:
        raise DatapackageNotValid(report.to_dict())


def create_report(package):
    tasks = []
    errors = []
    for resource in package.resources:
        logger.debug(f"Validating resource '{resource.name}'...")
        report = validate_resource(resource)
        logger.debug(f"Successfully validated resource '{resource.name}'")
        tasks.extend(report.tasks)
        errors.extend(report.errors)
    return Report(errors=errors, tasks=tasks)
