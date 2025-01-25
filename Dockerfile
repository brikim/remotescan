# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.13.1
FROM python:${PYTHON_VERSION}-alpine AS base
LABEL maintainer="Brian <bkimmle@gmail.com>"

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

ENV TZ=America/Chicago
ENV CONFIG_PATH='/config/config.conf'

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt && \
    apk upgrade --no-cache && \
    ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    mkdir /config && \
    mkdir /logs && \
    mkdir /app

# Copy the source code into the container.
COPY app.py /app
COPY api/ /app/api
COPY common/ /app/common
COPY external/ /app/external
COPY service/ /app/service

VOLUME ["/config"]
VOLUME ["/logs"]
VOLUME ["/media"]

# Run the application.
CMD [ "python", "/app/app.py"]
