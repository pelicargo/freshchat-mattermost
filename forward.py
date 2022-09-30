import base64
import datetime
import json
import os
import requests
import sys
from Crypto.Signature import pkcs1_15  # type: ignore
from Crypto.Hash import SHA256  # type: ignore
from Crypto.PublicKey import RSA  # type: ignore
from flask import Flask, request  # type: ignore
from typing import Callable, Dict, List, Tuple

FRESHCHAT_API_URL = os.environ['FRESHCHAT_API_URL']
FRESHCHAT_APP_ID = os.environ['FRESHCHAT_APP_ID']
FRESHCHAT_PUBLIC_KEY = os.environ['FRESHCHAT_PUBLIC_KEY']
FRESHCHAT_TOKEN = os.environ['FRESHCHAT_TOKEN']
MATTERMOST_API_URL = os.environ['MATTERMOST_API_URL']
MATTERMOST_BOT_TOKEN = os.environ['MATTERMOST_BOT_TOKEN']
MATTERMOST_SLASH_TOKEN = os.environ['MATTERMOST_SLASH_TOKEN']
MATTERMOST_CHANNEL_ID = os.environ['MATTERMOST_CHANNEL_ID']

freshchat_public_key = RSA.import_key(FRESHCHAT_PUBLIC_KEY)

# Utility function for partitioning.
def partition_list_str(lst: List[str], pred: Callable[[str], bool]) -> Tuple[List[str], List[str]]:
    yes: List[str] = []
    no: List[str] = []
    for d in lst:
        if pred(d):
            yes.append(d)
        else:
            no.append(d)
    return (yes, no)

# Returns the Response object as defined in the requests library (not Flask)
def freshchat_get_user(user_id):
    return freshchat_get('/users/' + user_id)

# Returns the Response object as defined in the requests library (not Flask)
def freshchat_get_agent(agent_id):
    return freshchat_get('/agents/' + agent_id)

# Returns the Response object as defined in the requests library (not Flask)
def freshchat_get(endpoint, **kwargs):
    return requests.get(
        FRESHCHAT_API_URL + endpoint,
        headers={
            'Authorization': 'Bearer ' + FRESHCHAT_TOKEN
        },
        **kwargs
    )

# Returns the Response object as defined in the requests library (not Flask)
def freshchat_post(endpoint, **kwargs):
    return requests.post(
        FRESHCHAT_API_URL + endpoint,
        headers={
            'Authorization': 'Bearer ' + FRESHCHAT_TOKEN
        },
        **kwargs
    )

# Returns the Response object as defined in the requests library (not Flask)
def mattermost_create_post(channel_id, message):
    return mattermost_post(
        '/posts',
        json={
            'channel_id': channel_id,
            'message': message
        }
    )

# Returns the Response object as defined in the requests library (not Flask)
def mattermost_get(endpoint, **kwargs):
    return requests.get(
        MATTERMOST_API_URL + endpoint,
        headers={
            'Authorization': 'Bearer ' + MATTERMOST_BOT_TOKEN
        },
        **kwargs
    )

# Returns the Response object as defined in the requests library (not Flask)
def mattermost_post(endpoint, **kwargs):
    return requests.post(
        MATTERMOST_API_URL + endpoint,
        headers={
            'Authorization': 'Bearer ' + MATTERMOST_BOT_TOKEN
        },
        **kwargs
    )

def format_freshchat_user(user):
    print(user)
    first_name = user.get('first_name')
    last_name = user.get('last_name')
    email = user.get('email')
    s = 'Client '
    if first_name != None:
        s += f'{first_name} '
    if last_name != None:
        s += f'{last_name} '
    if email != None:
        s += f'{email} '
    s += 'posted:\n'
    return s

def parse_mattermost_command(raw_text: str, raw_user_name: str) -> Tuple[str, str, str]:
    """
    Parse a Mattermost slash command in the form of
    "<convo id> [!!as:...] rest of message"
    :return: convo_id, message, user_name
    """
    # Parse the raw text
    words = raw_text.strip().split(" ")
    if len(words) < 2:
        raise ValueError("Bad command syntax")
    convo_id = words[0]
    special_words, message_words = partition_list_str(words[1:], pred=lambda x: x.startswith("!!"))
    message = " ".join(message_words)

    # Handle the as command
    user_name = raw_user_name
    as_lst = list(filter(lambda x: x.startswith("!!as:"), special_words))
    if len(as_lst) > 0:
        user_name = as_lst[0].removeprefix("!!as:")

    return convo_id, message, user_name

def create_app(test_config=None):
    app = Flask(__name__)

    def get_agents() -> List[dict]:
        resp = freshchat_get('/agents')
        if resp.status_code != 200:
            app.logger.error(f'When retrieving Freshchat agents, got {resp.status_code}')
        resp = resp.json()
        count = resp['pagination']['total_items']
        if count != len(resp['agents']):
            resp = freshchat_get('/agents', data={
                'items_per_page': count
            })
            if resp.status_code != 200:
                app.logger.error(f'When retrieving Freshchat agents with pagination, got {resp.status_code}')
        return resp['agents']

    def get_mattermost_users() -> List[dict]:
        resp = mattermost_get('/users')
        return resp.json()

    def map_usernames_to_agents() -> Dict[str, str]:
        users = get_mattermost_users()
        agents = get_agents()
        mapping: Dict[str, str] = {}
        for agent in agents:
            for user in users:
                if user['email'] == agent['email']:
                    mapping[user['username']] = agent['id']
        return mapping

    usernames_to_agents = map_usernames_to_agents()

    # {
    #   "actor": {
    #     "actor_type": "agent",
    #     "actor_id":"fba1873d-67d6-4d63-be97-53b29ae1e42a"
    #    },
    #    "action": "message_create",
    #    "action_time": "2021-08-17T08:06:22.824Z",
    #    "data": {
    #      "message": {
    #        "message_parts": [
    #          {
    #            "text": {
    #              "content": "hello"
    #            }
    #          }
    #        ],
    #        "app_id": "a1553a5a-9eed-48e8-9fc7-9106080f509d",
    #        "actor_id": "fba1873d-67d6-4d63-be97-53b29ae1e42a",
    #        "org_actor_id": "345162432277281455",
    #        "id": "6896afdc-23bc-45cc-8bfe-d5ecfbab6dc1",
    #        "channel_id": "eaee3077-7e72-475d-bd5c-9eeed4262995",
    #        "conversation_id": "ac2175df14d36caf64e9a578fad89070",
    #        "interaction_id": "515435468500047-1628507537000",
    #        "message_type": "normal",
    #        "actor_type": "agent",
    #        "created_time": "2021-08-17T08:06:22.803Z",
    #        "user_id": "Denise_aliasc26ddeed24ad9e8b19a68eb119d6e37c",
    #        "message_source":"web"
    #      }
    #    }
    # }

    @app.route('/', methods=['GET'])
    def do_nothing() -> Tuple[str, int]:
        print("Nothing to see here...", file=sys.stderr)
        return 'err', 404

    @app.route('/freshchat', methods=['POST'])
    def freshchat():
        verif = request.headers.get('X-Freshchat-Signature')
        if verif == None:
            return 'err', 401
        decoded = base64.b64decode(verif)
        hsh = SHA256.new(request.data)
        try:
            pkcs1_15.new(freshchat_public_key).verify(hsh, decoded)
        except (ValueError, TypeError):
            return 'err', 403
        payload = request.json
        message = payload['data']['message']
        conversation_id = message['conversation_id']

        msg = ''
        if message['actor_type'] == 'user':
            resp = freshchat_get_user(message['actor_id'])
            user = resp.json()
            msg += format_freshchat_user(user)
        else:
            resp = freshchat_get_agent(message['actor_id'])
            agent = resp.json()
            msg += f'{agent["first_name"]} {agent["last_name"]} posted:\n'

        for part in message['message_parts']:
            text = part.get('text')
            if text != None:
                msg += text['content'] + '\n'
        msg += f'To respond, enter /freshchat {conversation_id} [!!as:<username>] <text>.'
        resp = mattermost_create_post(MATTERMOST_CHANNEL_ID, msg)
        if resp.status_code == 201:
            return 'ok', 201
        else:
            app.logger.error(f'When posting to Mattermost, got {resp.status_code}:')
            app.logger.error(resp.text)
            return 'err', 500

    @app.route('/mattermost', methods=['POST'])
    def mattermost() -> Tuple[str, int]:
        token = request.form.get('token')
        if token == None:
            return 'err', 401
        if token != MATTERMOST_SLASH_TOKEN:
            return 'err', 403
        raw_user_name = request.form['user_name']
        raw_text = str(request.form['text'])

        app.logger.error(f"mattermost: raw_text = {raw_text}")

        parsing = parse_mattermost_command(raw_text = raw_text, raw_user_name = raw_user_name)
        app.logger.error(f"mattermost: parsing = {parsing}")
        convo_id, message, user_name = parsing

        try:
            actor_id = usernames_to_agents[user_name]
            resp = create_freshchat_message(convo_id, actor_id, message)
            # Responding with 201 Created causes Mattermost to think there was
            # an error. How come the Mattermost API gets to give me a 201, but
            # I can't do the same?
            return "ok", 200
        except KeyError:
            return 'No Freshchat user found!', 500

    # Returns the Response object as defined in the requests library (not Flask)
    def create_freshchat_message(conversation_id, actor_id, content):
        return freshchat_post(
            f'/conversations/{conversation_id}/messages',
            json={
                'message_parts': [
                    {
                        'text': {
                            'content': content
                        }
                    }
                ],
                'app_id': FRESHCHAT_APP_ID,
                'message_type': 'normal',
                'actor_type': 'agent',
                'actor_id': actor_id
            }
        )

    return app
