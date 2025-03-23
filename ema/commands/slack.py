from dataclasses import field, dataclass

from microcore import ui
from rich.pretty import pprint
from slack_bolt import App as SlackApp
from slack_bolt.adapter.socket_mode import SocketModeHandler

from ema.agent import answer
from ema.interfaces import Interface
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


def split_message_by_lines(message, max_length=3000):
    """Splits a long message into chunks, ensuring lines are not broken."""
    lines = message.split("\n")
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:  # +1 for newline
            chunks.append(current_chunk.strip())  # Save the current chunk
            current_chunk = ""  # Start a new chunk
        current_chunk += line + "\n"

    if current_chunk.strip():  # Add any remaining lines
        chunks.append(current_chunk.strip())


    return chunks

def message_handler(body, say, logger, slack_app):
    """Handles direct messages to the bot."""
    user_id = body["event"]["user"]
    text = body["event"]["text"]
    user = slack_app.client.users_info(user=user_id).data["user"]
    name = user.get("real_name") or user.get("name")
    vars = {}
    if user.get("tz"):
        tz = user["tz"]
        if user["tz_label"]:
            tz = f"{tz} ({user['tz_label']})"
        vars["tz"] = tz
    if user.get("profile"):
        vars["title"] = user["profile"].get("title")



    pprint(user)
    print(
        f"FROM {ui.green('@'+user['name'])}",
        ui.gray(f"({user['real_name']}, {user['profile']['title']}):"),
        "\n>",
        ui.cyan(text)
    )

    thinking_message = say({"text":"🤔","mrkdwn": True})
    ai_answer = answer(text, name, vars, interface=Interface.SLACK)
    chunks = split_message_by_lines(ai_answer)
    slack_app.client.chat_update(
        channel=body["event"]["channel"],
        ts=thinking_message["ts"],
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": chunks[0]}}]
    )

    for chunk in chunks[1:]:
        slack_app.client.chat_postMessage(
            channel=body["event"]["channel"],
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": chunk}}]
        )

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
