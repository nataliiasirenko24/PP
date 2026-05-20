import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.preprocessing import OneHotEncoder

# ── 2 по job_id: benefits, job_industries, job_skills, salaries
# 3 по company_id: companies, company_industries, company_specialities, employee_counts

def merge_files_with_agg(main_df, files_list, key_column, data_path='data/'):
    """
    Функция для циклического объединения файлов с автоматической агрегацией дубликатов.
    
    :param main_df: Основной датафрейм (df)
    :param files_list: Список имён файлов без расширения .csv
    :param key_column: Ключ для объединения ('company_id' или 'job_id')
    """
    current_df = main_df.copy()
    for file_name in files_list:
        print(f'Загружаю {file_name}.csv...')
        df_temp_raw = pd.read_csv(f'{data_path}{file_name}.csv')
        print(f'  Исходный размер {file_name}: {df_temp_raw.shape}')
        
        prefix = f'{file_name}_'
        
        # 1. Проверяем дубликаты по целевому ключу
        if df_temp_raw[key_column].duplicated().any():
            print(f'  [!] Найдено несколько строк на один {key_column}. Агрегирую данные...')
            
            # Собираем все колонки, кроме ключевой
            cols_to_agg = [col for col in df_temp_raw.columns if col != key_column]
            
            # Для каждой колонки склеиваем уникальные значения через запятую
            agg_dict = {col: lambda x: ', '.join(x.dropna().astype(str).unique()) for col in cols_to_agg}
            # Добавляем подсчет строк
            agg_dict[f'{file_name}_count'] = 'count'
            
            df_temp_raw[f'{file_name}_count'] = df_temp_raw[key_column]
            df_temp = df_temp_raw.groupby(key_column).agg(agg_dict).reset_index()
        else:
            print(f'  Дубликатов по {key_column} нет, агрегация не требуется.')
            df_temp = df_temp_raw.copy()
            
        # 2. Добавляем префикс ко всем колонкам, кроме самого ключа
        df_temp = df_temp.add_prefix(prefix).rename(
            columns={f'{prefix}{key_column}': key_column}
        )
        
        # Корректируем имя колонки с подсчетом количества, если она создалась
        if f'{prefix}{file_name}_count' in df_temp.columns:
            df_temp = df_temp.rename(columns={f'{prefix}{file_name}_count': f'{prefix}count'})

        # 3. Джойним к основному датафрейму
        current_df = current_df.merge(df_temp, on=key_column, how='left')
        print(f'  Итоговый размер df: {current_df.shape}\n' + '─'*50)
        
    return current_df

#######################################################################################################

def drop_columns(df, columns_to_drop):
    """
    Безопасно удаляет список колонок из датафрейма, 
    если они в нём существуют.
    
    :param dataframe: Исходный датафрейм (pd.DataFrame)
    :param columns_to_drop: Список названий колонок для удаления (list)
    :return: Датафрейм без указанных колонок
    """
    return df.drop(columns=columns_to_drop, errors='ignore')


############################################################################################################
def overview(data):
    '''
    Erstelle einen Überblick über einige wichtige Eigenschaften der Spalten eines DataFrames.
    Parametrs:
        df: Der zu betrachtende DataFrame
    Returns:
        None
    '''
    display(pd.DataFrame({'dtype': data.dtypes, # Dtypes
                            'count': data.count(), # Anzahl valider Einträge
                            'missing_n': data.isna().sum(), # Anzahl nan-Einträge
                            'missing_%': data.isna().mean()*100, # Anteil fehlender Daten in %
                            'uniques_n': data.nunique(), # Kardinalität (Anzahl einzigartiger Werte)
                            'uniques': [data[c].unique() for c in data.columns] # Auflistung einzigartiger Werte
                           }))