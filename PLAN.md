# Plan: Introduce Authentication Flag

This plan outlines the steps to introduce a feature flag that allows switching between API key authentication and Application Default Credentials (ADC).

## 1. Introduce `AUTH_MODE` Configuration

- [ ] **Modify `app.py` or configuration loader**:
    - Read a new environment variable `AUTH_MODE`.
    - The possible values for `AUTH_MODE` will be `API_KEY` and `ADC`.
    - Default to `API_KEY` if the variable is not set, to maintain backward compatibility.
    - Make the `auth_mode` value available to the components that need it.

## 2. Refactor Authentication in Agent and Service Initializers

For each component (agent or service) that communicates with a Google Cloud service:

- [ ] **Identify all classes that accept an `api_key` parameter.**
    - I will start by searching for `api_key:` in the codebase to find all relevant classes.

- [ ] **Modify the `__init__` methods of these classes:**
    - Add a new `auth_mode` parameter.
    - Inside the `__init__` method, use an `if/else` block based on the `auth_mode`:
        - If `auth_mode` is `API_KEY`, the existing logic of using the `api_key` parameter will be used.
        - If `auth_mode` is `ADC`, the client will be initialized without an `api_key`. The Google Cloud client libraries will automatically pick up the credentials from the environment.

## 3. Update Component Creation

- [ ] **Modify the part of the code where agent/service instances are created**:
    - When creating instances of the agents and services, pass the `auth_mode` configuration to them.

## 4. Update Documentation

- [ ] **Modify `README.md`**:
    - Document the new `AUTH_MODE` environment variable and its possible values (`API_KEY`, `ADC`).
    - Explain how to use each authentication method.

- [ ] **Modify `.env.example`**:
    - Add `AUTH_MODE=API_KEY` to the example environment file to show the default.

## 5. Verification

- [ ] **Manual testing**:
    - Run the application with `AUTH_MODE=API_KEY` (or without setting it) and verify it works as before.
    - Run the application with `AUTH_MODE=ADC` in an environment where ADC is configured (e.g., after running `gcloud auth application-default login`) and verify it authenticates correctly.
