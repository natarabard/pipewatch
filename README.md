# pipewatch

A lightweight CLI tool to monitor and alert on data pipeline health metrics from multiple sources.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install .
```

---

## Usage

Run a health check against a configured pipeline source:

```bash
pipewatch check --config pipelines.yaml
```

Watch continuously and receive alerts when metrics exceed thresholds:

```bash
pipewatch watch --source kafka --interval 30 --alert-on failure_rate>0.05
```

Example `pipelines.yaml`:

```yaml
sources:
  - name: orders-pipeline
    type: kafka
    topic: orders.processed
    thresholds:
      failure_rate: 0.05
      lag: 1000
```

Output:

```
[OK]   orders-pipeline  failure_rate=0.01  lag=42
[WARN] returns-pipeline failure_rate=0.07  lag=2300  ← threshold exceeded
```

---

## Configuration

| Flag | Description | Default |
|------|-------------|---------|
| `--config` | Path to YAML config file | `pipelines.yaml` |
| `--interval` | Polling interval in seconds | `60` |
| `--alert-on` | Alert condition expression | none |

---

## License

MIT © 2024 [yourname](https://github.com/yourname)