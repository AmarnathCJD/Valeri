FROM python:slim-bullseye

WORKDIR /app

COPY . /app

RUN pip3 install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y golang-go
RUN apt-get install -y ffmpeg
RUN apt-get install -y aria2
RUN apt-get install -y speedtest-cli
RUN apt-get install -y sox

# Set permissions for /spotify/bin/playplay
RUN chmod a+x /spotify/bin/playplay

# Run app.py when the container launches
CMD ["python3", "main.py"]
