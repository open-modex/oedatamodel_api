"""
Medati helps to format input data files and edits metadata.
"""

import json
from difflib import SequenceMatcher

import pandas
from omi.dialects.oep.dialect import OEP_V_1_5_Dialect
from omi.oem_structures.oem_v15 import OEPMetadata

OEDATAMODEL_COL_LIST = [
    "id",
    "region",
    "year",
    "timeindex_resolution",
    "timeindex_start",
    "timeindex_stop",
    "bandwidth_type",
    "version",
    "method",
    "source",
    "comment",
]

JSON_COL_LIST = [
    "bandwidth_type",
    "method",
    "source",
    "comment",
]


class Medati:
    """
    The class helps prepare data and metadata files for upload to the OpenEnergyPlatform.


    Methods
    -------

    _return_user_defined_columns(self) -> dict
        return user defined columns that are neither columns of oedatamodel-parameter scalar nor timeseries
    create_json_dict_from_user_defined_columns(self) -> dict
        read columns and return dict with column names as keys and empty value
    insert_user_column_dict_in_csv_based_on_oedatamodel_parameter(self) -> None
        insert each csv specific column dicts in respective csv
    make_csv_columns_postgresql_conform(self) -> dict
        correct columns from csv files to be postgresql-conform and save in csv
    update_oemetadata_schema_fields_name_from_csv_using_similarity(self) -> None
        update metadata information with actual csv column-header information and write into respective metadata json

    """

    def __init__(self, dataframe: pandas.DataFrame = None, metadata: dict = None):
        """
        Init medati class

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Specify csv file
        metadata : dict
            Specify metadata json

        Raises
        ------
        TypeError
            if dataframe or metadata has wrong type
        """

        # define paths for csv and oeo_annotation folder
        if isinstance(dataframe, pandas.DataFrame):
            self.dataframe = dataframe
        else:
            raise TypeError("'dataframe' has to be type: pd.DataFrame")
        if isinstance(metadata, dict):
            self.metadata = metadata
        else:
            raise TypeError("'metadata' has to be type: dict")

    def _return_user_defined_columns(self) -> dict:
        """
        Return user-defined columns that are neither columns of oedatamodel-parameter scalar nor timeseries.

        Returns
        -------
        dict
            Key -> filename: str ; Value -> set of user_defined_columns
        """

        return {
            "custom_columns": (
                set(self.dataframe.columns.tolist()) - set(OEDATAMODEL_COL_LIST)
            )
        }

    def create_json_dict_from_user_defined_columns(self) -> dict:
        """
        Read columns and return dict with column names as keys and empty value.

        Returns
        -------
        dict
            Key -> filename; Value -> dict of user_defined_columns
        """
        user_defined_cols_dict = self._return_user_defined_columns()

        json_dict_user_col = {}
        for df_name, user_cols in user_defined_cols_dict.items():
            csv_dict = {user_col: "" for user_col in user_cols}
            json_dict_user_col[df_name] = csv_dict

        return json_dict_user_col

    def insert_user_column_dict_in_csv_based_on_oedatamodel_parameter(self) -> None:
        """
        Insert each csv-specific column dicts in respective csv.
        """
        json_dict_user_col = self.create_json_dict_from_user_defined_columns()

        for column in JSON_COL_LIST:
            self.dataframe[f"{column}"] = f"{json_dict_user_col['custom_columns']}"

    def make_csv_columns_postgresql_conform(self):
        """
        Correct columns from csv files to be postgresql conform and save in csv.
        """

        # column header lowercase
        self.dataframe.columns = self.dataframe.columns.str.strip().str.lower()

        # remove postgresql incompatible characters from csv col-header
        postgresql_conform_to_replace = {
            "/": "_",
            "\\": "_",
            " ": "_",
            "-": "_",
            ":": "_",
            ",": "_",
            ".": "_",
            "+": "_",
            "%": "_",
            "!": "_",
            "?": "_",
            "(": "_",
            ")": "_",
            "[": "_",
            "]": "_",
            "}": "_",
            "{": "_",
            "ß": "ss",
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
        }

        for key, value in postgresql_conform_to_replace.items():
            self.dataframe.columns = [
                col.replace(key, value) for col in self.dataframe.columns
            ]

    def update_oemetadata_schema_fields_name_from_csv_using_similarity(self) -> dict:
        """
        Update metadata information with actual csv column-header information and write into respective metadata json.

        Returns
        -------
        dict
            Adapted metadata

        Raises
        ------
        Exception
            if something is wrong in metadata
        """

        # make column header postgresql conform
        self.make_csv_columns_postgresql_conform()

        csv_column_header = self.dataframe.columns

        metadata_user = self.metadata

        # omi
        # metadata 1.5 instance and parse metadata_user in python dict
        dialect1_5 = OEP_V_1_5_Dialect()
        # parse metadata_user in python dict
        parsed: OEPMetadata = dialect1_5._parser().parse(  # pylint: disable=W0212
            metadata_user
        )

        # similarity isn't case-agnostic. field.name.lower() -> to enable string comparison on lowercase
        for ressource in parsed.resources:
            for field in ressource.schema.fields:
                try:
                    field.name = self._similar(csv_column_header, field.name.lower())
                except Exception as exc:
                    raise Exception(
                        f"There is a problem in metadata file: {metadata_user['name']}. "
                        f"The metadata key `name` is: {field.name}"
                    ) from exc

        metadata = dialect1_5.compile_and_render(parsed)
        metadata = json.loads(metadata)

        self.metadata = metadata

        return metadata

    @staticmethod
    def _similar(csv_column_header: list, metadata_key: str) -> str:
        """
        Check the similarity of metadata and new postgresql-conform column headers and match them. Return the
        postgresql-conform column name.

        Parameters
        ----------
        csv_column_header: list
            CSV column headers, after postgresql-conform correction
        metadata_key: str
            metadata column key from metadata file

        Returns
        -------
        str
            postgresql-conform column name

        Raises
        ------
        ValueError
            if metadata key has no similarity with dataframe columns
        """
        similarity_criteria = 0.8
        sim_dict = {}
        for csv_header in csv_column_header:
            sim_value = SequenceMatcher(None, csv_header, metadata_key).ratio()
            sim_dict[(csv_header, metadata_key)] = sim_value
            if sim_value == 1:
                break

        if max(sim_dict.values()) >= similarity_criteria:
            return max(sim_dict, key=sim_dict.get)[0]

        raise ValueError(
            f"Your metadata column name: {metadata_key} - has no similarity with the postgresql-conform "
            f"corrected csv column headers {csv_column_header}\n"
            f"Postgresql-conform corrected csv column headers cannot be inserted into metadata, due to missing "
            f"match, please check manually if the column is present in your metadata.\n"
            f"Similarity below {similarity_criteria}: {sim_dict}"
        )
