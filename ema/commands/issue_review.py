from datetime import datetime, timedelta
from time import time
import textwrap

import microcore as mc
import typer
from microcore import ui
from slack_bolt import App

from ema.cli import app
import ema.db as db
from ema.commands.slack import SlackConfig
from ema.utils import format_dt, first_name, nick_name, full_name


@app.command()
def review(
    from_date: str = typer.Option(
        None,
        "--from",
        "-f",
        help="Will select only issues created after this date"
    ),
    notify: bool = False
):
    t = time()
    print(ui.magenta("---==[[Send issue reviews]]==---"))
    if not from_date:
        from_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d 00:00:00")
    print(f"  - From date: {ui.green(from_date)}")
    print(f"  - Send Slack notifications: [{ui.green('on' if notify else 'off')}]")
    data = mc.storage.read_json("issue_reviews.json", {})
    issues = db.sql(
        """
        SELECT * FROM issues 
        WHERE created_at > :from_date
        AND state in ('Triage', 'To Do', 'Todo', 'Backlog') 
        ORDER BY created_at
        """,
        dict(from_date=from_date)
    )

    qty_with_proposals = 0
    qty_new = 0
    for issue in issues:
        print(mc.utils.dedent(
            f"""
        {ui.green(issue['id'])} by {issue['creator']} {issue['created_at']} ({issue['state']})... 
        """
        ), end='')
        if issue["id"] in list(data.keys()):
            print(ui.yellow("already reviewed"))
            continue
        qty_new += 1
        res: dict = mc.llm(mc.tpl("review_issue.j2", issue=issue, indent = textwrap.indent)).parse_json()
        # remove proposals from list if "replace_from" is empty
        # (likely empty description)
        res["proposals"] = [p for p in res["proposals"] if p.get("replace_from")]
        have_proposals = len(res["proposals"])
        print(ui.yellow(len(res["proposals"])) + " proposals" if have_proposals else ui.green("ok"))
        data[issue["id"]] = {"review_date": format_dt(datetime.now())}
        if have_proposals:
            qty_with_proposals += 1
            data[issue["id"]] = {
                **data[issue["id"]],
                "id": issue["id"],
                "author": issue["creator"],
                "title": issue["title"],
                "url": issue["url"],
                **res
            }
        mc.storage.write_json("issue_reviews.json", data, backup_existing=False)
    print(f"Review completed in {ui.green(round(time()-t,2))} seconds.")
    print(f"Analyzed {ui.green(qty_new)} new Linear issues, made proposals to {qty_with_proposals} of them.")
    if notify and qty_with_proposals:
        send_issue_reviews()


@app.command()
def send_issue_reviews():
    print(ui.magenta("---==[[Send issue reviews]]==---"))
    config = SlackConfig()
    slack_app = App(token=config.bot_token, signing_secret=config.signing_secret)
    data = mc.storage.read_json("issue_reviews.json", {})

    # Fetch all Slack users to verify nicknames/full names
    slack_users = slack_app.client.users_list().get("members", [])
    print(ui.yellow(f"Found {len(slack_users)} Slack users"))
    def find_slack_user(nickname, full_name):
        for user in slack_users:
            profile = user.get("profile", {})
            slack_full_name = profile.get("real_name", "").lower()
            slack_nickname = profile.get("display_name", "").lower()
            if nickname.replace('@', '').lower() == slack_nickname or full_name.lower() == slack_full_name:
                return user["id"]
        return None

    for issue_id, issue in data.items():
        if not issue or issue.get("notified") or not issue.get("proposals"):
            continue  # Skip already notified or irrelevant issues


        slack_user_id = find_slack_user(nn:=nick_name(issue["author"]), fn:=full_name(issue["author"]))

        if not slack_user_id:
            print(ui.red(f"Slack user not found for nickname '{nn}' or full name '{fn}'. Skipping."))
            continue

        message = mc.tpl(
            "slack_issue_review_result.j2",
            issue=issue,
            first_name=first_name(issue["author"]),
        )
        print(ui.yellow(f"Sending notification for issue {issue_id} to {issue['author']}({slack_user_id})"))
        response = slack_app.client.chat_postMessage(
            channel=slack_user_id,
            text=message,
            unfurl_links=False,
            unfurl_media=False
        )

        if response["ok"]:
            print(ui.green(f"Notification sent for issue {issue_id}"))
            issue["notified"] = True
            mc.storage.write_json("issue_reviews.json", data, backup_existing=False)
        else:
            print(ui.red(f"Failed to notify for issue {issue_id}: {response['error']}"))
