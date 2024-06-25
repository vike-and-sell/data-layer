FROM python:3.12-slim

WORKDIR /data-layer-api

# get linux dependencies
RUN apt-get update
RUN apt-get -y install libpq-dev gcc

COPY requirements.txt .

# Create a virtual environment and install dependencies
RUN python3 -m venv /data-layer-api/env && \
    /data-layer-api/env/bin/pip install --upgrade pip && \
    /data-layer-api/env/bin/pip install -r requirements.txt

# Ensure the virtual environment binaries are in the PATH
ENV PATH="/data-layer-api/env/bin:$PATH"

ENV DATA_LAYER_URL="localhost:4000"

COPY . .

EXPOSE 4000

CMD ["python3", "-u", "wsgi.py"]