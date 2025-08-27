# MCP Servers

This directory contains the individual MCP servers which can be built from their respective Dockerfile's.

The current MCP servers we deploy are:
1. GitHub MCP
2. Kubernetes MCP
3. Slack MCP
4. Prompt server MCP

## Recent enhancements

- Prompt server now supports dynamic overrides per request:
  - `repo_url`: full GitHub URL (supports branch/path). The server derives organisation, repo, and project root.
  - `namespace` and `container`: hint Kubernetes diagnostics for multi‑namespace or multi‑container pods.
- Evidence‑driven prompt: requests clearer findings (timestamps, pod/container, file:line excerpts) and concise next actions.

### Example

HTTP:

```bash
curl -X POST http://localhost:8003/diagnose \
  -H "Authorization: Bearer $DEV_BEARER_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "text=website" \
  --data-urlencode "repo_url=https://github.com/<org>/<repo>/tree/main/<app-path>" \
  --data-urlencode "namespace=dev-website" \
  --data-urlencode "container=website"
```

Slack:

- `/diagnose website repo_url=https://github.com/<org>/<repo>/tree/main/<app-path> namespace=dev-website container=website`

# Attribution

The following MCP servers are based off of existing implementations:

1. GitHub: https://github.com/modelcontextprotocol/servers/tree/main/src/github (MIT License)
2. Slack: https://github.com/modelcontextprotocol/servers/tree/main/src/slack (MIT License)
3. Kubernetes: https://github.com/Flux159/mcp-server-kubernetes (MIT License)

Their respective licenses exist in the subdirectories.
