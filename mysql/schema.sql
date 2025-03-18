CREATE DATABASE IF NOT EXISTS ema;
USE ema;

-- <AI>
CREATE TABLE issues (
    uuid VARCHAR(36) PRIMARY KEY, -- linear internal id for GraphQL
    id VARCHAR(50) NOT NULL, -- human-readable id
    title TEXT NOT NULL,
    description TEXT,
    state VARCHAR(36), -- Popular values: Done, To Do, Canceled, In Review, Backlog, Duplicate, In Progress, Not applicable, Ready to Test, In UAT, Consider For Future, Triage, Suspended, Needs Clarification, In Testing, On Hold, To Test, In Development, Waiting for Merge, ...
    current_assignee VARCHAR(255), -- @nickname(FirstName LastName), current assignee (typically emptied when moved to Done)
    doer VARCHAR(255), -- Person who worked on the issue according to history or the current assignee
    historical_assignees TEXT, -- @nickname(FirstName LastName) separated by comma+space
    creator VARCHAR(255), -- @nickname(FirstName LastName)
    comments MEDIUMTEXT,
    milestone VARCHAR(255),
    archived_at TIMESTAMP,
    attachments TEXT,
    children TEXT, -- human-readable ids separated by comma+space
    cycle INT,
    due_date TIMESTAMP,
    estimate INT,
    labels VARCHAR(255),
    parent VARCHAR(36), -- human-readable id
    priority INT, -- 0,1,2,3,4
    priority_label VARCHAR(255), -- No priority, Urgent, High, Medium, Low
    project VARCHAR(255),
    url VARCHAR(255),
    snoozed_by VARCHAR(255), -- @nickname(FirstName LastName)
    snoozed_until TIMESTAMP,
    subscribers TEXT, -- @nickname(FirstName LastName) separated by comma+space
    team VARCHAR(255),
    trashed BOOLEAN,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    started_triage_at TIMESTAMP,
    triaged_at TIMESTAMP,
    added_to_cycle_at TIMESTAMP,
    added_to_project_at TIMESTAMP,
    added_to_team_at TIMESTAMP,
    updated_at TIMESTAMP,
    canceled_at TIMESTAMP
);
-- </AI>