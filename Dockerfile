FROM python:3.13.2-slim

RUN apt-get update -y

WORKDIR /app

# 1. 의존성 파일만 먼저 복사
COPY requirements.txt .

# 2. 의존성 설치 (소스 코드가 바뀌어도 이 단계는 캐시됨)
RUN pip install --no-cache-dir -r requirements.txt

# 3. 나머지 소스 코드 복사
COPY . .

ENTRYPOINT ["python3"]
CMD ["main.py"]
