# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2024-07-03

### Fixed

- Fix LTI roles model to handle additional roles from Moodle LTI launch requests

## [0.3.1] - 2024-06-26

### Added

- Add development view for lti select page

## [0.3.0] - 2024-06-05

### Added

- Add dedicated views depending on LTI roles
- Add a warren xi index all CLI command

### Changed

- Remove restricted access to instructors and administrators

### Security

- Pass `course_id`, `user_id` and `roles` through JWT token instead of app
 context data

## [0.2.0] - 2024-05-21

### Added

- Send LTI course id to the frontend
- Add a warren migration check CLI command

### Changed

- Restrict dashboards access to instructors and administrators
- Change cache key to indicator attributes instead of LRS query parameters

### Fixed

- Fix Breadcrumb trail order to be `organization > course > session`

## [0.1.0] - 2024-03-04

### Added

- Implement base view filters: date/times
- Implement base plugin architecture
- Bootstrap base backend boilerplate
- Implement video views endpoint
- Bootstrap base frontend boilerplate using turborepo
- Run ralph in the docker compose
- Add the LRS backend
- Switch the video view plugin from an elasticsearch to a LRS backend
- Remove the elasticsearch backend
- Add the LTI django application
- Rename the API directory to a more descriptive name.
- Add a select and date range picker to the web dashboard.
- Implement video downloads endpoint
- Rename video_uuid to follow xAPI semantic
- Use concise names in indicator and models
- Refactor the LRS client to be asynchronous
- Fix count of 0 in all video endpoints
- Require Python minimum version of 3.9
- Encapsulate statements pre-processing in a Mixin class
- Factorize Video indicators

[unreleased]: https://github.com/openfun/warren/compare/v0.3.2...main
[0.3.2]: https://github.com/openfun/warren/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/openfun/warren/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/openfun/warren/compare/v0.2.0...v0.3.0 
[0.2.0]: https://github.com/openfun/warren/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/openfun/warren/compare/abae78e...v0.1.0
