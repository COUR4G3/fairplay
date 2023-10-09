FROM python:3.11.4-slim-bullseye as base
LABEL maintainer="Michael de Villiers <michael@devilears.co.za>"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN --mount=type=cache,target=/root/.cache \
      pip --disable-pip-version-check install --upgrade \
        pip setuptools wheel

WORKDIR /opt/fairplay

COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
COPY docker/settings.toml /etc/fairplay/settings.toml

ENV CENTRIFUGAL_SETTINGS /etc/fairplay/settings.toml

ENTRYPOINT ["/docker-entrypoint.sh"]


FROM base as dev

ENV FLASK_DEBUG=1

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -yq \
      git libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
COPY dev/requirements.txt /tmp/dev-requirements.txt
COPY tests/requirements.txt /tmp/tests-requirements.txt

RUN --mount=type=cache,target=/root/.cache \
      pip --disable-pip-version-check install \
        -r /tmp/requirements.txt \
        -r /tmp/dev-requirements.txt \
        -r /tmp/tests-requirements.txt \
    && pip check

COPY . /opt/fairplay

RUN --mount=type=cache,target=/root/.cache \
  pip install --disable-pip-version-check -e .

EXPOSE 5000/tcp

CMD ["dev"]


FROM base as docs

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -yq \
      git \
      python3-enchant \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
COPY docs/requirements.txt /tmp/docs-requirements.txt
COPY typing/requirements.txt /tmp/typing-requirements.txt

RUN --mount=type=cache,target=/root/.cache \
      pip --disable-pip-version-check install \
        -r /tmp/requirements.txt \
        -r /tmp/docs-requirements.txt \
        -r /tmp/typing-requirements.txt \
        sphinx-autobuild \
    && pip check

COPY . /opt/fairplay

RUN --mount=type=cache,target=/root/.cache \
  pip install --disable-pip-version-check -e .

ENTRYPOINT ["sphinx-autobuild"]

EXPOSE 8000/tcp

CMD ["-a", "--host", "0.0.0.0", "--watch", "fairplay/", "docs/", "docs/_build/html"]


FROM base

RUN --mount=type=cache,target=/root/.cache \
      pip --disable-pip-version-check install \
        gunicorn \
    && pip check

COPY . /opt/fairplay

RUN --mount=type=cache,target=/root/.cache \
  pip install --disable-pip-version-check .

EXPOSE 5000/tcp

CMD ["run"]
