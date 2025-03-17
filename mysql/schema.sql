CREATE DATABASE IF NOT EXISTS ema;
USE ema;

CREATE TABLE issues (
    uuid VARCHAR(36) PRIMARY KEY,
    id VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    state VARCHAR(36), -- Stores state details (e.g., {"name": "In Progress"})
    assignee VARCHAR(255), -- Stores assignee details (e.g., {"displayName": "vitalii.stepanenko"})
    comments TEXT, -- Stores all comments as a JSON array
    archived_at TIMESTAMP,
    attachments TEXT, -- Stores all attachments as a JSON array
    children TEXT, -- Stores all children as a JSON array
    cycle INT,
    due_date TIMESTAMP,
    estimate INT,
    labels VARCHAR(255), -- Stores all labels as a JSON array
    parent VARCHAR(36),
    priority INT,
    priority_label VARCHAR(255),
    project VARCHAR(255), -- Stores project details (e.g., {"id": "...", "name": "...", "lead": {"displayName": "kristi"}})
    url VARCHAR(255),
    snoozed_by VARCHAR(255),
    snoozed_until TIMESTAMP,
    subscribers TEXT,
    team VARCHAR(255), -- Stores team details (e.g., {"name": "Data Analyzer"})
    trashed BOOLEAN,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    started_triage_at TIMESTAMP,
    triaged_at TIMESTAMP,
    added_to_cycle_at TIMESTAMP,
    added_to_project_at TIMESTAMP,
    added_to_team_at TIMESTAMP,
    updated_at TIMESTAMP,
    canceled_at TIMESTAMP
);