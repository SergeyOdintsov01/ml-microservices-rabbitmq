import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Пути к файлам
CSV_FILENAME = './logs/metric_log.csv'
PLOT_FILENAME = './logs/error_distribution.png'

# Проверяем, существует ли папка logs
if not os.path.exists('./logs'):
    os.makedirs('./logs')

def plot_error_distribution():
    try:
        # Читаем CSV-файл
        if os.path.exists(CSV_FILENAME):
            df = pd.read_csv(CSV_FILENAME)

            if 'absolute_error' in df.columns and not df['absolute_error'].isnull().all():
                # Строим гистограмму
                plt.figure(figsize=(8, 5))
                sns.histplot(df['absolute_error'], bins=10, kde=True, color='orange', edgecolor='black')
                plt.title('График абсолютной ошибки: |y_true - y_pred|')
                plt.xlabel('absolute_error')
                plt.ylabel('Count')  # Изменяем метку оси Y

                # Сохраняем график
                plt.savefig(PLOT_FILENAME)
                plt.close()
                print(f"Гистограмма успешно сохранена в {PLOT_FILENAME}")
            else:
                print("Столбец 'absolute_error' пуст или отсутствует.")
        else:
            print(f"Файл {CSV_FILENAME} не найден.")
    except Exception as e:
        print(f"Ошибка при построении графика: {e}")

# Вызов функции сразу при загрузке модуля
# print("Сервис plot запущен...")
plot_error_distribution()
