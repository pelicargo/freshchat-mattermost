#!/bin/sh
gunicorn -b 0.0.0.0:80 --chdir /opt/freshchat-mattermost 'forward:create_app()'
