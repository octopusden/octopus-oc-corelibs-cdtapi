# AGENTS.md

Guidance for coding agents working in this repository.

## Commands

```bash
# install (editable is convenient for iterating)
python -m pip install -e .

# full suite: unit tests plus the HttpAPI doctests (test_API.py loads them)
python -m unittest discover -v
python -m pytest oc_cdtapi/tests

# one module / one test
python -m pytest oc_cdtapi/tests/test_PostgresAPI.py -v
python -m pytest oc_cdtapi/tests/test_PostgresAPI.py::TestPostgresAPI::test_get_citypedms_by_dms_id -v

# build what CI publishes
python setup.py sdist bdist_wheel
```

The three `HttpAPI` doctests in `API.py` (`__init__`, `get`, `put`) start a local `TestServer` and fail on a developer machine, on `main` as well. Treat those three as a known baseline; any other failure is yours.

CI (`.github/workflows/`) delegates to the reusable `octopusden/octopus-base` workflow: `on-push.yml` deploys to Test on every push, `on-release.yml` deploys to Prod on a published release. The `Dockerfile` builds the wheel on Python 3.7 and runs `python setup.py test`. There is no lint step.

## Releasing

This is a shared library pinned by many services (for example `octopus-oc-srv-jobs-dms-mirror` requires `oc-cdtapi>=...`). Every change bumps `__version` in `setup.py`:
- a new method or class: minor (`3.47.1` → `3.48.0`);
- a fix: patch.

Never change the signature, return shape or error behaviour of an existing public method. Callers depend on them; add a new method or an optional keyword argument instead.

Keep code importable on Python 3.6+ (`python_requires=">=3.6"`; the image builds on 3.7): f-strings and simple type hints are fine, walrus operators and `dict | None` annotations are not.

## Architecture

`oc_cdtapi/` holds one client module per service. Most clients subclass `API.HttpAPI`:

- `API.py`: `HttpAPI`, a thin `requests.Session` wrapper.
  - Configuration comes from the constructor or, when a subclass sets `_env_prefix`, from `<PREFIX>_URL`, `<PREFIX>_USER` and `<PREFIX>_PASSWORD`.
  - `get/post/put/delete/head(req, params=..., ...)` join `req` onto the root URL and return the `requests.Response`.
  - Any status outside 200..399 raises `HttpAPIError(code, url, resp, text)`, so callers check `e.code` (typically `404`) rather than the status code.
  - The session retries only on 401.
- `PgAPI.py`: `PostgresAPI` (`PSQL_*`), the client for the IDP postgres API service (Bitbucket `IDP/idp-postgres-api-service`). Methods map one-to-one to its endpoints, mostly `rest/api/1/...`. Tasks switch between v1 and `api/v2` through `api_version`, and dumps use `api/v2`.
- `PgQAPI.py`: `PgQAPI`, a direct `psycopg2` client for the PostgreSQL message queue (no HTTP).
- `DmsAPI.py` (`DmsAPI`, `DmsAPIv3`), `DmsGetverAPI.py`, `NexusAPI.py` (Nexus and Artifactory), `JenkinsAPI.py`, `RundeckAPI.py`, `BitbucketAPI.py`, `DevPIAPI.py`, `Dbsm2API.py`, `OnecAPI.py`, `ForemanAPI/` (package with `api.py` and `dto.py`).
- `VaultAPI.py`: `VaultAPI.load_secret("PATH__KEY")` resolves a secret from the environment first, then Vault (`VAULT_URL`, `VAULT_TOKEN`, `VAULT_MOUNT_POINT`). Services use it for their argparse defaults.
- `TestServer.py`: a mock HTTP server used by the `HttpAPI` doctests.
- `nexus.py` (repo root): command-line tool for Maven-compatible storage, installed as a script.

### Adding a client method

Copy the shape of its neighbours. In `PgAPI.py`, for example:
- build `req`, call `self.get(req, params=...)`, log with `logging.debug(f'Using <method> to ...')`, and return `res.json()`;
- write a docstring with `Args`, `Returns`, `Raises` where relevant, and an `Example`;
- let `HttpAPIError` propagate unless the existing method family deliberately maps 404 to `None` (as `get_dump` does).

Name methods after the endpoint and key, matching existing ones (`get_citypedms_by_dms_id`, `get_citypeincs_by_citype_id`).

## Tests

- **Layout:** one file per module in `oc_cdtapi/tests/test_<Module>.py`, `unittest` style; pytest also runs them.
- **No real network.** Patch the HTTP verb on the class, `@patch('oc_cdtapi.PgAPI.PostgresAPI.get')`. Give the mock a `MagicMock` response with `.json.return_value`, and assert the exact call with `mock_get.assert_called_once_with('<path>', params={...})`.
- **Errors:** build them as `HttpAPIError(code=404, url="...")` through `side_effect`, then assert either the mapped result or `assertRaises(HttpAPIError)`.
- **Setup:** `setUp` patches `os.getenv` so clients construct without real environment variables.
- **Coverage:** every new method gets at least one test for the request it builds and the value it returns, plus its error path.

## Working in this repo

- **Untracked local files:** `.env` holds local credentials. Never read it into output, and never commit it. `__pycache__/` and `oc_cdtapi.egg-info/` are local build output.
- **Branches and worktrees:** branches are named `feat-…` / `fix-…`. Some are checked out as sibling worktrees (`../octopus-oc-corelibs-cdtapi-<topic>`), so check `git worktree list` before switching branches.
- **Commits:** PR titles and squash commits read `feat: …` / `fix: …`.
