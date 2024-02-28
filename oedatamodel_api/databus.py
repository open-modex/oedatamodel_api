import logging
from typing import Optional
from urllib.parse import quote

import databusclient
import requests

from oedatamodel_api.settings import DATABUS_URI_BASE, MOSS_URL, OEP_URL

logger = logging.getLogger("uvicorn")


class MetadataError(Exception):
    """Raised if metadata is invalid"""


class DeployError(Exception):
    """Raised if deploy fails"""


class MossError(Exception):
    """Raised if submitting metadata to MOSS fails"""


def get_table_meta(schema: str, table: str):
    """
    Requests metadata from OEP

    Parameters
    ----------
    schema: str
        OEP schema to get table from
    table: str
        OEP table to get metadata

    Returns
    -------
    metadata: dict
        Metadata of given OEP table

    Raises
    ------
    MetadataError
        Raised if either request fails, metadata is empty or required fields are empty
    """

    meta_url = f"{OEP_URL}/api/v0/schema/{schema}/tables/{table}/meta"
    response = requests.get(meta_url)
    if response.status_code != 200:
        raise MetadataError(f"Could not request metadata for table '{schema}.{table}'.")
    metadata = response.json()

    if len(metadata) == 0:
        raise MetadataError(f"Metadata for table '{schema}.{table}' is empty.")

    abstract = metadata.get("context", {}).get("documentation", "")
    if not abstract:
        raise MetadataError(f"Abstract for table '{schema}.{table}' is empty.")

    try:
        license_ = metadata["licenses"][0]["path"]
    except (IndexError, KeyError):
        license_ = None
    if not license_:
        raise MetadataError(f"No license found for for table '{schema}.{table}'.")

    return metadata


def register_oep_table(
    schema_name: str,
    table_name: str,
    group: str,
    account_name: str,
    api_key: str,
    version: str,
):
    """
    Registers OEP table on DataBus and MOSS

    Parameters
    ----------
    schema_name: str
        OEP schema where table is found
    table_name: str
        OEP table to register on databus
    group: str
        Databus group to deploy to
    account_name: str
        Databus account name
    api_key: str
        Databus API key
    version: str
        defines for which version table is filtered and registered

    Returns
    -------
    databus_identifier: str
        Databus ID
    """
    logger.info(
        f"Registering table '{schema_name}.{table_name}' in group '{account_name}/{group}' "
        f"with {version=}"
    )
    metadata = get_table_meta(schema_name, table_name)
    abstract = metadata["context"]["documentation"]
    license_ = metadata["licenses"][0]["path"]

    data_url = f"{OEP_URL}/api/v0/schema/{schema_name}/tables/{table_name}/rows?form=csv&where=version={version}"
    metadata_url = f"{OEP_URL}/api/v0/schema/{schema_name}/tables/{table_name}/meta/"

    distributions = [
        databusclient.create_distribution(
            url=data_url,
            cvs={"type": "data"},
            file_format="csv",
        ),
        databusclient.create_distribution(
            url=metadata_url,
            cvs={"type": "metadata"},
            file_format="json",
        ),
    ]

    version_id = get_databus_identifier(account_name, group, table_name, version)
    dataset = databusclient.create_dataset(
        version_id,
        title=metadata["title"],
        abstract=abstract,
        description=metadata.get("description", ""),
        license_url=license_,
        distributions=distributions,
    )

    try:
        databusclient.deploy(dataset, api_key)
    except databusclient.client.DeployError as de:
        raise DeployError(str(de))

    return version_id


def submit_metadata_to_moss(databus_identifier, metadata):
    """
    Submits metadata from DataBus artifact to MOSS

    Parameters
    ----------
    databus_identifier: str
        Databus ID to set up metadata on MOSS
    metadata: dict
        Metadata which shall be connected with databus ID

    Raises
    ------
    MossError
        if metadata cannot be submitted to MOSS
    """
    # generate the URI for the request with the encoded identifier
    api_uri = f"{MOSS_URL}?id={quote(databus_identifier)}"
    response = requests.put(
        api_uri, headers={"Content-Type": "application/ld+json"}, json=metadata
    )
    if response.status_code != 200:
        raise MossError(
            f"Could not submit metadata for DI '{databus_identifier}' to MOSS. "
            f"Reason: {response.text}"
        )


def get_databus_identifier(
    account_name: str, group: str, artifact_name: str, version: Optional[str] = None
):
    identifier = f"{DATABUS_URI_BASE}/{account_name}/{group}/{artifact_name}"
    if version:
        identifier += f"/{version}"
    return identifier


def check_if_artifact_exists(identifier: str):
    response = requests.get(identifier)
    if response.status_code == 200:
        return True
    return False
