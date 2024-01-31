FROM python:3.10.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV DATABASE_URI=mysql+pymysql://root:toor@weatherDB:3306/weatherDB

CMD ["python", "MyWeatherHandler.py"]