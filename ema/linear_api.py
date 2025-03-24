from dataclasses import dataclass, field
from datetime import datetime

import requests
from rich.pretty import pprint
import microcore as mc
from microcore import ui

from ema.utils import update_object_from_env

ISSUE_FRAGMENT = """
fragment IssueFields on Issue {
    id
    identifier
    title
    description
    state { name }
    assignee { displayName, name }
    creator { displayName, name }
    comments {
        nodes {
            user { displayName, name }
            body
            createdAt
        }
    }
    projectMilestone { name }
    createdAt
    completedAt
    canceledAt
    addedToCycleAt
    addedToProjectAt
    addedToTeamAt
    archivedAt
    attachments {
        nodes {
            id
            title
            url
            creator {
                name
                displayName
            }
            createdAt
        }
    }
    children {
        nodes {
            identifier
        }
    }
    cycle {
        id
        name
        number
        team {
            id
            name
        }
    }
    dueDate
    estimate
    history {
        nodes {
            actor { name displayName }
            archived
            archivedAt
            attachment {
                id
                title
                url
            }
            autoArchived
            autoClosed
            createdAt
            descriptionUpdatedBy { name displayName }
            fromAssignee { name displayName }
            fromCycle { id name number }
            fromEstimate
            fromPriority
            fromState { name }
            fromTitle
            fromDueDate
            toAssignee { name displayName }
            toCycle { id name number }
            toEstimate
            toPriority
            toState { name }
            toTitle
            toDueDate
            trashed
            addedLabels { name }
            removedLabels { name }
        }
    }
    labels {
        nodes {
            name
        }
    }
    number
    parent { id identifier title }
    priority
    priorityLabel
    project {
        id
        lead { name displayName }
        name
        status { name }
        url
    }
    snoozedBy { name displayName }
    snoozedUntilAt
    startedAt
    startedTriageAt
    subscribers {
        nodes { displayName name }
    }
    team { name }
    trashed
    triagedAt
    updatedAt
    url
}
"""


@dataclass
class LinearConfig:
    _ENV_PREFIXES = ["LINEAR_"]
    api_url = "https://api.linear.app/graphql"
    api_key: str = field(default="")
    team_keys: list[str] = field(default_factory=list)

    def __post_init__(self):
        update_object_from_env(self, prefixes=self._ENV_PREFIXES)


@dataclass
class Team:
    id: str
    name: str
    key: str

    def __str__(self):
        return f"{self.name} ({self.key})"


class LinearApi:
    config: LinearConfig

    def __init__(self, config: LinearConfig):
        self.config = config

    @property
    def headers(self):
        return {"Authorization": self.config.api_key, "Content-Type": "application/json"}

    def request(self, query: str, variables: dict = None) -> dict:
        response = requests.post(
            self.config.api_url, headers=self.headers, json={"query": query, "variables": variables}
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            try:
                setattr(e, "gql_errors", response.json()["errors"])
                print(ui.red("❌  Linear GraphQL Error:"))
                print(ui.magenta(query.strip()))
                pprint(variables)
                pprint(e.gql_errors)
                exit()
            finally:
                ...

        data = response.json()
        return data["data"]

    def issues(self, team: str) -> list[dict]:
        team = self.find_team(team)
        data = self.request(
            """
        {
            issues (
                first: 200
                filter: {
                    team: { id: { eq: "%s" } }
                    state: { name: {neq: "Done"} }
                }
            ) {
                nodes {
                    identifier
                    id
                    title
                    state { name }
                    description
                    assignee { displayName }
                    # comments { nodes {
                    #     user { displayName }
                    #     body
                    # } }
                }
            }
        }
        """
            % team.id
        )
        return data["issues"]["nodes"]

    def issue(self, uuid: str) -> dict:
        query = """
            %s
            query {
                issues(filter: { id: { eq: "%s" } }) {
                    nodes {
                        ...IssueFields
                    }
                }
            }
            """ % (
            ISSUE_FRAGMENT,
            uuid,
        )
        variables = {}
        response = self.request(query, variables)
        return response["issues"]["nodes"][0]

    def teams(self) -> list[Team]:
        teams = []
        has_next_page = True
        cursor = None

        while has_next_page:
            query = """
            query ($cursor: String) {
              teams(first: 50, after: $cursor) {
                nodes { id name key }
                pageInfo { hasNextPage endCursor }
              }
            }
            """

            variables = {"cursor": cursor}
            data = self.request(query, variables)
            nodes = data["teams"]["nodes"]
            page_info = data["teams"]["pageInfo"]
            teams.extend(nodes)
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]
        return [Team(**d) for d in teams]

    def find_team(self, value: str) -> Team:
        teams = self.teams()
        for team in teams:
            if team.name.lower() == value or team.key == value or team.id == value:
                return team

        raise ValueError("❌ Team not found!")

    def fetch_schema(self):
        """
        Fetches the GraphQL schema from Linear API
        in a reduced form while keeping all necessary fields and filtering methods.

        Returns:
            dict: The optimized schema.
        """
        print(ui.blue("🔍 Fetching Linear API schema..."))

        # First, get all type names while ignoring introspection types
        basic_query = """
        {
          __schema {
            types {
              name
              kind
            }
          }
        }
        """
        basic_schema = self.request(basic_query)

        # Filter out introspection and mutation types
        type_names = [
            t["name"]
            for t in basic_schema["__schema"]["types"]
            if not t["name"].startswith("__") and t["kind"] != "MUTATION"
        ]

        print(ui.green(f"✓ Found {len(type_names)} relevant types in schema"))

        # Fetch details for each type but omit descriptions and deeply nested ofType details
        complete_schema = {"types": {}}

        for i, type_name in enumerate(type_names):
            if i % 10 == 0:
                print(ui.blue(f"⏳ Fetching type details... ({i}/{len(type_names)})"))

            type_query = f"""
            {{
              __type(name: "{type_name}") {{
                name
                kind
                fields {{
                  name
                  type {{
                    name
                    kind
                    ofType {{
                      name
                      kind
                    }}
                  }}
                }}
                inputFields {{
                  name
                  type {{
                    name
                    kind
                    ofType {{
                      name
                      kind
                    }}
                  }}
                }}
                enumValues {{
                  name
                }}
              }}
            }}
            """

            type_data = self.request(type_query)
            if type_data and "__type" in type_data:
                complete_schema["types"][type_name] = type_data["__type"]

        print(
            ui.green(
                f"✓ Schema with {len(complete_schema['types'])} essential types successfully retrieved"
            )
        )

        return complete_schema

    #
    # def fetch_schema_full(self):
    #     """
    #     Fetches the GraphQL schema from Linear API in smaller chunks to stay within complexity limits.
    #
    #     Args:
    #         save_path: Optional path to save schema to a JSON file
    #
    #     Returns:
    #         dict: The assembled schema
    #     """
    #     print(ui.blue("🔍 Fetching Linear API schema..."))
    #
    #     # First get all type names (lower complexity query)
    #     basic_query = """
    #     {
    #       __schema {
    #         types {
    #           name
    #           kind
    #         }
    #       }
    #     }
    #     """
    #
    #     basic_schema = self.request(basic_query)
    #
    #     # Extract the type names, skipping introspection types
    #     type_names = [t["name"] for t in basic_schema["__schema"]["types"]
    #                   if not t["name"].startswith("__")]
    #
    #     print(ui.green(f"✓ Found {len(type_names)} types in schema"))
    #
    #     # Now get details for each type and build a complete schema
    #     complete_schema = {"types": {}}
    #
    #     for i, type_name in enumerate(type_names):
    #         # Show progress
    #         if i % 10 == 0:
    #             print(ui.blue(f"⏳ Fetching type details... ({i}/{len(type_names)})"))
    #
    #         # Query for a specific type's details
    #         type_query = f"""
    #         {{
    #           __type(name: "{type_name}") {{
    #             name
    #             kind
    #             description
    #             fields {{
    #               name
    #               description
    #               args {{
    #                 name
    #                 description
    #                 type {{ name kind }}
    #                 defaultValue
    #               }}
    #               type {{
    #                 name
    #                 kind
    #                 ofType {{
    #                   name
    #                   kind
    #                   ofType {{
    #                     name
    #                     kind
    #                   }}
    #                 }}
    #               }}
    #             }}
    #             inputFields {{
    #               name
    #               description
    #               type {{
    #                 name
    #                 kind
    #                 ofType {{
    #                   name
    #                   kind
    #                 }}
    #               }}
    #               defaultValue
    #             }}
    #             enumValues {{
    #               name
    #               description
    #             }}
    #             interfaces {{
    #               name
    #             }}
    #           }}
    #         }}
    #         """
    #
    #         type_data = self.request(type_query)
    #         if type_data and "__type" in type_data:
    #             complete_schema["types"][type_name] = type_data["__type"]
    #
    #     print(ui.green(f"✓ Schema with {len(complete_schema['types'])} types successfully retrieved"))
    #
    #     return complete_schema

    def schema(self):
        if mc.storage.exists("linear_schema.json"):
            return mc.storage.read_json("linear_schema.json")
        schema = self.fetch_schema()
        mc.storage.write_json("linear_schema.json", schema, backup_existing=False)
        return schema

    def fetch_all_issues(
        self, team: str = None, callback: callable = None, updated_after: datetime | str = None
    ) -> list[dict]:
        """
        Fetches all tasks (issues) from the Linear API.

        Args:
            team (str, optional): The team name, key, or ID to filter tasks by.
            callback (callable, optional): A function to apply to each fetched issue.
            updated_after (datetime, optional): Only return issues updated after this datetime.

        Returns:
            list[dict]: A list of tasks (issues) with their details.
        """
        tasks = []
        has_next_page = True
        cursor = None

        while has_next_page:
            print(".", end="")

            query = (
                """
            %s
            query ($cursor: String, $teamFilter: IssueFilter) {
              issues(first: 100, after: $cursor, filter: $teamFilter) {
                nodes {
                  ...IssueFields
                }
                pageInfo {
                  hasNextPage
                  endCursor
                }
              }
            }
            """
                % ISSUE_FRAGMENT
            )

            variables = {"cursor": cursor}
            filter_criteria = {}

            if team:
                team_obj = self.find_team(team)
                filter_criteria["team"] = {"id": {"eq": team_obj.id}}

            if updated_after:
                if isinstance(updated_after, str):
                    updated_after = datetime.fromisoformat(updated_after)
                iso_time = updated_after.isoformat()
                filter_criteria["updatedAt"] = {"gt": iso_time}

            if filter_criteria:
                variables["teamFilter"] = filter_criteria

            data = self.request(query, variables)
            if not data or "issues" not in data:
                break

            if callback:
                for task in data["issues"]["nodes"]:
                    callback(task)

            tasks.extend(data["issues"]["nodes"])
            page_info = data["issues"]["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

        return tasks

    def fetch_issue_qty(self, team: str = None, updated_after: datetime | str = None) -> int:
        """
        Counts the number of issues matching the filters via pagination.

        Args:
            team (str, optional): Team name, key, or ID.
            callback (callable, optional): Unused (for signature compatibility).
            updated_after (datetime or str, optional): Only count issues updated after this datetime.

        Returns:
            int: Total number of matching issues.
        """
        count = 0
        has_next_page = True
        cursor = None

        query = """
        query ($cursor: String, $teamFilter: IssueFilter) {
          issues(first: 100, after: $cursor, filter: $teamFilter) {
            nodes { id }  # just grab the minimal field
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """

        variables = {"cursor": cursor}
        filter_criteria = {}

        if team:
            team_obj = self.find_team(team)
            filter_criteria["team"] = {"id": {"eq": team_obj.id}}

        if updated_after:
            if isinstance(updated_after, str):
                updated_after = datetime.fromisoformat(updated_after)
            filter_criteria["updatedAt"] = {"gt": updated_after.isoformat()}

        if filter_criteria:
            variables["teamFilter"] = filter_criteria

        while has_next_page:
            print(".", end="")
            variables["cursor"] = cursor
            data = self.request(query, variables)
            nodes = data["issues"]["nodes"]
            count += len(nodes)
            page_info = data["issues"]["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

        return count


#
# # Fetch and print all teams
# all_teams = fetch_all_teams()
# for team in all_teams:
#     print(team)
#
# def create_headers(api_key):
#     """Returns request headers."""
#     return {
#         "Authorization": api_key,
#         "Content-Type": "application/json"
#     }
#
#
# def fetch_teams(config)->list[dict]:
#     query = """
#         query {
#           teams(first: 50) {
#             nodes {
#               id
#               name
#               key
#             }
#           }
#         }
#         """
#     response = requests.post(
#         config.linear_api_url,
#         json={"query": query},
#         headers=create_headers(config.linear_api_key)
#     )
#     data = response.json()
#     if "errors" in data:
#         print("❌ GraphQL Error:", data["errors"])
#         return None
#     teams = data.get("data", {}).get("teams", {}).get("nodes", [])
#     return teams
#
#
# def fetch_team_id(config, key_or_name=None):
#     teams = fetch_teams(config)
#     for team in teams:
#         if team["name"].lower() == config.linear_team_key.lower() or team["key"] == key_or_name:
#             return team["id"]
#
#     print("❌ Team not found!")
#     return None
#
#
# def get_latest_issue(config, team_id):
#     """Fetches the latest issue from the given team."""
#     query = """
#     query {
#       issues(filter: {team: {id: {eq: "%s"}}}, first: 1, orderBy: createdAt) {
#         nodes {
#       id
#       title
#       description
#       state {
#         name
#       }
#       priority
#       url
#       createdAt
#       updatedAt
#       assignee {
#         name
#       }
#       labels {
#         nodes {
#           name
#         }
#       }
#       project {
#         name
#       }
#       team {
#         name
#       }
#       comments {
#         nodes {
#           body
#           createdAt
#           # author {
#           #   name
#           # }
#         }
#
#     }
#   }
#       }
#     }
#     """ % team_id
#
#     response = requests.post(config.linear_api_url, json={"query": query},
#                              headers=create_headers(config.linear_api_key))
#     data = response.json()
#     pprint(data)
#     if "errors" in data:
#         print("❌ GraphQL Error:", data["errors"])
#         return None
#
#     issues = data.get("data", {}).get("issues", {}).get("nodes", [])
#     return issues[0] if issues else None
#
#
# def add_comment(config, issue_id, text="ок"):
#     """Adds a comment to the specified issue."""
#     mutation = """
#     mutation {
#       commentCreate(input: {issueId: "%s", body: "%s"}) {
#         success
#       }
#     }
#     """ % (issue_id, text)
#
#     response = requests.post(config.linear_api_url, json={"query": mutation},
#                              headers=create_headers(config.linear_api_key))
#     return response.json()
