# dbt Column-Level Lineage Research & Implementation Guide

## 1. What is Column Lineage?

**Column-level lineage** tracks data flow at the column level, showing:
- Which source columns contribute to each target column
- Transformations applied to columns through intermediate models
- Full ancestry/parentage of a column through multiple dbt model layers

**Examples in Portfolio context:**
```
varejo.dim_clientes.customer_segment_code 
  ← origen_cliente.SEGMENT_CODE (staging)
    ← origin_cliente.col_segmento (raw)
      ← postgres system.venda table

mart_request_history.api_service
  ← stg_request_logs.service
    ← system.request_log.service (API middleware logs)
```

---

## 2. How dbt Handles Column Lineage

### 2.1 Native Support in manifest.json (v1.5+)

dbt automatically captures **column-level lineage** in the `manifest.json` starting from **dbt v1.5**. The manifest includes:

```json
{
  "nodes": {
    "model.portifolio.dim_customers": {
      "name": "dim_customers",
      "columns": {
        "customer_id": {
          "name": "customer_id",
          "description": "Primary key",
          "data_type": "int",
          "lineage": {
            "upstream_lineage": [
              {
                "source_name": "stg_customers",
                "column_name": "customer_id"
              }
            ]
          }
        }
      }
    }
  }
}
```

### 2.2 How dbt Extracts Lineage

dbt uses **SQL parsing** (via sqlglot internally) to:
1. Parse each model's SQL file
2. Identify `ref()` and `source()` dependencies
3. Trace column mappings through SELECT statements
4. Build the DAG of column-to-column transformations

**Limitations:**
- **Dynamic SQL** (Jinja variables, macro logic): dbt cannot parse without execution
- **Complex logic**: CTEs, window functions, subqueries are tracked but attribution is simplified
- **Raw data**: Column lineage only available for modeled data, not raw source columns

---

## 3. Accessing Column Lineage in dbt

### 3.1 dbt Docs Site (UI)

When you run `dbt docs generate` and open the docs site:
1. Navigate to a model (e.g., `dim_customers`)
2. Click **Column Lineage** tab
3. Interactive graph shows upstream/downstream column dependencies

### 3.2 manifest.json (Programmatic)

Parse `portifolio/target/manifest.json` with Python:

```python
import json

with open("portifolio/target/manifest.json") as f:
    manifest = json.load(f)

# Access lineage for a column
model_node = manifest["nodes"]["model.portifolio.dim_customers"]
columns = model_node.get("columns", {})

for col_name, col_def in columns.items():
    lineage = col_def.get("lineage", {})
    upstream = lineage.get("upstream_lineage", [])
    print(f"{col_name} ← {upstream}")
```

### 3.3 dbt-core Python API

```python
from dbt.cli.main import main
from dbt.contracts.results import RunResult
import json

# Parse project
result = main(["parse"])

# Load manifest
with open("portifolio/target/manifest.json") as f:
    manifest = json.load(f)

# Navigate to models with lineage
for unique_id, node in manifest["nodes"].items():
    if "model" in unique_id:
        print(f"Model: {node['name']}")
        for col_name, col_def in node.get("columns", {}).items():
            lineage = col_def.get("lineage", {})
            if lineage:
                print(f"  {col_name}: {lineage}")
```

---

## 4. Alternative: External Tools for Advanced Lineage

### 4.1 **sqlglot** (Used by dlt in workspace)

```python
import sqlglot
from sqlglot.optimizer.qualify import qualify
from sqlglot.schema import MappingSchema

# Parse SQL with table schema awareness
query = """
SELECT 
  c.customer_id,
  c.name,
  SUM(o.amount) as total_spent
FROM origin_cliente c
JOIN origin_venda o ON c.customer_id = o.customer_id
GROUP BY 1, 2
"""

parsed = sqlglot.parse_one(query, dialect="postgres")

# Extract column lineage (which source columns → output columns)
# This requires building a schema of upstream tables first
```

*Note: dlt in your workspace uses this for `compute_columns_schema()` (see `dlt/dataset/lineage.py`)*

### 4.2 **dbt-core + sqlglot Integration**

Combine dbt's manifest with sqlglot parsing:

```python
import json
import sqlglot
from sqlglot.optimizer.qualify import qualify

def get_column_lineage(model_name: str, column_name: str):
    """Trace column lineage through model DAG"""
    with open("portifolio/target/manifest.json") as f:
        manifest = json.load(f)
    
    model = manifest["nodes"][f"model.portifolio.{model_name}"]
    
    # 1. Get column metadata
    col_meta = model["columns"].get(column_name, {})
    lineage = col_meta.get("lineage", {})
    
    # 2. Parse model's SQL for detailed column logic
    compiled_sql = model.get("compiled_sql", model["raw_sql"])
    parsed = sqlglot.parse_one(compiled_sql, dialect="postgres")
    
    return {
        "model": model_name,
        "column": column_name,
        "data_type": col_meta.get("data_type"),
        "upstream": lineage.get("upstream_lineage", []),
        "description": col_meta.get("description"),
    }
```

---

## 5. Implementation in Portfolio Project

### 5.1 **Option A: Leverage dbt Docs (Simplest)**

✅ **Pros:**
- Zero code; already built into dbt
- Interactive UI for exploring lineage
- Accessible to non-technical stakeholders

❌ **Cons:**
- Read-only; requires docs generation
- Not programmatic

**Steps:**
1. Run `dbt docs generate` (already in Makefile as `make dbt-build`)
2. Run `dbt docs serve` (add to Makefile)
3. Open browser → Navigate to model → Click "Column Lineage" tab

### 5.2 **Option B: Python Script for Programmatic Access (Recommended)**

Build a tool to query column lineage and export to:
- Interactive HTML report
- CSV/JSON for data governance tools
- Slack/email alerts on lineage changes

**Implementation:**

```python
# portifolio/tools/column_lineage_analyzer.py

import json
from pathlib import Path
from typing import Dict, List
import click

class ColumnLineageAnalyzer:
    def __init__(self, manifest_path: str = "target/manifest.json"):
        with open(manifest_path) as f:
            self.manifest = json.load(f)
    
    def get_column_ancestors(self, model: str, column: str, depth=0, visited=None) -> Dict:
        """Recursively trace column ancestors through model DAG"""
        if visited is None:
            visited = set()
        
        if depth > 10 or f"{model}.{column}" in visited:
            return None
        
        visited.add(f"{model}.{column}")
        
        try:
            node = self.manifest["nodes"][f"model.portifolio.{model}"]
        except KeyError:
            return None
        
        col_def = node.get("columns", {}).get(column, {})
        lineage = col_def.get("lineage", {})
        upstream = lineage.get("upstream_lineage", [])
        
        ancestors = {
            "model": model,
            "column": column,
            "data_type": col_def.get("data_type"),
            "description": col_def.get("description"),
            "sources": []
        }
        
        for source in upstream:
            parent = self.get_column_ancestors(
                source["source_name"],
                source["column_name"],
                depth + 1,
                visited
            )
            if parent:
                ancestors["sources"].append(parent)
        
        return ancestors
    
    def report_column_lineage(self, model: str, column: str) -> str:
        """Generate text report of column lineage"""
        lineage = self.get_column_ancestors(model, column)
        return self._format_lineage_tree(lineage)
    
    def _format_lineage_tree(self, node: Dict, indent: str = "") -> str:
        """Format lineage as ASCII tree"""
        result = f"{indent}{node['model']}.{node['column']} ({node['data_type']})\n"
        if node['description']:
            result += f"{indent}  └─ {node['description']}\n"
        
        for source in node['sources']:
            result += self._format_lineage_tree(source, indent + "  ├─ ")
        
        return result
    
    def export_system_domain_lineage(self, output: str = "lineage_report.txt"):
        """Export lineage for system domain (observability models)"""
        system_models = [
            ("stg_request_logs", "request_id"),
            ("stg_app_logs", "log_id"),
            ("mart_api_health", "service"),
            ("mart_pipeline_runs", "dag_id"),
            ("mart_request_history", "request_id"),
        ]
        
        with open(output, "w") as f:
            for model, column in system_models:
                lineage = self.get_column_ancestors(model, column)
                if lineage:
                    f.write(self._format_lineage_tree(lineage))
                    f.write("\n" + "=" * 80 + "\n\n")

@click.group()
def cli():
    pass

@cli.command()
@click.option("--model", required=True, help="Model name")
@click.option("--column", required=True, help="Column name")
def trace(model: str, column: str):
    """Trace column lineage"""
    analyzer = ColumnLineageAnalyzer()
    report = analyzer.report_column_lineage(model, column)
    click.echo(report)

@cli.command()
@click.option("--output", default="lineage_report.txt", help="Output file")
def system_lineage(output: str):
    """Export system domain lineage"""
    analyzer = ColumnLineageAnalyzer()
    analyzer.export_system_domain_lineage(output)
    click.echo(f"Exported to {output}")

if __name__ == "__main__":
    cli()
```

**Usage:**
```bash
python portifolio/tools/column_lineage_analyzer.py trace --model mart_api_health --column service

python portifolio/tools/column_lineage_analyzer.py system_lineage --output reports/system_lineage.txt
```

### 5.3 **Option C: dbt Artifacts + OpenLineage (Advanced)**

Use **OpenLineage** standard to export lineage for integration with:
- Data governance platforms (Collibra, Alation)
- Data catalogs (Atlan, DataHub)
- Observability tools

```python
from openlineage.client.run import RunEvent, RunState
from openlineage.client.client import OpenLineageClient

# Export dbt runs as OpenLineage events
client = OpenLineageClient("http://localhost:5000")

# dbt models → OpenLineage jobs
event = RunEvent(
    eventTime="2024-01-01T12:00:00Z",
    run=Run(
        runId="dbt-run-12345",
        facets={},
    ),
    job=Job(
        namespace="dbt://portifolio",
        name="mart_api_health",
        facets={},
    ),
    inputs=[...],  # upstream tables
    outputs=[...], # downstream tables
    producer="dbt",
)

client.emit(event)
```

---

## 6. Portfolio Lineage Visualization Example

### 6.1 System Domain (Observability)

```
system.request_log (OLTP → API middleware)
  └── stg_request_logs (staging model)
      ├── mart_api_health (hourly rollup)
      │   ├── api_service ← system.request_log.service
      │   ├── request_count ← COUNT(*) over stg_request_logs
      │   └── avg_duration_ms ← AVG(duration_ms) over stg_request_logs
      └── mart_request_history (raw detail)
          ├── request_id ← system.request_log.request_id
          ├── service ← system.request_log.service
          ├── endpoint ← system.request_log.endpoint
          └── status_code ← system.request_log.status_code

system.app_log (pipeline execution logs)
  └── stg_app_logs (staging model)
      └── mart_pipeline_runs (DAG/task tracking)
          ├── dag_id ← JSONB→>'dag_id' from system.app_log
          ├── task_id ← JSONB→>'task_id' from system.app_log
          ├── status ← JSONB→>'status' from system.app_log
          └── duration_s ← JSONB→>'duration_s' from system.app_log
```

### 6.2 Varejo Domain Example

```
origin_cliente (landing)
  └── stg_clientes (staging)
      ├── int_customers_enriched (intermediate)
      │   └── dim_customers (mart)
      │       ├── customer_id ← origin_cliente.id
      │       ├── name ← origin_cliente.nome
      │       └── segment ← origin_cliente.segmento
      └── int_vendas_por_cliente (intermediate)
          └── mart_customer_sales (mart)
              ├── customer_id ← origin_cliente.id
              └── total_sales ← SUM(origin_venda.valor)
```

---

## 7. Benefits for Portfolio Project

✅ **Data Governance**: Track which columns depend on legacy systems
✅ **Impact Analysis**: Before renaming/removing columns, see all downstream impacts
✅ **Documentation**: Auto-generate data lineage docs for stakeholders
✅ **Compliance**: Audit data flow for sensitive fields (PII tracking)
✅ **Quality**: Identify which models to rebuild after source schema changes
✅ **Observability**: Trace system logs through marts to understand monitoring data

---

## 8. Recommended Implementation Plan

### Phase 1: **Documentation & UI** (Week 1)
- [ ] Generate dbt docs with column lineage
- [ ] Add to Makefile: `docs: dbt docs serve`
- [ ] Document how to access column lineage in README

### Phase 2: **Programmatic Tool** (Week 2)
- [ ] Implement `portifolio/tools/column_lineage_analyzer.py`
- [ ] Add CLI commands for querying lineage
- [ ] Export system domain lineage as baseline

### Phase 3: **Integration** (Week 3-4)
- [ ] Integrate lineage tool into orchestration DAGs
- [ ] Export to data governance platform (if applicable)
- [ ] Add lineage tests to catch breaking changes

### Phase 4: **Advanced** (Future)
- [ ] OpenLineage integration for external catalogs
- [ ] Real-time lineage visualization in Airflow UI
- [ ] Automated impact analysis for schema migrations

---

## 9. References

- **dbt Column Lineage**: https://docs.getdbt.com/docs/build/column-lineage
- **manifest.json schema**: https://schemas.getdbt.com/dbt/manifest/v12.json
- **sqlglot**: https://github.com/tobymao/sqlglot (used in your dlt codebase)
- **OpenLineage**: https://openlineage.io/
- **dbt Docs**: https://docs.getdbt.com/docs/collaborate/builds-and-snapshots

---

## 10. Next Steps

1. **Test dbt Docs locally**: 
   ```bash
   make dbt-build && dbt docs serve
   ```

2. **Verify manifest.json contains lineage**:
   ```bash
   python -c "import json; m = json.load(open('portifolio/target/manifest.json')); \
     print(m['nodes']['model.portifolio.mart_api_health']['columns'])"
   ```

3. **Choose implementation option** (A, B, or C based on needs)

4. **Start with system domain** (most critical for observability)
