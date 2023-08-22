# Changelog
All notable changes to this project will be documented in this file.

The format is inspired from [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and the versioning aim to respect [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- update databus URL to https://databus.openenergyplatform.org
- update databus to v0.12

## [0.16.0] - 2023-06-19
### Added
- JSONs are fixed during upload process
- primary keys can be incremented automatically

### Changed
- Upload checks whether "model_draft" is set as schema in resource name

## [0.15.0]
### Changed
- updated frictionless (from 4.40.11 to 5.13.1)

### Fixed
- CSV validation due to header rows and delimiter
- fixed frictionless update-related stuff

## [0.14.0] - 2023-05-11
### Added
- SEDOS energysystem structure graph

## [0.13.0] - 2023-03-31
### Added
- view to fix oedatamodel metadata and CSV

## [0.12.0] - 2022-12-08
### Changed
- databus artifact (instead of each dataset) is registered on MOSS at first upload

## [0.11.0] - 2022-12-05
### Changed
- database version equals data version
- added "type" as variant to databus, holding types "data" (CSV) and "metadata" (JSON)

## [0.10.1] - 2022-11-23
### Fixed
- OEP to frictionless conversion for "int"

## [0.10.0] - 2022-11-17
### Added
- menu for SEDOS related views
- view to register data on databus
- view to upload CSV data to single table (incl. frictionless validation)
- multiple tables per source
- view to create OEP tables from OEM

### Changed
- error is raised, if no metadata found when uploading to table

### Fixed
- temp dir for datapackages
- query parameters in upload_datapackage
- token for metadata creation via oem2orm

## [0.9.0] - 2022-06-15
### Added
- query page with dynamic source parameters
- project-specific mappings and sources
- "table" mapping for raw data tables from OEP
- support for single csv output format
- dynamic query filters

## [0.8.0] - 2022-06-15
### Added
- version to index.html
- new mapping style using chained mappings

## [0.7.0] - 2022-06-14
### Changed
- introduced pre-commit and fixed multiple linter errors

## [0.6.0] - 2022-06-14
### Changed
- datapackage is uploaded as multiple files (instead of zip)

## [0.5.0] - 2022-06-09
### Changed
- OEP token must be provided by user
- redis is optional

## [0.4.1] - 2021-08-31
### Fixed
- csv output uses semicolons and double quotes
- removed column "type" from concrete mapping (scalars and timeseries)

## [0.4.0] - 2021-05-19
### Changed
- caching via redis (instead of mem_cache)

## [0.3.0] - 2021-03-10
### Added
- custom mapping via get request
- caching of OEP scenario request
- Build docs as json file, including module docs and mappings.
- Display mapping_custom module docs and available mappings on index.html.
- datapackage upload (removed legacy upload of zip files)

## [0.2.0] - 2020-10-01
### Added
- Upload of excel datapackage into OEP

## [0.1.0] - 2020-09-01
### Added
- Normalized, concrete and custom mapping of OEP request data
- OEP oedatamodel request of scenario data
