# [미실행 스텁] 실서버용 Spark 추출 job — 로컬 스택에서는 돌지 않는다.
# 대용량 Oracle 소스는 파이썬 로더 대신 회사 Spark 클러스터로 추출/변환하고,
# 임시 저장소(S3 또는 스테이징 Postgres)에 내려 dbt 가 이어받는다.
# 제출 자리: dags/extract.py 의 PythonOperator → SparkSubmitOperator 교체.
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("extract_portmaster2_full").getOrCreate()

df = (
    spark.read.format("jdbc")
    .option("url", "jdbc:oracle:thin:@//EES_HOST:1521/EES_SERVICE")
    .option("dbtable", "(SELECT * FROM ees.pcs_sq_port_mst_2nd WHERE db_user = 'PF_PCS')")
    .option("user", "${EES_USER}")
    .option("password", "${EES_PASSWORD}")
    .option("fetchsize", 10000)
    .load()
)

# 스테이징: S3(parquet) 또는 Postgres 중 택일 — 회사 자원 확정 시 한쪽만 남긴다
df.write.mode("overwrite").parquet("s3a://pcs-staging/brz/ees__portmaster2/")
# df.write.format("jdbc").option("url", "jdbc:postgresql://warehouse:5432/pcs_wh") \
#   .option("dbtable", "brz.ees__portmaster2").mode("overwrite").save()

spark.stop()
