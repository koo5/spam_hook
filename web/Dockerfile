FROM python:3.10


ARG uid=1000
ARG gid=1000
RUN groupadd -g $gid user && useradd -lm -u $uid -g $gid user
USER user


ENV PYTHONUNBUFFERED true
ENV PYTHONDONTWRITEBYTECODE 1
ENV PATH "/home/user/.local/bin:$PATH"


WORKDIR /
COPY app /
COPY requirements.txt /

RUN pip install -r requirements.txt

WORKDIR /app
