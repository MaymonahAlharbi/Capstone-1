FROM python

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 7070

CMD ["python", "app.py"]
