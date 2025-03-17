import os

from rich.pretty import pprint
import ema.env as env
from ema.cli_app import app

@app.command(name="team")
def get_team(name_or_key: str):
    print("Fetching team id for team:", name_or_key)
    team = env.linear_api.find_team(name_or_key)
    pprint(team)

@app.command(name="teams")
def get_teams():
    teams = env.linear_api.teams()
    pprint(teams)

@app.command(name="issues")
def get_issues(team: str):
    issues = env.linear_api.issues(team)
    pprint(issues)
    print("Total issues:", len(issues))

@app.command(name="all_issues")
def get_all_issues():
    issues = env.linear_api.fetch_all_issues()
    pprint(issues)
    print("Total issues:", len(issues))
    import microcore as mc
    mc.storage.write_json("all_issues.json", issues)

@app.command(name="issue")
def get_issue(identifier: str):
    issue = env.linear_api.issue(identifier)
    pprint(issue)


from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
@app.command(name="schema")
def schema():
    res = env.linear_api.schema()
    pprint(res)

@app.command(name="ask")
def ask(question: str):
    usr = os.getenv("CLI_USER")
    question = f"[name='{usr}']: {question}"
    print("Asking question:", question)

    from ema.agent import answer
    answer(question)
#
@app.command(name="gql")
def gql_query(query: str):
    print("Executing query:", query)
    result = env.linear_api.request(query)
    pprint(result)



# @app.command()
# def last_task():
#     tid = fetch_team_id(config, config.linear_team_key)
#     task = get_latest_issue(config, tid)
#     pprint(task)