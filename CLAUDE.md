# CLAUDE.md

## Project

`vm-stand-reaper` is a CLI utility that cleans up outdated virtual machines in **Yandex Compute Cloud**. A VM is grouped into a **stand** via the `id`, `team`, `owner` labels (all required); `ttl` (`Xm`/`Xh`/`Xd`/`never`) is optional and defaults to `4h` (overridable via `STAND_TTL`). A stand is deleted when its computed `delete_at` (latest VM `created_at` + stand TTL) is in the past. VMs missing required labels are always deleted.

## Tech Stack
- Python 3.13+, Poetry, Pytest
- Docker, multi-stage builds
- Terragrunt 0.90, OpenTofu 1.10

## Project Structure
```
vm-stand-reaper/
├── README.md
│
├── src/vm_stand_reaper/               # ── app (DDD layers) ──
│   ├── domain/model.py                # VirtualMachine, VirtualMachineLabels,
│   │                                  #   VirtualMachineStand (TTL logic, delete_at)
│   ├── service_layer/
│   │   ├── services.py                # sort/delete orchestration (asyncio.gather)
│   │   ├── unit_of_work.py            # AbstractUnitOfWork (port)
│   │   └── yc_uow.py                  # YC implementation of UoW
│   ├── adapters/
│   │   ├── repository.py              # AbstractRepository (port)
│   │   ├── yc_repository.py           # YC gRPC adapter + YCSDKFactory
│   │   ├── yc_settings.py             # pydantic-settings + SA-key validation
│   │   ├── environment_variables.py   # EnvironmentVariableName enum
│   │   └── logging.py                 # setup_logging (LOG_LEVEL)
│   └── entrypoints/cli.py             # click CLI: -b vm | -b stand
│
├── tests/unit/                        # unit tests on Fake* repos (no real YC)
│   ├── test_services.py               # FakeRepository / FakeUnitOfWork
│   ├── test_vm_labels.py
│   ├── test_vm_stands.py
│   └── test_yc_settings.py
│
├── docker/
│   └── Dockerfile                     # two-stage build (builder + runner)
│
└── infra/                             # ── IaC ──
    ├── terraform/modules/
    │   ├── yc-compute-instance/       # reusable TF module
    └── terragrunt/dev/                # dev env, 4 test stands (stand-01…04)
        └── stand-NN/                  # identical structure per stand
            ├── root.hcl / cloud.hcl / env.hcl / labels.yaml
            └── app/terragrunt.hcl + db/terragrunt.hcl
```

## Architecture

The codebase follows the **Domain-Driven Design layering** (cosmic python style) with a strict dependency direction:

```
entrypoints  ─►  service_layer  ─►  domain
                        │
                        └─►  adapters (repository, settings)
```

- `domain/model.py` — pure dataclasses/classes: `VirtualMachine`, `VirtualMachineLabels`, `VirtualMachineStand` (stand-aggregation, TTL parsing, `delete_at` computation live here). No I/O.
- `service_layer/services.py` — orchestration: `sort_vms_to_stands`, `delete_vms` (concurrent `asyncio.gather`), `delete_outdated_vm_stands`, `delete_outdated_vms`. Depends only on the abstract UoW.
- `service_layer/unit_of_work.py` (`AbstractUnitOfWork`) + `adapters/repository.py` (`AbstractRepository`) — the ports.
- `adapters/yc_repository.py` — the Yandex Cloud adapter: wraps `yandexcloud` SDK gRPC calls, runs sync SDK calls in `run_in_executor`, gates concurrency via `asyncio.Semaphore` (`max_concurrent_requests`), and maps protobuf `Instance` → domain `VirtualMachine` via `_to_domain_model`. `YCSDKFactory.create()` picks auth in priority: **IAM token → service-account key JSON → OAuth token**.
- `adapters/yc_settings.py` — `pydantic-settings` reads env (`.env.local` then `.env`, `extra="ignore"`) and validates the SA key JSON file structure when provided. All user-facing validation errors are re-raised as `ValueError`.
- `entrypoints/cli.py` — `click` CLI. Pushes CLI args back into `os.environ` before constructing `YCSettings`, then `asyncio.run`s the chosen cleanup path. `-b/--by_type` selects `vm` (concurrent) vs `stand` (sequential) semantics.

### Key invariants when modifying

- **Don't import adapters from `domain/` or `service_layer/services.py`** — those layers depend on abstractions only. The YC UoW is wired up lazily inside `cli.py`.
- **Label names are centralized** in `InstanceLabelName` (`yc_repository.py`) and `EnvironmentVariableName` (`environment_variables.py`); reuse rather than hardcoding strings.
- **`VirtualMachineStand` is mutable** (tracks `created_at`, `ttl`, `delete_at` as VMs are added via `add_vm`); `VirtualMachine`/`VirtualMachineLabels` are frozen dataclasses and used as set members — keep them hashable.
- **Tests use `FakeRepository`/`FakeUnitOfWork`** (see `tests/unit/test_services.py`); follow that pattern for new service-layer tests rather than mocking the YC SDK.

## Commands

```bash
# Python
poetry install
poetry run pytest                          # all tests
poetry run pytest tests/unit/test_services.py::test_delete_vms  # single test
poetry run vm-stand-reaper --help
poetry run vm-stand-reaper -b vm           # delete outdated VMs concurrently
poetry run vm-stand-reaper -b stand        # delete per-stand sequentially

# Docker
docker build -t vm-stand-reaper -f docker/Dockerfile .
docker run --rm -it -e YANDEX_IAM_TOKEN=$(yc iam create-token) -e YANDEX_CLOUD_ID=$DEV_CLOUD_ID -env YANDEX_FOLDER_ID=$DEV_FOLDER_ID -e STAND_TTL=10m vm-stand-reaper vm-stand-reaper -b vm

# IaC (run dev stand)
cd infra/terragrunt/dev/stand-01/
DEV_CLOUD_ID=... DEV_FOLDER_ID=... DEV_SUBNET_ID=... terragrunt run --all apply

# IaC (destroy dev stand)
cd infra/terragrunt/dev/stand-01/
DEV_CLOUD_ID=... DEV_FOLDER_ID=... DEV_SUBNET_ID=... terragrunt run run --all destroy
```
## Testing Guidelines
- **pytest** is the main framework.
- **Unit tests**: isolated, mock infrastructure. Cover domain logic and use cases.
- **Integration tests**: use real dependencies (API stubs).
- **E2E tests**: run against provisioned infrastructure (Terragrunt). Verify full scenarios.
- All tests must be reproducible.

## E2E Infrastructure

`infra/terraform/modules/yc-compute-instance/` is a reusable module (provider `yandex ~> 0.127`) that creates `count`-based compute instances and an optional Ansible inventory file from `inventory.tftpl`.

`infra/terragrunt/dev/stand-NN/{app,db}/terragrunt.hcl` consumes that module per stand. Each stand dir:
- includes `root.hcl` (generates `provider.tf` + local `remote_state`; an S3 backend block is commented out for non-dev use),
- reads `DEV_CLOUD_ID`/`DEV_FOLDER_ID`/`DEV_SUBNET_ID` from the environment via `cloud.hcl`/`env.hcl`,
- applies the stand's `labels.yaml` (the `id`/`team`/`owner`/`ttl` the reaper reads) to every instance.

## Code Style & Quality
- **Docstrings**: Google style.

## Conventions

- **Configuration**: Only through environment variables (pydantic-settings or similar). No hardcoding.
- **Commits**: Atomic, with meaningful messages (English, imperative mood).
- **Documentation**: Update README when adding commands or changing environment.
