# Scripts

Small one-off scripts can live here when a task is not worth adding to the CLI.

Prefer pydoit for the core workflow:

```bash
uv run --extra dev doit list
```

Routine script commands are exposed through pydoit:

```bash
uv run --extra dev doit wwcb_download
uv run --extra dev doit wwcb_parse
uv run --extra dev doit wwcb_ai_features
uv run --extra dev doit notebook
```
