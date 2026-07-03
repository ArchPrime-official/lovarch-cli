"""Platform workflows — Lovarch's product features exposed to the CLI/MCP.

Each workflow wraps an existing platform Edge Function (the same ones the web
app uses), called with the user's premium session so credits are debited
identically to the app. Cost is reported ONLY in the user's credits.
"""
from lovarch_cli.workflows.platform import PlatformWorkflows, WorkflowError

__all__ = ["PlatformWorkflows", "WorkflowError"]
