# API to connect OEP with MODEX frameworks

This API works as a connector between the OEP and energy system modelling frameworks from MODEX project.
Scenario data stored in the OEP can be requested by the API and will be parsed and provided for requesting framework.

# Get started (from scratch)

### Setup Python

Ideally you install the oedatamodel_api on a (Linux) Ubuntu 18.04 machine or you have a virtual machine like Oracle VirtualBox installed where you can set up a new Ubuntu 18.04 machine.

We assume that you are using a Python version >= Python3.8. You can check the Python version by opening a terminal and typing the following: 
```
$ python --version
``` 

If you need to install or upgrade Python on your machine, you can use these steps to build Python from source and not affect other Python versions that are already installed:

- Open a terminal:
```
sudo apt update
$ sudo apt upgrade
$ sudo apt dist-upgrade
$ sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev liblzma-dev wget
```

- Now create a temporary directory and download the python source code:

```
$ mkdir ~/tmp
$ cd ~/tmp
$ wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tgz
```

After downloading the package, run the commands below to extract the file and configure the python:

```
$ tar -xvzf Python-3.9.0.tgz
$ cd Python-3.9.0
$ ./configure
```

- install the python:

```
$ sudo make altinstall
```

- Use this python version:

```
$ python3.9 --version
$ python3.9 scriptname.py
```

credit for this step by step guide goes to:
https://tech.serhatteker.com/post/2020-09/how-to-install-python39-on-ubuntu/#method-1-install-it-from-source-code

### Install the oedatamodel_api
**For windows users we recommend to use docker or docker desktop, because there have been installation problems in the past. However, even when installing docker on windows, there may be problems with the installation of docker itself.**

To install the oedatamodel api, you need to clone this repository to your local machine (assuming you have git installed on your machine):
```
$ mkdir ~/github
$ cd github
$ git clone https://github.com/open-modex/oedatamodel_api.git
cd oedatamodel_api
``` 

Setup a [python virtual environment](https://docs.python.org/3/tutorial/venv.html):


```
# create a new folder "env" that contains the virtual env. in the current folder
$ python3.9 -m venv env
# activate the env.
$ source env/bin/activate
```

Install dependency manager and install dependencies:

```
$ pip install poetry
$ poetry install
```

Now you should have an executable version of oedatamodel_api installed locally. You can run it with the following commands:

```
# If you alraedy have a oep api token set 
# a environment virable on you machine. 
# Else you have to sign up to https://openenergy-platform.org/user/login/?next=/
$ export OEP_TOKEN="1234567890ABCD"

# run the oedatamodel api
$ python oedatamodel_api/webapp.py
```
# Usage

## Sources
The oedatamodel_api cannot be used automatically for all tables created in the oedatamodel format on the oep. 
To configure whether a table can be used with the oedatamodel_api, the concept of sources was introduced. 
All sources can be found in the [sources directory](https://github.com/open-modex/oedatamodel_api/tree/main/oedatamodel_api/sources).

A source is technically a table join, through which it is possible to receive the data of the tables as a JSON file from the OEP. 
In simple terms, a source establishes the connection to newly created tables. 

**Note:** To create tables on the OEP the python tool [oem2orm](https://github.com/OpenEnergyPlatform/oem2orm) can be used. 
Follow this [Jupyter Guide](https://github.com/OpenEnergyPlatform/tutorial/blob/develop/upload/OEP_Upload_Process_Data_and_Metadata_oem2orm.ipynb).

## API Website
After the successful installation and the start of the locally installed oedatamodel_api instance (as described above) 
the home page of the oedatamodel_api can be reached under the following address (use an internet browser of your choice):

`http://0.0.0.0:8000/`

The homepage of the oedatamodel api shows some basic documentation and list a overview of currently available mappings. 
This part is still in **developement**.

### Upload data to the OEP
To upload data to the OEP, the tables must be available in the sources. 
Only data that is available as a [frictionless datapackage](https://specs.frictionlessdata.io/data-package/) can be uploaded. 
An example of this can be found [here](https://github.com/OpenEnergyPlatform/oedatamodel/tree/develop/examples). 

To simplify the process, the oedatamodel_api provides another web page to upload the datapackage. 

`http://0.0.0.0:8000/upload_datapackage`

There it is also possible to apply a mapping to the data before it is uploaded. 
This allows data to be uploaded in any format as long as a suitable mapping is first created 
that converts the data structure into the oedatamodel normalization format. 

### Get data from the OEP 

To acess data from the oep using the API you have to provide an OEP API token as described above. 
If you followed the installation instructions, this token should be available.

The API serves data in `JSON` format which can be queryed using HTTP query parameters. 
For each framework that is already supported by the oedatamodel_api there is a mapping provided.

For example, to retrieve data from the API with a locally installed version of the oedatamodel_api, the URL is:

`http://0.0.0.0:8000/scenario/id/55?source=modex&mapping=concrete`


## Mappings
New mappings can be created as a simple JSON file that maps data structures (input/output data) to or from the oedatamodel. 
These files are stored and developed under `oedatamodel_api/mappings`. The file `mappingname.json` contains a query language developed as JMESPath. 
Mappings are often stacked, since each mapping can have a base mapping. 
Therefore, it is obvious that one has to take several "processing steps" to develop a new mapping. 

## Tutorial - Upload data
1. Install the oedatamodel_api and launch it. For windows users we recommend to use docker or docker desktop, because there have been installation problems in the past. However, even when installing docker on windows, there may be problems with the installation of docker itself.

2. Go to oedatamodel and download the example datapackage zip archive. [Click to download form github.](https://github.com/OpenEnergyPlatform/oedatamodel/blob/develop/examples/Datapackage.zip?raw=true)

3. Create the example tables on the OEP that will be used to uplad  example data. 

Assuming you have still activated your Python environment.

Navigate to the tutorial directory:
(Open a terminal)

`cd tutorial`

Run the [script to create](https://github.com/open-modex/oedatamodel_api/blob/main/tutorial/create_oed.py) the tables from metadata that is provided in the tutorials/metadata directory:

`python create_oed.py`

4. run the oedatamodel_api and open the datapackage upload page. Insert this URL in any browser:
`http://0.0.0.0:8000/upload_datapackage`

5. Setup the upload form:
    - select the datapackage zip archive
    - insert 'normalize_example' into the 'Mapping (optional)' field
    - click the checkbox 'Show data after mapping (instead of upload)'

6. Click 'Senden' and look at the resulting page
    - the datapackage should be valid

7. Klick "back" to go back to the upload page and uncheck 'Show data after mapping (instead of upload)'and klick 'Senden' again to finally upload the example data to the example oed tables.

8. Open the oep example table and see the result
Data should be uploaded to all of the following tables:
https://openenergy-platform.org/dataedit/view/model_draft/oed_scenario_example

https://openenergy-platform.org/dataedit/view/model_draft/oed_data_example

https://openenergy-platform.org/dataedit/view/model_draft/oed_scalar_example

https://openenergy-platform.org/dataedit/view/model_draft/oed_timeseries_example

9. run the [table reset script](https://github.com/open-modex/oedatamodel_api/blob/main/tutorial/delete_oed.py) to delete the tables so that the next user can go through the tutorial:
(Insert into Terminal)

`python delete_oed.py`

# Get started (docker)

Run `sudo docker-compose up -d --build` to run the task queue and the webapp simulaneously.

Now the webapp is available at `127.0.0.1:5001`

Run `sudo docker-compose down` to shut the services down.

## Develop while services are running

### Using [fastapi](https://fastapi.tiangolo.com/)

In another terminal go the the root of the repo and run `. fastapi_run.sh`

Now the fast app is available at `127.0.0.1:5001`

While docker runs :
https://vsupalov.com/rebuilding-docker-image-development/

## Docs

To build the docs simply go to the `docs` folder

    cd docs

Install the requirements

    pip install -r docs_requirements.txt

and run

    make html

The output will then be located in `docs/_build/html` and can be opened with your favorite browser
