FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir -r requirements.txt \
  && pip install --no-cache-dir -r docs/requirements.txt \
  && pip install --no-cache-dir -r tests/requirements.txt \
  && pip install --no-cache-dir -e .

VOLUME [ "/app" ]

EXPOSE 5000/tcp

ENTRYPOINT [ "fairplay" ]

CMD [ "run", "-h", "0.0.0.0" ]
