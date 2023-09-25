FROM python:3.8-alpine

RUN pip3 install gunicorn

# Change to non-root privilege
RUN adduser -D nonroot
USER nonroot

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt
COPY . /app/

ENV port=5000
ENV solr=http://neurobridges-ml.edc.renci.org:8983

CMD [ "gunicorn", "-w", "2", "--bind", "0.0.0.0:8080", "wsgi:app" ]