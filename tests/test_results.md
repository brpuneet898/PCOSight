# PCOSight Automated Test Results

This document summarizes the automated test suite added for PCOSight. The tests are located in the `tests/` directory and are designed to verify core software quality areas: model loading, input validation, prediction behavior, and Flask route behavior.

## Test Suite Overview

The test suite uses Python's built-in `unittest` framework, so it can be run without adding an extra testing dependency. It can be executed from the project root with:

```powershell
env\Scripts\python.exe tests\run_tests.py
```

The runner prints each test result in the terminal and ends with a clear summary showing total tests run, failures, errors, and final pass/fail status.

## Tests Included

### Model Loading Tests

These tests verify that the saved machine learning assets can be loaded correctly from the `saved_models/` directory.

- `test_basic_model_assets_load_with_expected_features`
  - Confirms that the basic logistic regression model, scaler, and feature list load successfully.
  - Checks that the loaded feature list matches the expected basic prediction input fields.
  - Verifies that the model supports probability prediction and the scaler supports transformation.

- `test_advanced_model_assets_load_with_expected_features`
  - Confirms that the advanced random forest model and feature list load successfully.
  - Checks that the loaded feature list matches the expected advanced prediction input fields.
  - Verifies that the model supports probability prediction.

### Prediction Tests

These tests verify that both prediction functions behave correctly with valid and invalid input.

- `test_basic_prediction_returns_probability_between_zero_and_one`
  - Runs the basic prediction function with a valid sample input.
  - Confirms that the result is a floating-point probability between `0.0` and `1.0`.

- `test_advanced_prediction_returns_probability_between_zero_and_one`
  - Runs the advanced prediction function with a valid sample input.
  - Confirms that the result is a floating-point probability between `0.0` and `1.0`.

- `test_basic_prediction_requires_all_expected_features`
  - Removes a required field from the basic input.
  - Confirms that the prediction function raises an error instead of silently accepting incomplete data.

- `test_advanced_prediction_requires_all_expected_features`
  - Removes a required field from the advanced input.
  - Confirms that the prediction function raises an error instead of silently accepting incomplete data.

### Flask Route Validation Tests

These tests use Flask's test client to verify important application-level behavior.

- `test_protected_prediction_pages_redirect_to_login`
  - Confirms that protected prediction pages cannot be accessed without login.
  - Verifies that unauthenticated users are redirected to the login page.

- `test_register_rejects_missing_required_fields`
  - Submits an incomplete registration form.
  - Confirms that the app rejects missing required fields and redirects back to registration.

- `test_login_rejects_unknown_user`
  - Submits login details for a user that does not exist.
  - Confirms that invalid login attempts are rejected and redirected back to login.

- `test_basic_form_submits_valid_input_to_prediction_pipeline`
  - Simulates a logged-in user submitting the basic prediction form.
  - Confirms that form values are converted into the expected model input format.
  - Verifies that the basic prediction, recommendation generation, and save pipeline are called.

- `test_advanced_form_submits_valid_input_to_prediction_pipeline`
  - Simulates a logged-in user submitting the advanced prediction form.
  - Confirms that form values are converted into the expected model input format.
  - Verifies that the advanced prediction, recommendation generation, and save pipeline are called.

## Developer Test Run Results

The developers ran the automated test suite and all tests passed successfully.

```text
test_advanced_form_submits_valid_input_to_prediction_pipeline (test_pcosight.FlaskRouteValidationTests.test_advanced_form_submits_valid_input_to_prediction_pipeline) ... ok
test_basic_form_submits_valid_input_to_prediction_pipeline (test_pcosight.FlaskRouteValidationTests.test_basic_form_submits_valid_input_to_prediction_pipeline) ... ok
test_login_rejects_unknown_user (test_pcosight.FlaskRouteValidationTests.test_login_rejects_unknown_user) ... ok
test_protected_prediction_pages_redirect_to_login (test_pcosight.FlaskRouteValidationTests.test_protected_prediction_pages_redirect_to_login) ... ok
test_register_rejects_missing_required_fields (test_pcosight.FlaskRouteValidationTests.test_register_rejects_missing_required_fields) ... ok
test_advanced_model_assets_load_with_expected_features (test_pcosight.ModelLoadingTests.test_advanced_model_assets_load_with_expected_features) ... ok
test_basic_model_assets_load_with_expected_features (test_pcosight.ModelLoadingTests.test_basic_model_assets_load_with_expected_features) ... ok
test_advanced_prediction_requires_all_expected_features (test_pcosight.PredictionTests.test_advanced_prediction_requires_all_expected_features) ... ok
test_advanced_prediction_returns_probability_between_zero_and_one (test_pcosight.PredictionTests.test_advanced_prediction_returns_probability_between_zero_and_one) ... ok
test_basic_prediction_requires_all_expected_features (test_pcosight.PredictionTests.test_basic_prediction_requires_all_expected_features) ... ok
test_basic_prediction_returns_probability_between_zero_and_one (test_pcosight.PredictionTests.test_basic_prediction_returns_probability_between_zero_and_one) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.653s

OK

Test summary
Tests run: 11
Failures:  0
Errors:    0
Result:    PASS
```

## Conclusion

The PCOSight project now includes an automated test suite that verifies key functionality across model loading, prediction logic, input validation, and authenticated route behavior. The completed run shows that all 11 tests passed with zero failures and zero errors.
