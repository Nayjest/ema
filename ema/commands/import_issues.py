from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from time import time

from rich.pretty import pprint
from sqlalchemy import Table, text
from sqlalchemy.dialects.mysql import insert

from ema.cli import app
import ema.env as env
import ema.db as db

@app.command()
def test():
    with db.session() as ses:
        print(ses.execute(text("SELECT 1")).fetchall())

class State(str, Enum):
    DONE = "Done"
    TO_DO = "To Do"
    CANCELED = "Canceled"
    IN_REVIEW = "In Review"
    BACKLOG = "Backlog"
    DUPLICATE = "Duplicate"
    IN_PROGRESS = "In Progress"
    NOT_APPLICABLE = "Not applicable"
    READY_TO_TEST = "Ready to Test"
    IN_UAT = "In UAT"
    CONSIDER_FOR_FUTURE = "Consider for Future"
    TRIAGE = "Triage"
    FALSE_POSITIVE = "False Positive"
    SUSPENDED = "Suspended"
    CONVERTED_TO_STORY = "Converted to Story"
    NEEDS_CLARIFICATION = "Needs Clarification"
    PATCH_IN_UAT = "Patch in UAT"
    CHROMIUM = "Chromium"
    IN_TESTING = "In Testing"
    ON_HOLD = "On Hold"
    NEEDS_STORY = "Needs Story"
    TO_TEST = "To Test"
    IN_DEVELOPMENT= "In Development"
    WAITING_FOR_MERGE = "Waiting for Merge"
    DESIGN_REVIEW = "Design Review"
    INITIAL_PRODUCT_REVIEW = "Initial Product Review"
    UAT= "UAT"
    CODE_REVIEW = "Code Review"
    RESEARCH = "Research"
    WONT_DO = "Won't Do"
    COMPLETE = "Complete"
    DESIGN = "Design"

    @staticmethod
    def non_doer_states():
        return [
            State.DONE,
            State.CANCELED,
            State.IN_REVIEW,
            State.IN_UAT,
            State.IN_REVIEW,
            State.READY_TO_TEST,
            State.DONE,
            State.FALSE_POSITIVE,
            State.SUSPENDED,
            State.NEEDS_CLARIFICATION,
            State.PATCH_IN_UAT,
            State.CHROMIUM,
            State.IN_TESTING,
            State.TO_TEST,
            State.DESIGN_REVIEW,
            State.INITIAL_PRODUCT_REVIEW,
            State.UAT,
            State.CODE_REVIEW,
            State.WONT_DO,
            State.COMPLETE
        ]

def user_view(record: dict | None):
    return f"@{record['displayName']}({record['name']})" if record else None

def dt(field):
    if not field:
        return None
    return datetime.fromisoformat(field).strftime("%Y-%m-%d %H:%M:%S")

def identify_doer(task):
    nodes = task["history"]["nodes"]
    items = [i for i in nodes if i["fromState"] and i["toState"]]
    for i in items:
        if i["toState"]["name"] == "In Progress":
            return user_view(i["actor"])
    if task["state"]["name"] in State.non_doer_states():
        for i in items:
            if i["fromState"]["name"] == "In Progress":
                return user_view(i["actor"])
    return user_view(task["assignee"])


def historical_assignees(task):
    nodes = task["history"]["nodes"]
    items = [user_view(i["toAssignee"]) for i in nodes if i["toAssignee"]]
    items += [user_view(i["fromAssignee"]) for i in nodes if i["fromAssignee"]]
    if task["assignee"]:
        items += [user_view(task["assignee"])]
    return ", ".join(set(items))

def process_task(task):
    pprint(task)
    issues_table = Table("issues", db.db_metadata, autoload_with=db.db_engine)

    task["history"]["nodes"].sort(key=lambda x: x["createdAt"])
    task["comments"]["nodes"].sort(key=lambda x: x["createdAt"])

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
        current_assignee=user_view(task["assignee"]),
        doer=identify_doer(task),
        historical_assignees=historical_assignees(task),
        creator=user_view(task["creator"]),
        comments = comments,
        milestone = task["projectMilestone"]["name"] if task["projectMilestone"] else None,
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
        completed_at=dt(task["completedAt"]),
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


@app.command()
def import_issues():
    t = time()
    env.linear_api.fetch_all_issues(callback=process_task)
    print(f"Done in {time() - t:.2f}s")