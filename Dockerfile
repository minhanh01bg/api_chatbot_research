FROM python:3.10-slim


RUN mkdir -p /requirements
COPY requirements/base.txt /requirements/base.txt

COPY requirements/dev.txt /requirements/dev.txt

RUN pip install -r /requirements/base.txt
RUN pip install -r /requirements/dev.txt
COPY settings.toml settings.toml
COPY app /app
WORKDIR /app
RUN mkdir -p alembic
RUN pip install opencv-python opencv-python-headless opencv-contrib-python-headless langgraph==0.2.73
EXPOSE 7000
CMD uvicorn main:app --reload --host 0.0.0.0 --port 7000