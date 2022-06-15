# Changelog
All notable changes to this project will be documented in this file.

The format is inspired from [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and the versioning aim to respect [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
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
