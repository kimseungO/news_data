from dotenv import load_dotenv
import os
import mysql.connector
import pandas as pd


data = pd.read_excel('/app/data/news_preproc.xlsx')


# MySQL 연결
if os.environ.get("KUBERNETES_SERVICE_HOST") is None:
    # .env 파일의 경로를 명시적으로 지정합니다.
    # 프로젝트 구조에 따라 'backend/.env' 대신 '.env'만 필요할 수도 있습니다.
    # 예: load_dotenv(dotenv_path=".env")
    load_dotenv(dotenv_path=".env")

# MySQL 연결 설정
# 환경 변수가 설정되어 있지 않을 경우를 대비하여 .get() 메서드를 사용하고 기본값을 제공하는 것이 좋습니다.
try:
    conn = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"), # 환경 변수 없으면 'localhost' 기본값
        user=os.environ.get("DB_USER", "root"),       # 환경 변수 없으면 'root' 기본값
        password=os.environ.get("DB_PASSWORD", ""),   # 환경 변수 없으면 빈 문자열 기본값
        database=os.environ.get("DB_NAME", "test_db"), # 환경 변수 없으면 'test_db' 기본값
    )
    cursor = conn.cursor()
    print("✅ 데이터베이스 연결 성공!")
except mysql.connector.Error as err:
    print(f"❌ 데이터베이스 연결 오류: {err}")
    # 오류 발생 시 프로그램 종료 또는 적절한 예외 처리
    exit()


# 1. 우선 필요한 열이 없다면 테이블에 열 추가
alter_sqls = [
    "ALTER TABLE news_raw ADD cluster2nd INT",
    "ALTER TABLE news_raw ADD keyword VARCHAR(255)",
    "ALTER TABLE news_raw ADD counts INT"
]

for sql in alter_sqls:
    try:
        cursor.execute(sql)
    except mysql.connector.errors.ProgrammingError as e:
        print(f"[무시됨] ALTER 오류 (이미 존재할 가능성): {e}")

conn.commit()

if 'data' not in locals():
    print("경고: 'data' DataFrame이 정의되지 않았습니다. DB에 데이터를 넣을수 없습니다.")

update_sql = """
UPDATE news_raw
SET cluster2nd = %s,
    keyword = %s,
    counts = %s
WHERE url = %s
"""

for _, row in data.iterrows():
    try:
        cursor.execute(update_sql, (
            int(row['cluster2nd']) if not pd.isnull(row['cluster2nd']) else None,
            row['keyword'],
            int(row['counts']) if not pd.isnull(row['counts']) else 1,
            row['url']  # 기준 URL
        ))
    except Exception as e:
        print(f"❌ UPDATE 실패 (URL: {row['url']}) → {e}")

conn.commit()
cursor.close()
conn.close()
print("✅ 클러스터링 정보(키워드 포함)를 기존 테이블 news_raw에 반영 완료!")
