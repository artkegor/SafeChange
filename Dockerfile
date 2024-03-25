FROM python:3.10

WORKDIR /safechange

COPY . .
RUN pip install -U pip setuptools wheel
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]