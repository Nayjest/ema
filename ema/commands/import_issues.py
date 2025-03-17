from dataclasses import dataclass
from datetime import datetime
from itertools import cycle
from time import sleep, time

from rich.pretty import pprint
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from ema.cli import app
import ema.env as env
import ema.db as db

@dataclass
class Task:
    uuid: str
    title: str
    description: str
    state: str
    assignee: str
    team: str

def user_view(record: dict | None):
    return f"@{record['displayName']}({record['name']})" if record else None

def dt(field):
    if not field:
        return None
    return datetime.fromisoformat(field).strftime("%Y-%m-%d %H:%M:%S")

def process_task(task):
    pprint(task)
    issues_table = Table("issues", db.db_metadata, autoload_with=db.db_engine)
    comments = "\n---\n".join([
        f"[{dt(c['createdAt'])}] {user_view(c['user'])}: {c['body']}"
        for c in task["comments"]["nodes"]
    ])
    attachments = "\n---\n".join([
        f"[{dt(a['createdAt'])}] {user_view(a['creator'])}: [{a['url']}]({a['title']})"
        for a in task["attachments"]["nodes"]
    ])
    data = dict(
        uuid=task["id"],
        id=task["identifier"],
        title=task["title"],
        description=task["description"],
        state=task["state"]["name"],
        assignee=user_view(task["assignee"]),
        comments = comments,
        created_at=dt(task["createdAt"]),
        canceled_at=dt(task["canceledAt"]),
        added_to_cycle_at=dt(task["addedToCycleAt"]),
        added_to_project_at=dt(task["addedToProjectAt"]),
        added_to_team_at=dt(task["addedToTeamAt"]),
        archived_at=dt(task["archivedAt"]),
        attachments=attachments,
        # attachments = task["attachments"]["nodes"],
        children=', '.join([i["identifier"] for i in task["children"]["nodes"]]),
        cycle=task["cycle"]["number"] if task["cycle"] else None,
        due_date=dt(task["dueDate"]),
        estimate=task["estimate"],
        labels=', '.join([i["name"] for i in task["labels"]["nodes"]]),
        priority=task["priority"],
        priority_label=task["priorityLabel"],

        project=task["project"]["name"] if task["project"] else None,
        url=task["url"],
        snoozed_by=user_view(task["snoozedBy"]),
        snoozed_until=dt(task["snoozedUntilAt"]),
        started_at=dt(task["startedAt"]),
        started_triage_at=dt(task["startedTriageAt"]),
        subscribers=', '.join([user_view(i) for i in task["subscribers"]["nodes"]]),
        team=f"{task['team']['name']}" if task["team"] else None,
        trashed=task["trashed"],
        triaged_at=dt(task["triagedAt"]),
        updated_at=dt(task["updatedAt"]),
    )
    with db.session() as ses:
        stmt = insert(issues_table).values(data)
        stmt = stmt.on_duplicate_key_update(
            **{k: stmt.inserted[k] for k in data.keys()}
        )
        # For PostgreSQL
        # stmt = stmt.on_conflict_do_update(index_elements=['uuid'],  set_={k: stmt.excluded[k] for k in data.keys()})
        ses.execute(stmt)
        ses.commit()
    # with db.session() as ses:
    #     try:
    #         ses.execute(issues_table.insert().values(data))
    #         ses.commit()
    #     except Exception as e:
    #         # If a duplicate key error occurs, update the existing record
    #         ses.rollback()
    #         update_stmt = issues_table.update().where(issues_table.c.uuid == task["id"]).values(data)
    #         ses.execute(update_stmt)
    #         ses.commit()



@app.command()
def import_issues():
    t = time()
    env.linear_api.fetch_all_issues(callback=process_task)
    print(f"Done in {time() - t:.2f}s")