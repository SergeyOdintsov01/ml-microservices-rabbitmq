# Задаем базовый образ 
FROM python:latest

# Монтируем рабочую директория в файловой системе контейнера
WORKDIR /usr/src/app

# Копируем в рабочую директорию контейнера, файлы нашего сервиса
COPY /src/metric.py /usr/src/app
COPY /requirements.txt /usr/src/app

# Запускаем обновление пакетов 
RUN apt-get update && apt-get install -y 

# И устанавливаем нужные для работы микросервиса пакеты
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем наш скрипт
CMD ["python" , "metric.py"]