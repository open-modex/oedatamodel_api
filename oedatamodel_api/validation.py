import csv
import logging
import os
import sys
import tempfile

from frictionless import FrictionlessException, Package, Report, validate_resource

from oedatamodel_api.settings import UPLOAD_FILEPATH

# Increase max cell size (in order to successfully load timeseries.series)
# avoid error: The data source has not supported or has inconsistent contents: field larger than field limit (131072)
csv.field_size_limit(sys.maxsize)

logger = logging.getLogger("uvicorn.error")


class DatapackageNotValid(Exception):
    """Exception is raised if datapackage is not valid"""


def create_and_validate_datapackage(datapackage_files):
    # Save and load datapackage into temporary folder:
    with tempfile.TemporaryDirectory(dir=UPLOAD_FILEPATH) as tempdir:
        for upload_file in datapackage_files:
            with open(
                os.path.join(tempdir, upload_file.filename), "wb+"
            ) as file_object:
                file_object.write(upload_file.file.read())
        logger.debug("Successfully extracted datapackage to temp folder")
        try:
            package = Package(f"{tempdir}/datapackage.json")
        except FrictionlessException as fe:
            raise DatapackageNotValid(str(fe)) from fe
        logger.debug("Successfully loaded datapackage")
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
