## Skripts to work with OEP and Databus API

### Purpose
The Scripts found in this folder can be used to Upload or Register Data to the [OEP](https://openenergy-platform.org/)
or Register Data on the [Databus](https://energy.databus.dbpedia.org/)
They can be especially handy if multiple Datasets are to be handled.

### Getting startet
- Clone Repository to your Machine
- Create environment (or use existing) with necessary packages:
  - `python-dotenv`
  - `requests`
- Rename `env_template` to `.env`
- Write your credentials and settings to `.env` file
- For each skript enter the folder where the files that shall be processed are located
write own filestream

###  [OEP](https://openenergy-platform.org/) Dataset Registration
- Skript: multiple_databus_registration.py
- Purpose: Registers multiple .json Metadata-files on the [OEP](https://openenergy-platform.org/)

To use the script, you must have an API key and user account at OEP.
The Skript has been working correctly if your console is printing out `Response 200`

Please not that the same or different Metadata can be registered multiple times and the API may return `Response 200` even though there are issues on the Data. This may happen if existing Metadata with already uploaded Data is overwritten with new Metadata information such as a changed Datatype. To change the Datatype of a column the Dataset should be deleted first.

For Further understanding of what the skipt does you may reffer to the [API](https://modex.rl-institut.de/create_table/) with your Browser

###  [OEP](https://openenergy-platform.org/) Dataset Upload
- Skript: multiple_csv_upload.py
- Purpose: Upload multiple Datasets to existing Metadata on the [OEP](https://openenergy-platform.org/)

To use the script, you must have an API key and user account at OEP. The names (and shema) of the csv files should be
corresponding to the names used within the Metadatafiles resource as name:

``
 "resources": ["name": "model_draft.file_name" ....
``

In this example the shema is `model_draft` and the name of the file that is to be uploaded is `file_name.csv`
The Skript has been working correctly if your console is printing out `Response 200`

Please note that after the first successful run of the skript the data will be have been uploaded to the OEP and the same Data cannot be Uploaded again. You may adjust the `primary key` column i.e. `ID` and the `version` to reupload.

For Further understanding of what the skipt does you may reffer to the [API](https://modex.rl-institut.de/upload/) with your Browser

### [Databus](https://energy.databus.dbpedia.org/) registration
- Skript: multiple_databus_registration.py
- Purpose: Register multiple datasets from the [OEP](https://openenergy-platform.org/) onto the [Databus](https://energy.databus.dbpedia.org/)

This skript uses the csv file folder again to read all Datasets that are to be registered onto the [Databus](https://energy.databus.dbpedia.org/).
The Group name for the [Databus](https://energy.databus.dbpedia.org/) and the Version (from version collumn) has to be given in the `.env` File
The Skript has been working correctly if your console is printing out `Response 200`

Please note that after the first successful run the Data will be registered on the Databus and the same Data (same version) can not be registered again.

For Further understanding of what the skipt does you may reffer to the [API](https://modex.rl-institut.de/databus/) with your Browser
