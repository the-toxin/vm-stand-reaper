ARG PYTHON_VERSION=3.13 \
    PYTHON_VERSION_MINOR=3.13 \
    POETRY_VERSION=2.2.1 \
    APP_HOME="/opt/app"


FROM python:${PYTHON_VERSION}-slim AS builder

ARG PYTHON_VERSION \
    POETRY_VERSION \
    APP_HOME

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR ${APP_HOME}

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-root --no-ansi

COPY src/ ./src/
RUN poetry install --only main --no-ansi


FROM python:${PYTHON_VERSION}-slim AS runner

LABEL description="VM Stand Reaper" \
      version="0.1.0"

ARG APP_HOME \
    PYTHON_VERSION_MINOR \
    USER_ID=1000 \
    GROUP_ID=1000

ENV APP_HOME=${APP_HOME} \
    PYTHON_VERSION_MINOR=${PYTHON_VERSION_MINOR} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

USER appuser
WORKDIR ${APP_HOME}

COPY --from=builder /usr/local/lib/python${PYTHON_VERSION_MINOR}/site-packages /usr/local/lib/python${PYTHON_VERSION_MINOR}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appgroup src/ ./src/

CMD ["vm-stand-reaper", "--help"]
