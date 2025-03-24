import textwrap
from datetime import datetime
from time import time
from enum import Enum


from rich.pretty import pprint
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn,
    TimeElapsedColumn,
)
from sqlalchemy import Table, text, update
from sqlalchemy.dialects.mysql import insert
import microcore as mc
from microcore import ui

from ema.cli import app
import ema.env as env
import ema.db as db


@app.command()
def test():
    def date_format(dt: str | datetime) -> str:
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %B, %H:%M")

    with db.session() as ses:
        result = ses.execute(text("SELECT * FROM issues limit 1"))
        rows = result.mappings().all()  # returns list of dict-like RowMapping
        i = dict(rows[0])
        pprint(i, expand_all=True, indent_guides=True)
        view = mc.tpl(
            "issue_view.j2", issue=rows[0], indent=textwrap.indent, date_format=date_format
        )
        print(mc.ui.blue(view))


@app.command("index-all-content")
def index_all_content():
    def date_format(dt: str | datetime) -> str:
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %B, %H:%M")

    start = time()
    mc.texts.clear("issues")
    with db.session() as ses:
        result = ses.execute(text("SELECT * FROM issues"))
        rows = result.mappings().all()
        issues_table = Table("issues", db.db_metadata, autoload_with=db.db_engine)

        with Progress() as progress:
            task = progress.add_task("[cyan]Indexing issues...", total=len(rows))
            for row in rows:
                issue = dict(row)
                rendered = mc.tpl(
                    "issue_view.j2",
                    issue=row,
                    indent=textwrap.indent,
                    date_format=date_format,
                )
                mc.texts.save("issues", rendered, {"issue_id": issue["id"]})
                ses.execute(
                    update(issues_table)
                    .where(issues_table.c.id == issue["id"])
                    .values(all_content=rendered)
                )

                progress.update(task, advance=1)

        ses.commit()

    duration = time() - start
    print(mc.ui.green(f"\n✅ Done: {len(rows)} issues updated."))
    print(mc.ui.green(f"🕒 Took {duration:.2f} seconds."))


@app.command("index-vec")
def index_vec():
    start = time()
    collection = "issues"
    print("Clearing vector db...")
    mc.texts.clear(collection)

    print("Querying RDBMS...")
    with db.session() as ses:
        result = ses.execute(text("SELECT id, all_content FROM issues"))
        rows = result.mappings().all()

    print("Preparing data for vector db...")
    data = [[row["all_content"], {"issue_id": row["id"]}] for row in rows]

    chunk_size = 100
    total_chunks = (len(data) + chunk_size - 1) // chunk_size
    print(f"Saving to vector db {len(data)} items in {total_chunks} chunks...")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("Chunk {task.completed}/{task.total}"),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("[green]Saving chunks...", total=total_chunks)

        for i in range(0, len(data), chunk_size):
            chunk = data[i: i + chunk_size]
            mc.texts.save_many(collection, chunk)
            progress.update(task, advance=1)

    print(f"Done in {time() - start:.2f} seconds.")


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
    IN_DEVELOPMENT = "In Development"
    WAITING_FOR_MERGE = "Waiting for Merge"
    DESIGN_REVIEW = "Design Review"
    INITIAL_PRODUCT_REVIEW = "Initial Product Review"
    UAT = "UAT"
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
            State.COMPLETE,
        ]


def user_view(record: dict | None):
    return f"@{record['displayName']}({record['name']})" if record else None


def dt(field):
    if not field:
        return None
    return datetime.fromisoformat(field).strftime("%Y-%m-%d %H:%M:%S")


def dt_human(dt: str | datetime) -> str:
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d %B, %H:%M")


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
    issues_table = Table("issues", db.db_metadata, autoload_with=db.db_engine)

    task["history"]["nodes"].sort(key=lambda x: x["createdAt"])
    task["comments"]["nodes"].sort(key=lambda x: x["createdAt"])

    comments = "\n---\n".join(
        [
            f"[{dt(c['createdAt'])}] {user_view(c['user'])}: {c['body']}"
            for c in task["comments"]["nodes"]
        ]
    )
    attachments = "\n---\n".join(
        [
            f"[{dt(a['createdAt'])}] {user_view(a['creator'])}: [{a['url']}]({a['title']})"
            for a in task["attachments"]["nodes"]
        ]
    )
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
        comments=comments,
        milestone=task["projectMilestone"]["name"] if task["projectMilestone"] else None,
        created_at=dt(task["createdAt"]),
        canceled_at=dt(task["canceledAt"]),
        added_to_cycle_at=dt(task["addedToCycleAt"]),
        added_to_project_at=dt(task["addedToProjectAt"]),
        added_to_team_at=dt(task["addedToTeamAt"]),
        archived_at=dt(task["archivedAt"]),
        attachments=attachments,
        # attachments = task["attachments"]["nodes"],
        children=", ".join([i["identifier"] for i in task["children"]["nodes"]]),
        cycle=task["cycle"]["number"] if task["cycle"] else None,
        due_date=dt(task["dueDate"]),
        estimate=task["estimate"],
        labels=", ".join([i["name"] for i in task["labels"]["nodes"]]),
        priority=task["priority"],
        priority_label=task["priorityLabel"],
        project=task["project"]["name"] if task["project"] else None,
        url=task["url"],
        snoozed_by=user_view(task["snoozedBy"]),
        snoozed_until=dt(task["snoozedUntilAt"]),
        started_at=dt(task["startedAt"]),
        started_triage_at=dt(task["startedTriageAt"]),
        subscribers=", ".join([user_view(i) for i in task["subscribers"]["nodes"]]),
        team=f"{task['team']['name']}" if task["team"] else None,
        trashed=task["trashed"],
        triaged_at=dt(task["triagedAt"]),
        completed_at=dt(task["completedAt"]),
        updated_at=dt(task["updatedAt"]),
    )
    data["all_content"] = mc.tpl(
        "issue_view.j2",
        issue=data,
        indent=textwrap.indent,
        date_format=dt_human,
    )
    with db.session() as ses:
        stmt = insert(issues_table).values(data)
        stmt = stmt.on_duplicate_key_update(**{k: stmt.inserted[k] for k in data.keys()})
        # For PostgreSQL
        # stmt = stmt.on_conflict_do_update(index_elements=['uuid'],  set_={k: stmt.excluded[k] for k in data.keys()})
        ses.execute(stmt)
        ses.commit()
    mc.texts.delete("issues", what={"issue_id": data["id"]})
    mc.texts.save("issues", data["all_content"], {"issue_id": data["id"]})


@app.command("index-issues", help="Import issues from Linear")
@app.command("import_issues", hidden=True)
def index_issues(force: bool = False, fast: bool = False):
    print(ui.magenta("--==[[ Linear Issues Indexing ]]==--"))
    EPOCH_START = "1970-01-01"
    idx_info_file = "idx_info/linear_issues.json"
    last_indexed = mc.storage.read_json(idx_info_file, {}).get("last_indexed", EPOCH_START)

    if force:
        last_indexed = EPOCH_START
        mc.ui.warning("--force: True", mc.ui.red("(!) database will be truncated"))
        db.sql("DELETE FROM issues WHERE true")
        mc.texts.clear("issues")
        mc.storage.delete(idx_info_file)

    if fast:
        mc.ui.warning(
            "--fast: True", mc.ui.red("progress will not reflect the actual number of issues")
        )
        issue_qty = 20  # arbitrary small start
    else:
        print("Calculating number of issues to index...")
        issue_qty = env.linear_api.fetch_issue_qty(updated_after=last_indexed)
        print(f"Total issues to index: {issue_qty}")

    print(
        f"Last indexed: "
        f"{mc.ui.green(last_indexed) if last_indexed != EPOCH_START else mc.ui.red('never')}"
    )

    records = []
    t = time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        TextColumn("Imported: {task.completed}/{task.total}"),
        TimeElapsedColumn(),
    ) as progress:

        task_id = progress.add_task("[cyan]Indexing issues...", total=issue_qty)

        def progress_callback(issue):
            process_task(issue)
            records.append(issue)

            # Dynamically increase total in fast mode
            if fast and progress.tasks[task_id].completed >= progress.tasks[task_id].total:
                progress.update(task_id, total=progress.tasks[task_id].total * 5)

            progress.advance(task_id)

        env.linear_api.fetch_all_issues(callback=progress_callback, updated_after=last_indexed)

    duration = time() - t

    idx_info = {
        "last_indexed": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration,
        "updated_records": len(records),
    }
    mc.storage.write_json(idx_info_file, idx_info, backup_existing=False)
