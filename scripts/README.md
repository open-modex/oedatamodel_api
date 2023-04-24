## Scripts to work with OEP and "Databus" API

### Purpose
The scripts found in this folder can be used to "Upload" or "Register Data" to the [OEP](https://openenergy-platform.org/)
or register data on the ["Databus"](https://energy.databus.dbpedia.org/). They can be especially handy when dealing with multiple datasets.

### Getting started
- Clone the repository to your machine.
- Create an environment (or use an existing one) with the necessary packages:
  - `python-dotenv`
  - `requests`
- Rename `env_template` to `.env`.
- Write your credentials and settings to the `.env` file.
- For each script, enter the folder where the files that shall be processed are located and write your file stream.

### [OEP](https://openenergy-platform.org/) Dataset Registration
- Script: `multiple_oep_registration.py`
- Purpose: Registers multiple .json Metadata files on the [OEP](https://openenergy-platform.org/).

To use the script, you must have an API key and user account at OEP.
The script is working correctly if your console is printing out `Response 200`.

Please note that the same or different "OEMetadata" can be registered multiple times, and the API may return `Response 200` even though there are issues with the data. This may happen if existing "OEMetadata" with already uploaded data is overwritten with new "OEMetadata" information, such as a changed datatype. To change the datatype of a column, the dataset should be deleted first.

For a further understanding of what the script does, you may refer to the [API](https://modex.rl-institut.de/create_table/) with your browser.

### [OEP](https://openenergy-platform.org/) Dataset Upload
- Script: `multiple_csv_upload.py`
- Purpose: Uploads multiple datasets to existing Metadata on the [OEP](https://openenergy-platform.org/).

To use the script, you must have an API key and user account at OEP. The names (and schema) of the csv files should be corresponding to the names used within the "OEMetadatafiles" resource as name:

``
 "resources": ["name": "model_draft.file_name" ....
``

In this example, the schema is `model_draft`, and the name of the file to be uploaded is `file_name.csv`. The script is working correctly if your console is printing out `Response 200`.

Please note that after the first successful run of the script, the data will have been uploaded to the OEP, and the same data cannot be uploaded again. You may adjust the `primary key` column, i.e., `ID`, and the `version` to re-upload.

For a further understanding of what the script does, you may refer to the [API](https://modex.rl-institut.de/upload/) with your browser.

### ["Databus"](https://energy.databus.dbpedia.org/) Dataset Upload
- Skript: multiple_databus_upload.py
- Purpose: Upload multiple Datasets to existing resources on the ["Databus"](https://energy.databus.dbpedia.org/)

This script uses the csv file folder again to read all Datasets that are to be uploaded onto the ["Databus"](https://energy.databus.dbpedia.org/).
The group name for the ["Databus"](https://energy.databus.dbpedia.org/) and the version (from the version column) has to be given in the `.env` file
The script has been working correctly if your console is printing out `Response 200`

Please note that after the first successful run the data will have been uploaded to the ["Databus"](https://energy.databus.dbpedia.org/) and the same data cannot be uploaded again. You may adjust the `primary key` column, i.e. `ID`, and the `version` to re-upload.

For further understanding of what the script does you may refer to the [API](https://modex.rl-institut.de/upload/) with your browser.
