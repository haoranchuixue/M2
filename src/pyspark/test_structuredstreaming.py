import os
import sys

# 设置环境变量（必须在导入 pyspark 之前设置）
# 注意：必须删除可能存在的系统 HADOOP_HOME，防止被覆盖
os.environ['SPARK_HOME'] = 'D:\\spark-3.5.8-bin-hadoop3'
os.environ['JAVA_HOME'] = 'C:\\Program Files\\Java\\jdk-17'
# 设置 HADOOP_HOME - Windows 上运行 Spark 必需
# 使用 Spark 自带的 hadoop 目录，或者指向已安装兼容版本的 winutils
os.environ['HADOOP_HOME'] = 'D:\\spark-3.5.8-bin-hadoop3'
# 强制清除可能存在的旧路径，确保使用正确的 bin 目录
path_entries = os.environ.get('PATH', '').split(';')
# 移除旧的 hadoop 路径
path_entries = [p for p in path_entries if 'hadoop' not in p.lower() or 'spark' in p.lower()]
# 将 Spark hadoop bin 目录添加到 PATH 开头（优先级最高）
os.environ['PATH'] = 'D:\\spark-3.5.8-bin-hadoop3\\bin;' + ';'.join(path_entries)

import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, count, sum as spark_sum
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType


def main():
    """主函数：从 Socket 读取流数据并处理"""
    # 创建 SparkSession
    spark = SparkSession.builder \
        .config("spark.hadoop.native.lib", "false") \
        .master("local[*]") \
        .appName("SocketStreaming") \
        .getOrCreate()   
    spark.sparkContext.setLogLevel("WARN")
    
    # 从 Socket 读取流数据（每行一条 JSON 记录）
    lines = spark.readStream \
        .format("socket") \
        .option("host", "8.218.89.44") \
        .option("port", 9999) \
        .load()
    
    # 定义 JSON 数据的 schema
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("amount", DoubleType(), True)
    ])
    
    # 解析 JSON 数据
    data = lines.select(
        from_json(col("value"), schema).alias("data")
    ).select("data.*")
    
    # 过滤和统计：只处理金额大于 100 的记录
    result = data.filter(col("amount") > 100) \
        .groupBy("name") \
        .agg(
            count("*").alias("count"),
            spark_sum("amount").alias("total")
        )
    
    # 创建检查点目录
    checkpoint_dir = os.path.join(os.path.dirname(__file__), "checkpoints", "socket_streaming")
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # 输出到控制台
    query = result.writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", False) \
        .option("checkpointLocation", checkpoint_dir) \
        .start()
    
    print("流处理已启动，等待从 localhost:9999 接收数据...")
    print("发送 JSON 格式数据，例如：")
    print('  {"id": 1, "name": "Alice", "amount": 150.5}')
    print('  {"id": 2, "name": "Bob", "amount": 200.0}')
    print("\n可以使用以下命令发送数据：")
    print("  Windows: telnet localhost 9999")
    print("  Linux/Mac: nc localhost 9999")
    print("按 Ctrl+C 停止流处理")
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n流处理已停止")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
