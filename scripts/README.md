# Scripts

Small one-off scripts can live here when a task is not worth adding to the CLI.

Prefer the CLI for core workflow:

```bash
uv run python -m corn_forecast.cli --help
```

Routine script commands are exposed through pydoit:

```bash
uv run --extra dev doit wwcb_download
uv run --extra dev doit wwcb_parse
uv run --extra dev doit wwcb_ai_features
uv run --extra dev doit notebook
```
