## 18. Repository layout

Defines responsibility boundaries, not mandatory implementation details.

```text
resume-assistant/
  app/
    application and evaluation packages
  frontend/
    local web application
  test/
    unit test
  database/
    public synthetic fixtures and expected behavior
  reports/
    sanitized, reproducible public reports
  docs/
    architecture, runbook, demo, and decisions
  private/
    local-only gitignored data and outputs
```
