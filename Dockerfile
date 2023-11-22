FROM python:3.9-slim

WORKDIR /app_folder

COPY . .

RUN pip install -r req.txt

# CMD gunicorn --bind 0.0.0.0:4848 wsgi:app_test

CMD ["gunicorn", "-b", "0.0.0.0:4848", "server_wsgi:application"]

# CMD ["sleep", "infinity"]