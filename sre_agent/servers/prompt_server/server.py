"""A server containing a prompt to trigger the agent."""

from dataclasses import dataclass
from functools import lru_cache

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Support both package (tests) and module-only (container) layouts
try:  # package layout
    from sre_agent.servers.prompt_server.utils.schemas import (
        PromptServerConfig,  # type: ignore
    )
    from sre_agent.servers.prompt_server.utils.url_parser import (
        parse_github_url,  # type: ignore
    )
except ModuleNotFoundError:  # module-only layout inside container
    from utils.schemas import PromptServerConfig  # type: ignore
    from utils.url_parser import parse_github_url  # type: ignore

mcp = FastMCP("sre-agent-prompt")

mcp.settings.host = "127.0.0.1"  # nosec B104
mcp.settings.port = 3001


@lru_cache
def _get_prompt_server_config() -> PromptServerConfig:
    return PromptServerConfig()


@mcp.prompt()
def diagnose(
    service: str,
    slack_channel_id: str,
    repo_url: str | None = None,
    namespace: str | None = None,
    container: str | None = None,
) -> str:
    """Prompt the agent to perform a task.

    Allows optional overrides via `repo_url` and Kubernetes `namespace`/`container`.
    """
    cfg = _get_prompt_server_config()

    org = cfg.organisation
    repo = cfg.repo_name
    root = cfg.project_root

    if repo_url:
        parsed = parse_github_url(repo_url)
        org = parsed.organisation or org
        repo = parsed.repo_name or repo
        # If a repo URL is provided without a path, default to repository root
        root = parsed.project_root if parsed.project_root is not None else ""

    ns_text = f" in the namespace {namespace}" if namespace else ""
    container_text = f" for the container {container}" if container else ""

    root_text = root if root else "the root directory of the repository"

    @dataclass(frozen=True)
    class PromptContext:
        service: str
        ns_text: str
        container_text: str
        org: str
        repo: str
        root_text: str
        slack_channel_id: str

    @dataclass(frozen=True)
    class DiagnosePromptSteps:
        logs: str
        logs_hint: str
        code: str
        diagnose: str
        report: str
        notify: str

        @classmethod
        def from_context(
            cls,
            context: "PromptContext",
        ) -> "DiagnosePromptSteps":
            logs = (
                f"1) Logs: List pods{context.ns_text if context.ns_text else ''}. "
                "Then get the last 1000 lines of logs for the pod of service "
                f"'{context.service}'{context.container_text}."
            )
            logs_hint = (
                "   If a pod name is required, list pods first and choose the "
                "one matching the service label."
            )
            code = (
                f"2) Code: Using GitHub org '{context.org}', repo "
                f"'{context.repo}', inspect {context.root_text}. "
                "If the path does not exist, list directories and fetch the "
                "referenced file."
            )
            diagnose = (
                "3) Diagnose: Identify the most likely root cause; include file "
                "paths and short code excerpts."
            )
            report = "4) Report: Create one GitHub issue (skip if issues disabled)."
            notify = (
                f"5) Notify: Post a concise summary to Slack channel "
                f"{context.slack_channel_id}."
            )
            return cls(
                logs=logs,
                logs_hint=logs_hint,
                code=code,
                diagnose=diagnose,
                report=report,
                notify=notify,
            )

        def parts(self) -> list[str]:
            return [
                "You are SRE Agent. Perform a focused diagnosis and return clear "
                "findings.",
                self.logs,
                self.logs_hint,
                self.code,
                self.diagnose,
                self.report,
                self.notify,
                "Output requirements:",
                "- Summarise key errors with timestamps and pod/container.",
                (
                    "- Reference code locations (file:line) and include short "
                    "snippets when relevant."
                ),
                "- Provide next actions.",
                "- Create at most one issue and one Slack message.",
            ]

    step_templates = DiagnosePromptSteps.from_context(
        PromptContext(
            service=service,
            ns_text=ns_text,
            container_text=container_text,
            org=org,
            repo=repo,
            root_text=root_text,
            slack_channel_id=slack_channel_id,
        )
    )
    return "\n".join(step_templates.parts())


app = FastAPI()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Health check endpoint for the firewall."""
    return {"status": "healthy"}


app.mount("/", mcp.sse_app())
