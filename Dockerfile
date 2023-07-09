FROM python:3.11-buster

ARG APP_FOLDER=/home/authn/authn_git

RUN pip install poetry && useradd -d /home/authn -U -m -u 1111 authn && mkdir $APP_FOLDER

WORKDIR $APP_FOLDER

COPY --chown=authn:authn . .

USER root

RUN chmod 777 $APP_FOLDER

USER authn

RUN poetry install

ENTRYPOINT ["poetry", "run"]

CMD ["python", "main.py"]
