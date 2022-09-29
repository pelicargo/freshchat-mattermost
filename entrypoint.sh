#!/bin/sh
gunicorn --chdir /opt/freshchat-mattermost 'forward:create_app()'
