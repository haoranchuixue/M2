# Spark 作业故障排查记录

## 2026-03-31 全域流量分层作业 ExecutorLostFailure

### 作业信息

| 项目 | 值 |
|------|-----|
| 作业名称 | 全域流量分层_分广告主版_online |
| DataWorks Task ID | 1000272888974 |
| EMR Workspace | w-bf46ed6e59a27dd3 |
| Job Run ID | jr-7f72ff35584643a4 |
| Spark 版本 | 3.5.2-emr (JDK17, EMR Serverless on K8s) |
| 引擎 | Gluten/Velox 列式加速引擎 |

### 故障现象

- 作业频繁失败，Stage 41 的 Task 5 连续失败 4 次后作业 abort
- Executor 异常退出，exit code **134**（SIGABRT）
- Container 启动后约 85 秒即崩溃

### 错误日志

```
Exception in thread "main" org.apache.spark.SparkException:
Job aborted due to stage failure: Task 5 in stage 41.0 failed 4 times,
most recent failure: Lost task 5.3 in stage 41.0 (TID 166719)
(21.131.14.101 executor 1625): ExecutorLostFailure
(executor 1625 exited caused by one of the running tasks)
Reason: The executor with id 1625 exited with exit code 134(unexpected).
container state: terminated
termination reason: Error
```

### 数据规模（Stage 37，Stage 41 的上游）

| 指标 | 值 |
|------|-----|
| 任务数 | 474 |
| Input | 7.3 GiB / 4.35 亿条 |
| Shuffle Write | 9.3 GiB / 4.34 亿条 |

### 根因分析

1. **Exit code 134 = 128 + 6 = SIGABRT**：进程收到 abort 信号，属于 native 级别崩溃
2. 作业使用 Gluten/Velox 列式引擎，内存分配走 native heap（off-heap），不受 JVM `-Xmx` 控制
3. Stage 41 在 shuffle read 阶段，Velox 异步操作（如 shuffle 数据拉取）在 Task 停止时未能在默认超时内完成，触发 SIGABRT
4. 特定 Task（Task 5）稳定复现，疑似该分区存在数据倾斜，数据量大导致异步操作耗时更长

### 解决方案

增加 Gluten/Velox 的异步操作超时参数：

```properties
spark.gluten.sql.columnar.backend.velox.asyncTimeoutOnTaskStopping=100000
```

该参数将 Velox Task 停止时等待异步操作完成的超时时间增大到 100 秒（默认值较小），避免 shuffle 数据量大时异步操作超时导致 abort。

### 后续观察

- [ ] 确认添加参数后作业是否稳定通过
- [ ] 如仍有问题，考虑增大 `spark.executor.memoryOverhead` 或增加 `spark.sql.shuffle.partitions`
- [ ] 长期关注是否存在广告主维度的数据倾斜
