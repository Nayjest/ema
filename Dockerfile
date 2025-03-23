FROM python:3.12.7-slim-bookworm

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y && \
    apt-get install -y \
    mc  \
    procps \
    expect \
    make \
    curl

WORKDIR /app

COPY requirements /app/requirements
RUN pip install --upgrade pip
RUN pip install supervisor  # works only for unix systems
RUN pip install --no-cache-dir -r /app/requirements/dev.txt
COPY supervisord.conf /etc/supervisord.conf
RUN ln -s /usr/local/bin/supervisorctl /usr/local/bin/ctl # handy alias to use 'ctl' instead of 'supervisorctl'
CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]