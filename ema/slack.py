from dataclasses import field, dataclass

from microcore import ui
from rich.pretty import pprint
from slack_bolt import App as SlackApp
from slack_bolt.adapter.socket_mode import SocketModeHandler

from ema.utils import update_object_from_env
from ema.cli_app import app as cli_app

@dataclass
class SlackConfig:
    bot_token: str = field(default="")
    app_token: str = field(default="")
    signing_secret: str = field(default="")

    def __post_init__(self):
        update_object_from_env(self, prefixes=["SLACK_"])

def mention_handler(body, say):
    """Handles @mentions to the bot."""
    say("Hello! 👋")

def message_handler(body, say, logger, slack_app):
    """Handles direct messages to the bot."""
    user_id = body["event"]["user"]
    text = body["event"]["text"]
    user = slack_app.client.users_info(user=user_id).data["user"]

    pprint(user)
    print(
        f"FROM {ui.green('@'+user['name'])}",
        ui.gray(f"({user['real_name']}, {user['profile']['title']}):"),
        "\n>",
        ui.cyan(text)
    )

    # Optional: Respond to the user
    say("Got your message! 👍")

@cli_app.command()
def slack():
    """CLI command to start the Slack bot."""
    config = SlackConfig()
    slack_app = SlackApp(token=config.bot_token, signing_secret=config.signing_secret)

    # Register event handlers
    slack_app.event("app_mention")(mention_handler)
    slack_app.event("message")(lambda body, say, logger: message_handler(body, say, logger, slack_app))

    handler = SocketModeHandler(slack_app, config.app_token)
    handler.start()
