from pyspark.sql import SparkSession
import findspark
findspark.init()


import os
os.environ['SPARK_HOME'] = 'D:\\spark-3.5.8-bin-hadoop3'
os.environ['JAVA_HOME'] = 'C:\\Program Files\\Java\\jdk-17'


# 设置JAVA_HOME环境变量，确保Spark可以找到Java运行环境
# 创建SparkSession对象，用于与Spark交互
spark = SparkSession.builder \
    .config("spark.hadoop.native.lib", "false") \
    .master("local") \
    .appName("Example") \
    .getOrCreate()

# Sample data
data = [("James", "Smith", "USA", 30),
        ("Michael", "Rose", "USA", 25),
        ("Robert", "Williams", "USA", 35),
        ("Maria", "Jones", "USA", 28)]
# Column names
columns = ["First Name", "Last Name", "Country", "Age"]

# Create DataFrame
df = spark.createDataFrame(data, schema=columns)

# Show the DataFrame
# df.show()
df.createOrReplaceTempView("user")
# spark.sql("select * from user").show()
# 过滤First Name为 James 的行
spark.sql("select * from user where `First Name` = 'James'").show()


# Stop the SparkSession
spark.stop()