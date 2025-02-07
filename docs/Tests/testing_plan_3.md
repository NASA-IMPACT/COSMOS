# Testing Plan

## Overview
This document provides a comprehensive outline of our application's current test coverage, identifies areas that require immediate testing attention, and guides future test development priorities.

## Note on Test Coverage
The percentages of test coverage reported below are derived using the `coverage` tool. This tool generates a coverage report as part of the Run Full Test Suite, which triggers every time a commit is made to a branch for which there is an open PR. Observations from these reports can be viewed directly in the terminal.

## Testing Categories and Current Coverage

### Configuration and Setup
- **Critical and Untested**:
  - `config/settings/local.py` (0%): Environment-specific settings for local development.
  - `config/settings/production.py` (0%): Environment-specific settings for production environments.
  - `config/wsgi.py` (0%): WSGI configuration for deployment.
- **Partially Tested**:
  - `config/urls.py` (71%): URL dispatching and routing configurations.
- **Tested**:
  - `config/settings/base.py` (100%): Base settings including middleware, database configurations, etc.

### Model Layer
- **Critical and Undertested**:
  - `sde_collections/models/collection.py` (65%): Core model for handling collections, requires deeper testing due to its critical role in data management.
  - `sde_collections/models/pattern.py` (46%): Handles complex pattern matching logic, significantly under-tested.
  - `feedback/models.py` (64%): Involves important logic for managing feedback, requires additional coverage to ensure robust data integrity and operations.
- **Tested**:
  - `environmental_justice/models.py` (97%)
  - `sde_collections/models/candidate_url.py` (82%)
  - `sde_collections/models/collection_choice_fields.py` (86%)
  - `sde_collections/models/delta_patterns.py` (89%)
  - `sde_collections/models/delta_url.py` (77%)
  - `sde_indexing_helper/users/models.py` (100%)

### Views and Controllers
- **Critical and Undertested**:
  - `sde_collections/views.py` (38%): Central component for application's user interface logic, critically under-tested.
- **Tested**:
  - `environmental_justice/views.py` (100%)
  - `feedback/views.py` (100%)

### Data Serialization and APIs
- **Critical and Undertested**:
  - `sde_collections/serializers.py` (75%): Essential for API interaction, requires further testing to ensure robust data serialization.
- **Tested**:
  - `environmental_justice/serializers.py` (100%)
  - `feedback/serializers.py` (100%)

### Admin Interface
- **Critical and Undertested**:
  - `sde_collections/admin.py` (66%): Admin interface for managing application data, requires additional tests.
- **Tested**:
  - `environmental_justice/admin.py` (100%)
  - `feedback/admin.py` (100%)

### Utilities and Helpers
- **Critical and Undertested/Untested**:
  - `sde_collections/utils/github_helper.py` (19%)
  - `sde_collections/utils/health_check.py` (14%)
  - `sde_collections/utils/bulk_github_push.py` (0%)
  - `sde_collections/utils/generate_deployment_message.py` (0%)
  - `sde_collections/utils/slack_utils.py` (79%)
  - `sde_indexing_helper/utils/storages.py` (0%)

### Testing Infrastructure
- **Tested with Gaps**:
  - `sde_collections/tests/*.py`
  - `sde_indexing_helper/users/tests/*.py`

### Database and Migration Scripts
- **Critical and Mostly Untested**:
  - `config_generation/*.py`: Most scripts involved in database configuration and migration scripts are critically under-tested, posing a risk to data integrity and application setup.

### Task Automation and Background Jobs
- **Critical and Undertested**:
  - `sde_collections/tasks.py` (44%): Handles background tasks and automation, significantly under-tested considering their operational importance.

## Critical Areas for Immediate Testing
1. **Configuration Files**: Immediate testing for `config/settings/local.py` and `config/settings/production.py` to ensure they function correctly across different environments.
2. **Core Business Logic in Models and Views**: Focus on significantly under-tested `sde_collections/models/collection.py` and `sde_collections/views.py`.
3. **Utility Scripts and Background Jobs**: Address the lack of tests for critical utilities such as `sde_collections/utils/github_helper.py` and `sde_collections/tasks.py`.

## Recommended Actions
- **Expand Unit Tests**: For critical configuration files and complex models.
- **Integration Tests**: Enhance coverage for views and serializers to ensure complete application workflows.
- **Continuous Integration Improvements**: Implement tests during CI processes and enforce coverage thresholds.

## Conclusion
This plan highlights critical testing needs and outlines a structured approach to addressing immediate testing gaps while setting a long-term foundation for continuous quality assurance. By following this plan, we aim to improve the robustness and reliability of our application systematically.
