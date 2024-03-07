FROM python:3.8-alpine

RUN pip3 install gunicorn

# Change to non-root privilege
RUN adduser -D nonroot
USER nonroot

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt
COPY . /app/

ENV port=8080

EXPOSE 8080

CMD ["gunicorn", "--access-logfile", "-", "--error-logfile", "-", "-w", "2", "--bind", "0.0.0.0:8080", "wsgi:app" ]