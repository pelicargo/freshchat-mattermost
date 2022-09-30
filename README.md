# Freshchat integration for mattermost

This is a webservice that forwards messages between Mattermost and FreshChat.

## Dependencies

See `requirements.txt`.

## Environment Variables

It uses the following environment variables:

- `FRESHCHAT_API_URL`: `https://example.freshchat.com/v2`
- `FRESHCHAT_APP_ID`: Under "Integration Settings"
- `FRESHCHAT_PUBLIC_KEY`: See https://support.freshchat.com/en/support/solutions/articles/239404-freshchat-webhooks-payload-structure-and-authentication
- `FRESHCHAT_TOKEN`: See https://support.freshchat.com/en/support/solutions/articles/50000000011-api-tokens
- `MATTERMOST_API_URL`: `https://example.mattermost.com/api/v4`
- `MATTERMOST_BOT_TOKEN`: The personal access token for the bot, see https://developers.mattermost.com/integrate/reference/bot-accounts/
- `MATTERMOST_CHANNEL_ID`: Found under "View Info," in faint gray at the bottom of the panel
- `MATTERMOST_SLASH_TOKEN`: The personal access token for the slash command

## Notes

Set `FLASK_RUN_HOST` and `FLASK_RUN_PORT` to control the listening host/port.

## Service Setup

1. Add a new slash command for Mattermost (https://developers.mattermost.com/integrate/slash-commands/)
and point it to the `/mattermost` endpoint.

2. Register a FreshChat webhook (https://support.freshchat.com/en/support/solutions/articles/239439-conversation-apis-and-webhooks)
and point it to the `/freshchat` endpoint.
