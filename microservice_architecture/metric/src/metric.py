import pika
import json
import pandas as pd
import os

# ------- СЕРВИС ПОЛУЧАЕТ СООБЩЕНИЯ ИЗ ОЧЕРЕДЕЙ y_true И y_pred -------

try:
    # Подключение к RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq", port=5672)
    )

    # Настраиваем канал
    channel = connection.channel()
    channel.queue_declare(queue="y_true")
    channel.queue_declare(queue="y_pred")


    # Имя файла для сохранения данных
    CSV_FILENAME = './logs/metric_log.csv'

    # Создаем DataFrame с нужными столбцами
    df = pd.DataFrame(columns=['id', 'y_pred', 'y_true', 'absolute_error'])

    # Создаем CSV-файл с заголовками, если его нет
    if not os.path.isfile(CSV_FILENAME):
        df.to_csv(CSV_FILENAME, index=False)

    # Функция для вычисления абсолютной ошибки
    def calculate_error(row):
        if pd.notna(row['y_pred']) and pd.notna(row['y_true']):
            return abs(row['y_pred'] - row['y_true'])
        return None


    # Функция для сохранения DataFrame в CSV
    def save_to_csv(df, filename=CSV_FILENAME):
        file_exists = os.path.isfile(filename)
        df.to_csv(filename, mode='w', header=True, index=False)

    # Обработчик сообщений
    def callback(ch, method, properties, body):
        global df

        try:
            # Разбираем сообщение
            data_form_queue = json.loads(body)
            print(f"Получено сообщение из {method.routing_key}: {data_form_queue}")

            msg_id = data_form_queue.get('id')
            value = data_form_queue.get('body')

            # Определяем, из какой очереди пришло сообщение
            if method.routing_key == "y_true":
                # Обновляем y_true
                if msg_id in df['id'].values:
                    df.loc[df['id'] == msg_id, 'y_true'] = value
                else:
                    # Добавляем новую строку
                    new_row = {"id": msg_id, "y_true": value, "y_pred": None, "absolute_error": None}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            elif method.routing_key == "y_pred":
                # Обновляем y_pred
                if msg_id in df['id'].values:
                    df.loc[df['id'] == msg_id, 'y_pred'] = value
                else:
                    # Добавляем новую строку
                    new_row = {"id": msg_id, "y_true": None, "y_pred": value, "absolute_error": None}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Пересчитываем absolute_error
            df['absolute_error'] = df.apply(calculate_error, axis=1)

            # Сохраняем в CSV
            save_to_csv(df)

            print(f"Обновленный DataFrame:\n{df}")
        except Exception as e:
            print(f"Ошибка в обработке сообщения: {e}")


    # Подписываемся на очереди
    channel.basic_consume(queue="y_true", on_message_callback=callback, auto_ack=True)
    channel.basic_consume(queue="y_pred", on_message_callback=callback, auto_ack=True)

    print("Ожидание сообщений...")
    channel.start_consuming()
except Exception as e:
    print(f"Не удалось подключиться к очереди. Или другие проблемы: {e}")