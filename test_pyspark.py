from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[1]").appName("test").getOrCreate()
print("PySpark OK rows=" + str(spark.range(3).count()))
spark.stop()
