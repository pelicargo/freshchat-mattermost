FROM ubuntu:22.04

RUN apt-get update && apt-get -y --no-install-recommends install python3-pip python3-cryptography

WORKDIR /opt/freshchat-mattermost

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

COPY forward.py ./forward.py
COPY entrypoint.sh ./entrypoint.sh

ENTRYPOINT ["/opt/freshchat-mattermost/entrypoint.sh"]
