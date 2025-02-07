# Testing Plan

## Overview
This document provides a comprehensive outline of our application's current test coverage, identifies areas that require immediate testing attention, and guides future test development priorities.

## Note on Test Coverage
The percentages of test coverage reported below are derived using the `coverage` tool. This tool generates a coverage report as part of the Run Ful Test Suite, which triggers every time a commit is made to a branch for which there is an open PR. Observations from these reports can be viewed directly in the terminal.

## Testing Categories and Current Coverage

### Configuration and Setup
- **Files and Coverage**:
  - `config/settings/local.py` (0%)
  - `config/settings/production.py` (0%)
  - `config/settings/base.py` (100%)
  - `config/urls.py` (71%)
  - `config/wsgi.py` (0%)

### Model Layer
- **Files and Coverage**:
  - `environmental_justice/models.py` (97%)
  - `feedback/models.py` (64%)
  - `sde_collections/models/candidate_url.py` (82%)
  - `sde_collections/models/collection.py` (65%)
  - `sde_collections/models/collection_choice_fields.py` (86%)
  - `sde_collections/models/delta_patterns.py` (89%)
  - `sde_collections/models/delta_url.py` (77%)
  - `sde_collections/models/pattern.py` (46%)
  - `sde_indexing_helper/users/models.py` (100%)

### Views and Controllers
- **Files and Coverage**:
  - `environmental_justice/views.py` (100%)
  - `feedback/views.py` (100%)
  - `sde_collections/views.py` (38%)

### Data Serialization and APIs
- **Files and Coverage**:
  - `environmental_justice/serializers.py` (100%)
  - `feedback/serializers.py` (100%)
  - `sde_collections/serializers.py` (75%)

### Admin Interface
- **Files and Coverage**:
  - `environmental_justice/admin.py` (100%)
  - `feedback/admin.py` (100%)
  - `sde_collections/admin.py` (66%)

### Utilities and Helpers
- **Files and Coverage**:
  - `sde_collections/utils/*.py` (Various coverage)
  - `sde_indexing_helper/utils/*.py` (0% to 100% coverage)

### Testing Infrastructure
- **Files and Coverage**:
  - `sde_collections/tests/*.py` (High coverage with some gaps)
  - `sde_indexing_helper/users/tests/*.py` (High coverage with minor gaps)

### Database and Migration Scripts
- **Files and Coverage**:
  - `config_generation/*.py` (Mostly 0% with some critical scripts untested)
  - All migration files across modules (Varied coverage, some with 0%)

### Task Automation and Background Jobs
- **Files and Coverage**:
  - `sde_collections/tasks.py` (44%)

### Critical Areas for Immediate Testing
- **Configuration Files**: Immediate attention to `local.py` and `production.py` is crucial for environment-specific settings.
- **View Layers in `sde_collections`**: Given their centrality to application logic and low coverage.
- **Model Complexity**: Specifically, the `sde_collections/models/collection.py` and `pattern.py` due to their low coverage and complexity.

## Recommended Actions
1. **Expand Unit Tests**: Focus on untested configuration files and complex models.
2. **Integration Tests**: Develop tests for views to ensure full application flow is covered.
3. **Continuous Integration Improvements**: Ensure that all tests are executed during CI processes, and add checks for test coverage thresholds.

## Conclusion
Prioritizing these areas will ensure robustness and reliability of our application, addressing both immediate testing gaps and setting a foundation for continuous quality assurance.
