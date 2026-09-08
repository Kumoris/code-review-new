# Spark 代码与数据管道检视规则

> 触发条件：(a) `.py`/`.java`文件含`SparkSession`/`DataFrame`/`RDD`/`Dataset`，或 (b) 变更文件含`*.dataset.yaml`/`*.pipeline.yaml`

---

## 目录

- [SQL 规则](#sql-规则)
- [DataFrame 规则](#dataframe-规则)
- [UDF 规则](#udf-规则)
- [缓存与持久化](#缓存与持久化)
- [数据管道配置规则](#数据管道配置规则)

---

## SQL 规则

| 规则ID | 规则名称 | 说明 |
|--------|---------|------|
| SPARK-SQL-001 | 避免 `SELECT *` | 显式列出所需列，避免不必要的数据读取和schema变更影响 |
| SPARK-SQL-002 | 分区裁剪 | WHERE条件必须包含分区列，避免全表扫描 |
| SPARK-SQL-003 | 大表JOIN顺序 | 小表在左，大表在右；使用broadcast hint优化小表JOIN |
| SPARK-SQL-004 | 数据倾斜处理 | GROUP BY/JOIN key分布不均时使用salting或skew hint |
| SPARK-SQL-005 | 避免笛卡尔积 | CROSS JOIN必须有明确业务需求并添加限制条件 |

## DataFrame 规则

| 规则ID | 规则名称 | 说明 |
|--------|---------|------|
| SPARK-DF-001 | 避免重复计算 | 同一DataFrame多次action时先cache/persist |
| SPARK-DF-002 | 谓词下推 | 尽早filter，减少后续处理数据量 |
| SPARK-DF-003 | 列裁剪 | 只select需要的列，避免携带不必要数据 |
| SPARK-DF-004 | 避免collect到Driver | 大数据集用take/foreach替代collect |
| SPARK-DF-005 | 合并窄转换 | 连续map/filter可合并为单次转换 |

## UDF 规则

| 规则ID | 规则名称 | 说明 |
|--------|---------|------|
| SPARK-UDF-001 | 优先使用内置函数 | 内置函数有Catalyst优化，UDF无法优化 |
| SPARK-UDF-002 | 避免在UDF中创建外部连接 | 每行调用导致连接风暴，使用广播变量或mapPartitions |
| SPARK-UDF-003 | 类型安全 | Python UDF返回值类型必须与声明一致 |

## 缓存与持久化

| 规则ID | 规则名称 | 说明 |
|--------|---------|------|
| SPARK-CACHE-001 | 及时unpersist | 不再使用的缓存DataFrame必须unpersist释放资源 |
| SPARK-CACHE-002 | 选择合适存储级别 | 根据数据使用频率和计算成本选择MEMORY_ONLY/MEMORY_AND_DISK等 |
| SPARK-CACHE-003 | 避免缓存过小DataFrame | 缓存开销可能超过重算成本，仅在多次使用时缓存 |

## 数据管道配置规则

> 适用于 `.dataset.yaml`、`.pipeline.yaml` 等 Spark 数据管道配置文件

| 规则ID | 规则名称 | 检查锚点 | 说明 |
|--------|---------|----------|------|
| SPARK-PIPE-001 | retention 不得超标 | `retention` 字段值 | `partitionType=time` 且 `format=csv` 时，retention 不应超过 granularity 对应规范值：1m→1D，5m→7D，1h→30D，1d→365D。超标将导致存储资源急剧消耗和数据清理失效 |
| SPARK-PIPE-002 | 禁止重复键 | 同一 YAML 文件中重复的 key | YAML 解析器以最后出现的值为准，重复键导致配置混乱难以维护 |
| SPARK-PIPE-003 | granularity 变更需评估 | `granularity` 字段从大值改小值 | granularity 变小（如 5m→1m）导致数据写入频率倍增，需确认上游数据源是否满足产出能力、网络带宽是否充足 |
| SPARK-PIPE-004 | partitionType 与 format 一致性 | `partitionType` + `format` 组合 | 某些组合不合理（如 partitionType=hash 但无 partitionColumn），或 format 与下游消费者不兼容 |

### SPARK-PIPE-001 详细说明

- **检查锚点**: `.dataset.yaml` 文件中 `retention` 字段被新增或修改
- **触发条件**: `partitionType="time"` 且 `format="csv"` 时，`retention` 值超过 granularity 允许上限
- **严重程度**: major（存储资源耗尽风险）→ 若 retention 超标 10 倍以上则为 fatal
- **反例**:
  - `granularity: "5m"`, `retention: "50D"` — 5m 粒度允许最长 7D，50D 超标 7 倍，数据量暴增
  - `granularity: "1m"`, `retention: "30D"` — 1m 粒度允许最长 1D，30D 超标 30 倍
- **正例**:
  - `granularity: "5m"`, `retention: "7D"` — 在规范范围内
  - `granularity: "1h"`, `retention: "30D"` — 在规范范围内
