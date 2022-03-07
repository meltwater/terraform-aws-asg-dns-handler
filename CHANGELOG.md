# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Nothing.

### Changed

- Nothing.

### Removed

- Nothing.

### Deprecated

- Nothing.

## [1.2.2] - 2021-10-01

- [#188](https://github.com/meltwater/drone-cache/pull/188) v1.2.0 breaks EC2 IAM role bucket access

## [1.2.1] - 2021-09-30

### Added

- [#183](https://github.com/meltwater/drone-cache/pull/183) set goarch for arm64 goreleaser

## [1.2.0] - 2021-09-29

**Warning** arm64 docker images are broken in this release, please use to 1.2.1

### Added

- [#146](https://github.com/meltwater/drone-cache/issues/146) Provide an arm image
  - Multiple PRs
- [#99](https://github.com/meltwater/drone-cache/issues/99) Document building images and pushing locally for PR testing
- [#142](https://github.com/meltwater/drone-cache/issues/142) backend/s3: Add option to assume AWS IAM role
- [#102](https://github.com/meltwater/drone-cache/pull/102) Implement option to disable cache rebuild if it already exists in storage.
- [#86](https://github.com/meltwater/drone-cache/pull/86) Add backend operation timeout option that cancels request if they take longer than given duration. `BACKEND_OPERATION_TIMEOUT`, `backend.operation-timeot`. Default value is `3 minutes`.
- [#86](https://github.com/meltwater/drone-cache/pull/86) Customize the cache key in the path. Adds a new `remote_root` option to customize it. Defaults to `repo.name`.
  - Fixes [#97](https://github.com/meltwater/drone-cache/issues/97).
  [#89](https://github.com/meltwater/drone-cache/pull/89) Add Azure Storage Backend.
  [#84](https://github.com/meltwater/drone-cache/pull/84) Adds compression level option.
  [#77](https://github.com/meltwater/drone-cache/pull/77) Adds a new hidden CLI flag to be used for tests.
  [#73](https://github.com/meltwater/drone-cache/pull/73) Add Google Cloud storage support
  [#68](https://github.com/meltwater/drone-cache/pull/68) Introduces new storage backend, sFTP.

### Changed

- [#138](https://github.com/meltwater/drone-cache/pull/138) backend/gcs: Fix GCS to pass credentials correctly when `GCS_ENDPOINT` is not set.
- [#135](https://github.com/meltwater/drone-cache/issues/135) backend/gcs: Fixed parsing of GCS JSON key.
- [#151](https://github.com/meltwater/drone-cache/issues/151) backend/s3: Fix assume role parameter passing
- [#164](https://github.com/meltwater/drone-cache/issues/164) tests: lock azurite image to 3.10.0
- [#133](https://github.com/meltwater/drone-cache/pull/133) backend/s3: Fixed Anonymous Credentials Error on public buckets. 
  - Fixes [#132](https://github.com/meltwater/drone-cache/issues/132)

### Removed

- Nothing.

### Deprecated

- Nothing.