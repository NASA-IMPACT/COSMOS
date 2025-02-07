# Testing Plan for Project

## Overview
This document outlines the current testing status and identifies priority areas where additional testing is necessary to ensure application robustness and maintainability.

## Note on Test Coverage
The percentages of test coverage reported below are derived using the `coverage` tool. This tool generates a coverage report as part of the Run Full Test Suite, which triggers every time a commit is made to a branch for which there is an open PR. Observations from these reports can be viewed directly in the terminal.

## Current Testing Status Overview

### Well-Covered Areas (90-100% Coverage)
- **Configuration and Initial Setup**
  - `config/__init__.py`, `config/celery_app.py`, `config/settings/base.py`, `config/settings/__init__.py`, `config/settings/test.py`: These configurations are crucial for the application's initial setup and runtime environment, and they are well-tested ensuring stability in configuration loading and processing.

- **Environmental Justice Features**
  - All modules within `environmental_justice` except some migrations showing high test coverage. This includes models, views, and serializers which are critical to the functionality of the environmental justice features.

- **Feedback System**
  - Similar to environmental justice, the feedback system shows robust testing across its serializers, views, and most models.

### Areas with Moderate Coverage (70-89% Coverage)
- **sde_collections**
  - Some modules in `sde_collections` like `admin.py`, `models/collection.py`, and `models/candidate_url.py` show moderate coverage, suggesting that critical business logic related to collection management could benefit from additional testing.

### Critical Areas with Insufficient Tests (<70% Coverage)
- **Settings Files**
  - `config/settings/local.py` and `config/settings/production.py`: These files are crucial as they define environment-specific settings but currently have 0% coverage. Immediate attention is required to ensure that all configurations hold up under various environments.

- **Configuration Generation**
  - Most of the `config_generation` scripts such as `db_to_xml.py`, `api.py`, `generate_commands.py`, etc., are critically under-tested. Given that these scripts likely play a significant role in setting up and maintaining the application state, comprehensive tests are essential.

- **Utilities and Helpers**
  - Utility scripts and helpers like those in `sde_collections/utils`, particularly `github_helper.py` and `health_check.py`, show significant gaps in testing. These are important for the application's integration and maintenance operations.

## Recommendations for Immediate Test Development

### High Priority Tests
1. **Complete Testing for Settings Management**
   - Develop tests for `config/settings/local.py` and `config/settings/production.py` to validate all configurations under simulated environments to prevent deployment issues.

2. **Robust Tests for Configuration Generation**
   - Implement unit and integration tests for the `config_generation` module to ensure all configurations and settings are generated correctly and errors are handled gracefully.

3. **Enhanced Testing for Collection Management**
   - Focus on increasing coverage for `sde_collections/models` and `sde_collections/views`. Given their direct impact on user data management and interface behavior, it is critical to cover these with more comprehensive tests including edge cases and failure modes.

### Medium Priority Tests
1. **Utility Scripts and Helpers**
   - Scripts that support operational tasks such as `sde_collections/utils/github_helper.py` and `health_check.py` need thorough testing to ensure reliability in operational tasks.

2. **Admin Interfaces and Forms**
   - Given the moderate coverage in some admin and form-related areas, additional tests should be considered to cover all user interactions and data validation scenarios.

### Lower Priority Tests
1. **Further Testing of Well-Covered Areas**
   - While not immediate, ensure that any new features or changes in areas like `environmental_justice` and `feedback` modules continue to maintain high coverage and reflect any new business logic or changes.

## Testing Plan Execution

- **Schedule and Assignments**: Assign test development tasks according to priority, with scheduled milestones for high-priority tests within the next sprint. Medium and lower priority tests can be scheduled for subsequent sprints.
- **Resources**: Allocate resources not only for writing tests but also for setting up better test environments and potentially integrating more comprehensive CI/CD pipelines to automate and validate coverage on each build.
- **Review and Adapt**: Continuously monitor test coverage metrics and adapt the testing plan as the project evolves. This dynamic approach will help ensure that the testing strategy remains aligned with project goals and technological shifts.
