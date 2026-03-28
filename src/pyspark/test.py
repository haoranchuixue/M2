from pyspark.sql import SparkSession
#-- import findspark
#-- findspark.init()


import os
import sys
#-- os.environ['SPARK_HOME'] = 'D:\\spark-3.5.8-bin-hadoop3'
os.environ['JAVA_HOME'] = 'C:\\Program Files\\Java\\jdk-17'
# 设置Python路径，解决Windows上Python worker连接问题
python_executable = sys.executable
os.environ['PYSPARK_PYTHON'] = python_executable
os.environ['PYSPARK_DRIVER_PYTHON'] = python_executable

# 创建SparkSession对象，用于与Spark交互
spark = SparkSession.builder \
    .config("spark.hadoop.native.lib", "false") \
    .config("spark.pyspark.python", python_executable) \
    .config("spark.pyspark.driver.python", python_executable) \
    .master("local[*]") \
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
df = spark.createDataFrame(data, columns)

# Show the DataFrame
# df.show()
df.createOrReplaceTempView("user")
# spark.sql("select * from user").show()
# 过滤First Name为 James 的行
spark.sql("select * from user").show()


# Stop the SparkSession
spark.stop()


