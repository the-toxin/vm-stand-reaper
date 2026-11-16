# VM Stand Reaper

## Overview

This utility is designed to manage virtual machine (VM) "stands" (logical groups) in [**Yandex Compute Cloud**](https://yandex.cloud/ru/docs/compute/)  based on **Yandex Cloud** resource labels.

## Infrastructure Context

In Yandex Compute Cloud, VMs are organized into logical groups called **"Stands"** using a specific set of resource labels. Stand membership is defined by matching required label values.

### Required Label Schema

The following labels **must** be applied to VMs during stand deployment:

| Label | Description | Format | Requirement |
|-------|-------------|--------|-------------|
| **id** | Unique stand identifier | String (e.g., `"id-123"`) | **Required** |
| **team** | Owner team name | String (e.g., `"team"`) | **Required** |
| **owner** | Stand owner (username) | String (e.g., `"user"`) | **Required** |

### Optional Label

| Label | Description | Format | Notes |
|-------|-------------|--------|-------|
| **ttl** | Time-to-live (stand lifetime) | `"Xm"` – minutes<br>`"Xh"` – hours<br>`"Xd"` – days<br>`"never"` – permanent | Optional. Default behavior if omitted may vary. |

**Examples of valid TTL values:**
- `"30m"` – 30 minutes
- `"24h"` – 24 hours
- `"7d"` – 7 days
- `"never"` – stand will not be auto-removed

### Stand Grouping Logic

A VM belongs to a specific stand if and only if all its **required labels** (`id`, `team`, `owner`) match exactly with other VMs. The `ttl` label does not affect grouping.

---

## Installation

### [Python Poetry](https://python-poetry.org/)

```bash
git clone <repository-url>
cd <project-directory>
poetry install
```

### Docker
```bash
docker build -t vm-stand-reaper -f docker/Dockerfile .
```

## Usage

```bash
vm-stand-reaper [options]
```

## Examples

### Clean VMs in cloud concurrently by VM
```bash
vm-stand-reaper -b vm
```

### Clean VMs in cloud concurrently by VM (Docker)
```bash
docker run --rm -it \
    --env-file ./docker.env \
    --volume ./vm-stand-reaper-data:/opt/app/data \
    vm-stand-reaper vm-stand-reaper -b vm
```

## Configuration

Set environment variables for authentication:
```bash
export YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH="<file-path>"
export YANDEX_CLOUD_ID="<cloud-id>"
export YANDEX_FOLDER_ID="<folder-id>"
```
or
```bash
export YANDEX_OAUTH_TOKEN="<yandex-cloud-oauth-token>"
export YANDEX_CLOUD_ID="<cloud-id>"
export YANDEX_FOLDER_ID="<folder-id>"
```
