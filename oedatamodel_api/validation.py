import csv
import logging
import sys

from frictionless import FrictionlessException, Package, Report, validate_resource

# Increase max cell size (in order to successfully load timeseries.series)
# avoid error: The data source has not supported or has inconsistent contents: field larger than field limit (131072)
csv.field_size_limit(sys.maxsize)

logger = logging.getLogger("uvicorn.error")


class DatapackageNotValid(Exception):
    """Exception is raised if datapackage is not valid"""


def create_and_validate_datapackage(datapackage_path):
    try:
        package = Package(datapackage_path)
    except FrictionlessException as fe:
        raise DatapackageNotValid(str(fe)) from fe
    logger.debug("Successfully loaded datapackage")
    report = create_report(package)
    if not report.valid:
        raise DatapackageNotValid(report.to_dict())
    logger.info(f"Successfully validated datapackage '{package.name}'")
    return package


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
