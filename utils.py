import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.preprocessing import OneHotEncoder
import pandas as pd
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import textwrap
from sklearn.model_selection import train_test_split



# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ФУНКЦИИ ДЛЯ ЗАГРУЗКИ И НОРМАЛИЗАЦИИ ДАННЫХ
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# _detect_encoding
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _detect_encoding(path):
    """UTF-8 BOM — частая история в SO Survey CSV."""
    with open(path, "rb") as f:
        raw = f.read(4)
    if raw[:3] == b"\xef\xbb\xbf": return "utf-8-sig"
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"): return "utf-16"
    return "utf-8"

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# _read_file
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _read_file(path):
    """Читает CSV с автоопределением формата и кодировки."""
    enc = _detect_encoding(path)
    for encoding in dict.fromkeys([enc, "utf-8", "utf-8-sig", "latin-1"]):
        for sep in (",", ";", "\t"):
            try:
                return pd.read_csv(path, sep=sep, encoding=encoding,
                                   low_memory=False, on_bad_lines="skip",
                                   na_values=['nan', 'NaN', '<NA>', ''])
            except Exception:
                continue
    raise ValueError(f"Не удалось прочитать: {path}")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# normalize_year
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def normalize_year(df_raw, year, schema):
    """
    Переименовывает колонки к canonical именам по переданной SCHEMA.

    Parameters
    ----------
    df_raw : pd.DataFrame  — исходный датафрейм одного года
    year   : int           — год опроса
    schema : dict          — cfg.SCHEMA из config_mappings

    Returns
    -------
    pd.DataFrame с canonical-именами + колонкой 'year'
    """
    schema_year = schema.get(year, {})
    n = len(df_raw)
    result = {"year": [year] * n}
    for canonical, original in schema_year.items():
        if original and original in df_raw.columns:
            result[canonical] = df_raw[original].values
        else:
            result[canonical] = pd.array([pd.NA] * n)
    df_norm = pd.DataFrame(result)
    df_norm["salary"] = pd.to_numeric(df_norm["salary"], errors="coerce")
    return df_norm

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# load_year
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def load_year(year, data_dir="data"):
    """Ищет файл года в data_dir и читает его. Возвращает (df, filename) или (None, None)."""
    candidates = [
        os.path.join(data_dir, f"so_{year}.csv"),
        os.path.join(data_dir, f"{year}.csv"),
        os.path.join(data_dir, f"so_{year}.xlsx"),
        os.path.join(data_dir, f"{year}.xlsx"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if path is None:
        return None, None
    return _read_file(path), os.path.basename(path)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# merge_feature_cols
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def merge_feature_cols(df, col_main, col_entry, col_result):
    df = df.copy()  # ← не мутируем входной df

    combined = (
        df[col_main].fillna('').astype(str) + ';' +
        df[col_entry].fillna('').astype(str)
    )
    combined = combined.str.strip(';')

    def clean_and_deduplicate(x):
        if not x:
            return ""
        parts = [p.strip() for p in x.split(';') if p.strip()]
        return ';'.join(dict.fromkeys(parts))

    df[col_result] = combined.apply(clean_and_deduplicate)
    return df

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# classify_data_role
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def classify_data_role(devtype, data_role_mapping):
    """
    Возвращает категорию data-специалиста или None.

    Parameters
    ----------
    devtype           : значение ячейки (строка или NaN)
    data_role_mapping : cfg.DATA_ROLE_MAPPING
    """
    if pd.isna(devtype):
        return None
    roles = {r.strip() for r in str(devtype).split(";")}
    for category, keywords in data_role_mapping:
        if any(kw in roles for kw in keywords):
            return category
    return None

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ФУНКЦИИ ОСНОВНЫЕ
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# overview
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

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
    
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# drop_columns
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def drop_columns(df, columns_to_drop):
    """
    Безопасно удаляет список колонок из датафрейма, 
    если они в нём существуют.
    
    :param dataframe: Исходный датафрейм (pd.DataFrame)
    :param columns_to_drop: Список названий колонок для удаления (list)
    :return: Датафрейм без указанных колонок
    """
    return df.drop(columns=columns_to_drop, errors='ignore')


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# optimize_types
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def optimize_types(data, cat_cols, num_cols):
    '''
    Optimiert den Speicherbedarf des DataFrames durch Anpassung der Datentypen.
        Funktion reduziert den Speicherverbrauch:
        Numerische Spalten (num_cols) auf den kleinstmöglichen Datentyp herunterskaliert, 
        basierend auf dem Wertebereich der Daten.
        Kategoriale Spalten (cat_cols) in den Pandas-Typ 'category' konvertiert,
        was bei Spalten mit vielen Wiederholungen massiv Speicher spart.
    Parameters:
        data (pd.DataFrame): Der zu optimierende DataFrame.
        cat_cols (list): Liste der Namen der kategorialen Spalten.
        num_cols (list): Liste der Namen der numerischen Spalten.
    Returns:
        pd.DataFrame: Der DataFrame mit optimierten Datentypen.
    '''
    for c in num_cols:
        if c in data.columns:
            if pd.api.types.is_numeric_dtype(data[c]):
                if (data[c] % 1 != 0).any():
                    data[c] = data[c].astype('float32')
                else:
                    if data[c].min() < 0:
                        if data[c].min() >= -128 and data[c].max() <= 127:
                            data[c] = data[c].astype('int8')
                        elif data[c].min() >= -32768 and data[c].max() <= 32767:
                            data[c] = data[c].astype('int16')
                        else:
                            data[c] = data[c].astype('int32')
                    else:
                        if data[c].max() < 255:
                            data[c] = data[c].astype('uint8')
                        elif data[c].max() < 65535:
                            data[c] = data[c].astype('uint16')
                        else:
                            data[c] = data[c].astype('int32')  
                        
    for c in cat_cols:
        if c in data.columns:
            data[c] = data[c].astype('category')
    
    return data

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# fix_apostrophes
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────



def fix_apostrophes(mapping: dict) -> dict:
    """Заменяет типографские апострофы на стандартные во всех ключах."""
    return {
        k.replace("\u2019", "'").replace("\u2018", "'"): v
        for k, v in mapping.items()
    }

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# impute_work_exp
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────




def impute_work_exp(df):
    """
    Создает признак work_exp_is_missing и заполняет пропуски 
    медианой по группам 'education' и 'years_code'.
    """
    df = df.copy()
    
    # 1. Создаем индикатор пропусков (0 или 1)
    df['work_exp_is_missing'] = df['workexp'].isna().astype(int)
    
    # 2. Вычисляем медианы для групп
    # Группируем и сохраняем как Series
    medians = df.groupby(['education', 'yearscode'], observed=True)['workexp'].transform('median')
    
    # 3. Заполняем пропуски в work_exp вычисленными медианами
    df['workexp'] = df['workexp'].fillna(medians)
    
    # 4. Если остались NaN (например, группа была целиком из пропусков), 
    # заполняем их глобальной медианой
    global_median = df['workexp'].median()
    df['workexp'] = df['workexp'].fillna(global_median)
    
    return df


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ФУНКЦИИ ДЛЯ EDA
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════



# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# explore_unique_values
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def explore_unique_values(df, columns, top_n=5, show_trash_only=False):
    """
    Universelle Funktion zur Analyse eindeutiger Werte und Identifikation von Textrauschen (Datenmüll).
    
    Parameters:
    -----------
    df : pd.DataFrame - Der zu analysierende Datensatz.
    columns : str or list - Name der Spalte oder Liste von Spalten für die Analyse.
    top_n : int - Anzahl der häufigsten Werte, die angezeigt werden sollen (Default: 20).
    show_trash_only : bool - Wenn True, werden nur fehlerhafte Strings (mit Umbrüchen, Tabs etc.) ausgegeben.
    """
    # Konvertierung eines einzelnen Spaltennamens (String) into eine Liste
    if isinstance(columns, str):
        columns = [columns]
        
    for col in columns:
        if col not in df.columns:
            print(f"❌ Spalte '{col}' ist im DataFrame nicht vorhanden.\n" + "-"*60)
            continue
            
        print(f"🔍 Spaltenanalyse: '{col}'")
        print(f"Zeilen: {len(df[col]):,}     Ausgefüllt (Nicht-NaN): {df[col].notna().sum():,}     Eindeutige Werte: {df[col].nunique():,}")
        
        # Berechnung der absoluten und relativen Häufigkeiten (inklusive NaN)
        counts = df[col].value_counts(dropna=False)
        percentages = df[col].value_counts(dropna=False, normalize=True) * 100
        
        # Erstellung des finalen Statistik-Reports
        report_df = pd.DataFrame({
            'Häufigkeit': counts,
            'Anteil (%)': percentages.round(2)
        })
        
        if show_trash_only:
            # Filterung von Strings mit Zeilenumbrüchen (\n, \r), Tabs (\t) oder Mehrfachleerzeichen
            trash_mask = report_df.index.astype(str).str.contains(r'[\n\t\r]|\s{2,}', regex=True)
            report_df = report_df[trash_mask]
            print(f"⚠️ Fehlerhafte eindeutige Werte gefunden (mit Umbrüchen/Leerzeichen): {len(report_df)}")
            if len(report_df) == 0:
                print("Filter ist leer. Kein verdecktes Textrauschen erkannt!")
                continue
        
        # Ausgabe der Top-Ergebnisse
        print(f"Anzeige der ersten {min(top_n, len(report_df))} Zeilen:")
        print(report_df.head(top_n).to_string())
        
        # Hinweis bei unvollständiger Anzeige aufgrund der Begrenzung (top_n)
        if len(report_df) > top_n:
            print(f"... und weitere {len(report_df) - top_n} eindeutige Werte sind ausgeblendet (Parameter top_n anpassen).")
            
        print("-" * 60 + "\n")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# group_rare_categories
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def group_rare_categories(data, c, threshold=5):
    '''
    Zusammenfassung von seltenen Werten zu einer gemeinsamen Gruppe Other.
    Parameters:
        data : pandas.DataFrame
        c: columns
        threshold: %
    Returns: series
    '''
    series = data[c].copy()
    probs = series.value_counts(normalize=True)
    rare_categories = probs[probs < threshold / 100].index
    if str(series.dtype) == 'category':
        if 'Other' not in series.cat.categories:
            series = series.cat.add_categories('Other')
    return series.replace(rare_categories, 'Other')

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# explore_multivalue_column
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def explore_multivalue_column(df, columns, top_n=5, sep=';', show_trash_only=False):
    """
    Universelle Funktion zur Analyse von Multivalue-Spalten (Mehrfachantworten) 
    und Identifikation von Textrauschen (Datenmüll).
    
    Parameters:
    -----------
    df : pd.DataFrame - Der zu analysierende Datensatz.
    columns : str or list - Name der Spalte oder Liste von Spalten für die Analyse.
    top_n : int - Anzahl der häufigsten Werte, die angezeigt werden sollen (Default: 5).
    sep : str - Trennzeichen innerhalb der Multivalue-Strings (Default: ';').
    show_trash_only : bool - Wenn True, werden nur fehlerhafte Strings (mit Umbrüchen, Tabs etc.) ausgegeben.
    """
    # Konvertierung eines einzelnen Spaltennamens (String) into eine Liste
    if isinstance(columns, str):
        columns = [columns]
        
    for col in columns:
        if col not in df.columns:
            print(f"❌ Spalte '{col}' ist im DataFrame nicht vorhanden.\n" + "-"*60)
            continue
            
        # Нахождение базовых метрик заполненности
        clean_series = df[col].dropna().astype(str)
        total_valid = len(clean_series)
        
        if total_valid == 0:
            print(f"🔍 Spaltenanalyse: '{col}'")
            print(f"Zeilen: {len(df[col]):,}     Ausgefüllt (Nicht-NaN): 0     Eindeutige atomare Werte: 0")
            print("-" * 60 + "\n")
            continue

        # Парсинг мультизначных строк (взрыв серий)
        flat_series = clean_series.str.split(sep).explode().str.strip()
        flat_series = flat_series[flat_series != '']
        
        # Расчет частот и долей (доля считается от числа заполненных строк респондентов)
        counts = flat_series.value_counts()
        percentages = (counts / total_valid) * 100
        
        # Erstellung des finalen Statistik-Reports
        report_df = pd.DataFrame({
            'Häufigkeit': counts,
            'Anteil (%)': percentages.round(2)
        })
        report_df.index.name = col
        
        print(f"🔍 Spaltenanalyse: '{col}'")
        print(f"Zeilen: {len(df[col]):,}     Ausgefüllt (Nicht-NaN): {total_valid:,}     Eindeutige Werte: {len(report_df):,}")
        
        if show_trash_only:
            # Filterung von Strings mit Zeilenumbrüchen (\n, \r), Tabs (\t) oder Mehrfachleerzeichen
            trash_mask = report_df.index.astype(str).str.contains(r'[\n\t\r]|\s{2,}', regex=True)
            report_df = report_df[trash_mask]
            print(f"⚠️ Fehlerhafte eindeutige Werte gefunden (mit Umbrüchen/Leerzeichen): {len(report_df)}")
            if len(report_df) == 0:
                print("Filter ist leer. Kein verdecktes Textrauschen erkannt!")
                print("-" * 60 + "\n")
                continue
        
        # Ausgabe der Top-Ergebnisse
        print(f"Anzeige der ersten {min(top_n, len(report_df))} Zeilen:")
        print(report_df.head(top_n).to_string())
        
        # Hinweis bei unvollständiger Anzeige aufgrund der Begrenzung (top_n)
        if len(report_df) > top_n:
            print(f"... und weitere {len(report_df) - top_n} eindeutige Werte sind ausgeblendet (Parameter top_n anpassen).")
            
        print("-" * 60 + "\n")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# normalize_multivalue_column
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def normalize_multivalue_column(
    df: pd.DataFrame,
    column_name: str,
    mapping: dict[str, str],
    sep: str = ";",
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Ersetzt Synonyme und führt Unterkategorien in einer Multivalue-Spalte zusammen.

    Logik:
    ------
    - Splittet jede Zelle anhand des Trennzeichens 'sep'
    - Wendet das Mapping an: alter_wert → neuer_wert
    - Entfernt Duplikate innerhalb einer Zeile (nach der Konsolidierung von Synonymen)
    - Fügt die Werte wieder mittels 'sep' zusammen

    Parameters
    ----------
    df : pd.DataFrame
        Der ursprüngliche Datensatz.
    column_name : str
        Die zu normalisierende Spalte.
    mapping : dict[str, str]
        Wörterbuch für Ersetzungen. Schlüssel = Ausgangswert, Wert = Zielwert.
        Mehrere Schlüssel können auf denselben Wert verweisen (Synonyme).
        Beispiel:
            {
                "Bash/Shell": "Bash/Shell/PowerShell",
                "PowerShell": "Bash/Shell/PowerShell",
                "Bash/Shell (all shells)": "Bash/Shell/PowerShell",
                "MATLAB": "Matlab",
                "Lisp": "LISP",
                "Cobol": "COBOL",
                "Visual Basic (.Net)": "VBA",
            }
    sep : str
        Trennteichen für die Werte innerhalb einer Zelle (Default: ';')
    inplace : bool
        True  — Modifiziert das DataFrame direkt (Inplace-Operation).
        False — Gibt eine Kopie zurück (Standard-Sicherheitsmodus).

    Returns
    -------
    pd.DataFrame
        Das DataFrame mit der normalisierten Spalte.
    """
    # Zuweisung des Ziel-DataFrames basierend auf dem inplace-Parameter
    result = df if inplace else df.copy()

    def _normalize_row(val):
        if pd.isna(val):
            return val
        
        # Aufteilung der Zelle in einzelne Elemente und Entfernung von Whitespaces
        parts = [p.strip() for p in str(val).split(sep) if p.strip()]
        
        # Anwendung des Mappings; Werte ohne Match bleiben unverändert
        mapped = [mapping.get(p, p) for p in parts]
        
        # Deduplizierung unter Beibehaltung der ursprünglichen Reihenfolge
        seen, deduped = set(), []
        for item in mapped:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
                
        return sep.join(deduped)

    # Zeilenweise Anwendung der Normalisierungslogik
    result[column_name] = result[column_name].apply(_normalize_row)

    # Berechnung der Anzahl tatsächlich modifizierter Zeilen
    changed = (result[column_name] != df[column_name]).sum()
    
    return result

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# replace_rare_with_other
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def replace_rare_with_other(
    df: pd.DataFrame,
    column_name: str,
    mapping: Optional[dict[str, str]] = None,
    threshold: float = 5,  
    other_label: str = "Other",
    sep: str = ";",
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Ersetzt seltene Unterkategorien (Anteil < threshold %) durch 'other_label'.

    Logik:
    ------
    1. Berechnung des Anteils jedes atomaren Wertes an der Gesamtzahl ausgefüllter Zeilen
       (analog zu explore_multivalue_column).
    2. Werte unterhalb des Schwellenwerts werden durch 'other_label' ersetzt.
    3. Wenn eine Zelle nach der Ersetzung mehrere 'other_label'-Einträge enthält,
       werden diese zu einem einzigen Eintrag konsolidiert (Deduplizierung).
    4. Ein optionales Mapping ermöglicht erzwungene Ersetzungen / Umbenennungen
       spezifischer Werte VOR der Schwellenwert-Berechnung.

    Parameters
    ----------
    df : pd.DataFrame
        Der ursprüngliche Datensatz.
    column_name : str
        Die zu verarbeitende Spalte.
    mapping : dict[str, str] | None
        Zusätzliche erzwungene Ersetzungen (Anwendung VOR der Schwellenwert-Berechnung).
        Falls die Funktionen nacheinander aufgerufen werden, dasselbe Wörterbuch wie bei
        normalize_multivalue_column übergeben, andernfalls None.
    threshold : float
        Schwellenwert in Prozent (Default: 1.0, d. h. < 1% → 'Other').
    other_label : str
        Label für seltene Werte (Default: 'Other').
    sep : str
        Trennteichen für die Werte innerhalb einer Zelle.
    inplace : bool
        True  — Modifiziert das DataFrame direkt (Inplace-Operation).
        False — Gibt eine Kopie zurück (Standard-Sicherheitsmodus).

    Returns
    -------
    pd.DataFrame
        Das DataFrame mit ersetzten seltenen Werten.
    """
    # Zuweisung des Ziel-DataFrames basierend auf dem inplace-Parameter
    result = df if inplace else df.copy()

    # Schritt 0: Anwendung des Mappings, falls übergeben
    if mapping:
        result = normalize_multivalue_column(
            result, column_name, mapping, sep=sep, inplace=True
        )

    # Schritt 1: Frequenzberechnung auf der aktuellen (bereits normalisierten) Spalte
    clean = result[column_name].dropna().astype(str)
    total_valid = len(clean)


    # Aufteilen der Multivalue-Listen in einzelne Zeilen (Explode) und Bereinigung
    flat = clean.str.split(sep).explode().str.strip()
    flat = flat[flat != ""]
    counts = flat.value_counts()
    share = (counts / total_valid) * 100

    # Identifikation seltener Kategorien unterhalb des Schwellenwerts
    rare = set(share[share < threshold].index)
    # Das 'other_label' selbst wird niemals als "selten" eingestuft
    rare.discard(other_label)

    # Schritt 2: Zeilenweise Anwendung der Ersetzungslogik
    def _replace_row(val):
        if pd.isna(val):
            return val
        
        parts = [p.strip() for p in str(val).split(sep) if p.strip()]
        # Ersetzung seltener Werte durch das definierte Label
        replaced = [other_label if p in rare else p for p in parts]
        
        # Deduplizierung von 'Other'-Einträgen unter Beibehaltung der Reihenfolge
        seen, deduped = set(), []
        for item in replaced:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
                
        return sep.join(deduped)

    # Anwendung der Transformationsfunktion auf die Zielspalte
    result[column_name] = result[column_name].apply(_replace_row)
    return result

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# clean_employment_status
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def clean_employment_status(text):
    """
    Классифицирует грязные строки занятости по ключевым словам.
    """
    if not isinstance(text, str):
        return 'Not Employed / Other'
    
    text_lower = text.lower()
    
    # Приоритет 1: Полная занятость (самая большая группа)
    if 'full-time' in text_lower or text_lower == 'employed':
        return 'Full-time'
    
    # Приоритет 2: Фриланс и контракты
    if 'independent contractor' in text_lower or 'freelancer' in text_lower or 'self-employed' in text_lower:
        return 'Freelance'
    
    # Приоритет 3: Частичная занятость
    if 'part-time' in text_lower:
        return 'Part-time'
    
    # Все остальные (студенты, пенсионеры, безработные) 
    return 'Unknown'

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# categorize_currency
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def categorize_currency(text):
    text = str(text)
    if 'United States' in text or 'USD' in text:
        return 'USD'
    elif 'European Euro' in text or 'EUR' in text:
        return 'EUR'
    elif 'Pound sterling' in text or 'GBP' in text:
        return 'GBP'
    elif 'Indian rupee' in text or 'INR' in text:
        return 'INR'
    elif 'Canadian dollar' in text or 'CAD' in text:
        return 'CAD'
    elif 'Brazilian real' in text or 'BRL' in text:
        return 'BRL'
    elif 'Australian dollar' in text or 'AUD' in text:
        return 'AUD'
    elif 'Polish zloty' in text or 'PLN' in text:
        return 'PLN'
    elif 'Polish zloty' in text or 'PLN' in text:
        return 'PLN'
    elif 'Swedish krona' in text or 'SEK' in text:
        return 'SEK'
    elif 'Swiss franc' in text or 'CHF' in text:
        return 'CHF'
    elif 'Russian ruble' in text or 'RUB' in text:
        return 'RUB'
    elif 'Czech koruna' in text or 'CZK' in text:
        return 'CZK'
    elif 'Israeli new shekel' in text or 'ILS' in text:
        return 'ILS'
    elif 'Ukrainian hryvnia' in text or 'UAH' in text:
        return 'UAH'
    elif 'Turkish lira' in text or 'TRY' in text:
        return 'TRY '
    else:
        return 'Other'




















# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ФУНКЦИИ ДЛЯ ВИЗУАЛИЗАЦИИ
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════



# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# catplot






# ══════════════════════════════════════════════════════════════════════════════
# EDA КАТЕГОРИАЛЬНЫХ ПРИЗНАКОВ
# ══════════════════════════════════════════════════════════════════════════════
 
# ══════════════════════════════════════════════════════════════════════════════
# EDA КАТЕГОРИАЛЬНЫХ ПРИЗНАКОВ  (2×2 layout)
# ══════════════════════════════════════════════════════════════════════════════
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def eda_categorical(
    df: pd.DataFrame,
    col: str,
    *,
    year: int | None = None,
    country: str | None = None,
    top_n: int = 10,
    target: str = "salary",
    year_col: str = "year",
    country_col: str = "country",
    trend_years: tuple[int, int] | None = None,
    figsize: tuple = (18, 12),
    save_path: str | None = None,
) -> None:
    """
    EDA-Dashboard für kategoriale Features — 2×2 Grafik-Raster.
    
    ОБНОВЛЕНИЯ:
    - Легенды строго в один столбик.
    - Цвета палитры перемешиваются для максимального контраста близких категорий.
    """
    C_RED = "#D7191C" 

    # 1. Базовая фильтрация по стране
    data_base = df.copy()
    if country is not None and country_col in data_base.columns: 
        data_base = data_base[data_base[country_col] == country]

    if data_base.empty:
        print(f"⚠️ DataFrame ist nach der Länderfilterung leer.")
        return

    # Временные срезы данных
    data_2024 = data_base[data_base[year_col] == 2024].copy() if year_col in data_base.columns else pd.DataFrame()
    data_2025 = data_base[data_base[year_col] == 2025].copy() if year_col in data_base.columns else pd.DataFrame()

    if year is not None:
        data_trend = data_base[data_base[year_col] == year].copy()
    elif trend_years is not None and year_col in data_base.columns:
        data_trend = data_base[(data_base[year_col] >= trend_years[0]) & (data_base[year_col] <= trend_years[1])].copy()
    else:
        data_trend = data_base.copy()

    # 2. Определение Топ-N (по частоте за ВСЕ ГОДА)
    counts_all = data_base[col].value_counts()
    top_cats = counts_all.head(top_n).index.tolist()
    n_hidden = max(0, counts_all.shape[0] - top_n)
    
    order = top_cats
    
    # ИЗМЕНЕНО: Берём палитру и перемешиваем её, чтобы убрать парные схожие оттенки
    if top_n <= 20:
        base_colors = list(sns.color_palette("tab20", 20).as_hex())
        # Используем фиксированный seed, чтобы при перезапуске цвета одной категории не менялись случайным образом
        rng = np.random.default_rng(seed=4)
        rng.shuffle(base_colors)
        base_colors = base_colors[:top_n]
    else:
        base_colors = sns.color_palette("husl", top_n).as_hex()

    # ЖЕСТКАЯ СВЯЗКА: Категория -> Уникальный контрастный цвет
    category_colors = {cat: base_colors[i] for i, cat in enumerate(order)}
    color_list_main = [category_colors[cat] for cat in order]

    plot_data_all_years = data_base[data_base[col].isin(top_cats)].copy()
    plot_data_trend = data_trend[data_trend[col].isin(top_cats)].copy()
    plot_data_2024 = data_2024[data_2024[col].isin(top_cats)].copy() if not data_2024.empty else pd.DataFrame()
    plot_data_2025 = data_2025[data_2025[col].isin(top_cats)].copy() if not data_2025.empty else pd.DataFrame()

    meta = []
    if year:               meta.append(f"Jahr: {year}")
    elif trend_years:      meta.append(f"Trend: {trend_years[0]}-{trend_years[1]}")
    if country:            meta.append(country)
    meta_str = "  |  " + "  |  ".join(meta) if meta else ""

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    main_title = f"EDA-Dashboard: {col}{meta_str}" + (f"  (Top-{top_n} von {counts_all.shape[0]} Klassen)" if n_hidden > 0 else "")
    fig.suptitle(main_title, fontsize=16, fontweight="bold", y=1.02)

    # ════════════════════════════════════════════════════════════════════════
    # [0,0] KUBUS 1: Marktanteile (Alle Jahre vs. 2025)
    # ════════════════════════════════════════════════════════════════════════
    ax = axes[0, 0]
    
    freq_all = plot_data_all_years[col].value_counts().reindex(order).fillna(0)
    pct_all = (freq_all / len(data_base) * 100).values
    count_all_vals = freq_all.values
        
    if not plot_data_2025.empty:
        freq_2025 = plot_data_2025[col].value_counts().reindex(order).fillna(0)
        pct_2025 = (freq_2025 / len(data_2025) * 100).values
        count_2025_vals = freq_2025.values
    else:
        pct_2025, count_2025_vals = np.zeros(len(order)), np.zeros(len(order))

    y_positions = np.arange(len(order))
    bar_width = 0.38

    # order[0] = самая частая категория — рисуем сверху (максимальная y-позиция)
    # порядок по оси Y: order[0] вверху, order[-1] внизу
    y_rev = y_positions[::-1]   # позиции сверху вниз

    bars_all  = ax.barh(y_rev + bar_width/2, pct_all,  height=bar_width,
                        color=color_list_main, alpha=0.9,  edgecolor="white", label="Alle Jahre")
    bars_2025 = ax.barh(y_rev - bar_width/2, pct_2025, height=bar_width,
                        color=color_list_main, alpha=0.45, edgecolor="white", label="Jahr 2025")

    max_pct = max(pct_all.max(), pct_2025.max(), 1)
    for bar, c_val, p_val in zip(bars_all, count_all_vals, pct_all):
        if p_val > 0:
            ax.text(bar.get_width() + max_pct * 0.015, bar.get_y() + bar.get_height()/2,
                    f"{int(c_val):,} ({p_val:.1f}%)", va="center", fontsize=8, color="#222222", fontweight="bold")

    for bar, c_val, p_val in zip(bars_2025, count_2025_vals, pct_2025):
        if p_val > 0:
            ax.text(bar.get_width() + max_pct * 0.015, bar.get_y() + bar.get_height()/2,
                    f"{int(c_val):,} ({p_val:.1f}%)", va="center", fontsize=8, color="#555555")

    ax.set_yticks(y_rev)
    ax.set_yticklabels(order)
    ax.set_xlim(0, max_pct * 1.35)
    ax.set_title("Marktanteile: Gesamt vs. 2025", fontweight="bold", pad=10)
    ax.set_xlabel("Anteil an der Stichprobe (%)")
    ax.set_ylabel(col)
    ax.legend(loc="upper right")
    ax.grid(axis='x', linestyle=':', alpha=0.5)

    # ════════════════════════════════════════════════════════════════════════
    # [0,1] KUBUS 2: ИСПРАВЛЕНО -> Легенды строго в ОДИН столбик (ncol=1)
    # ════════════════════════════════════════════════════════════════════════
    ax = axes[0, 1]
    
    if year is not None or (trend_years is not None and trend_years[0] == trend_years[1]):
        freq_pie = plot_data_trend[col].value_counts().reindex(order).fillna(0).reset_index()
        freq_pie.columns = [col, "count"]
        freq_pie["pct"] = freq_pie["count"] / len(data_trend) * 100
        
        pie_vals = freq_pie["count"].values
        pie_labels = [f"{c} ({p:.1f}%)" if p > 0 else "" for c, p in zip(freq_pie[col], freq_pie["pct"])]
        
        pie_colors = [category_colors[cat] for cat in freq_pie[col]]
        
        wedges, _ = ax.pie(
            pie_vals, labels=None, colors=pie_colors,
            startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 0.8},
        )
        # ИСПРАВЛЕНО: Легенда для круговой диаграммы справа, в один столбик
        ax.legend(wedges, pie_labels, loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8, ncol=1)
        current_yr = year if year else trend_years[0]
        ax.set_title(f"Marktanteile im Jahr {current_yr} (Pie Chart)", fontweight="bold", pad=10)
    else:
        yearly_totals = plot_data_trend.groupby(year_col).size()
        trend_freq = plot_data_trend.groupby([year_col, col]).size().reset_index(name="counts")
        trend_freq["share_pct"] = trend_freq.apply(
            lambda row: (row["counts"] / yearly_totals[row[year_col]] * 100) if row[year_col] in yearly_totals else 0, axis=1
        )
        
        for cat in order: 
            sub = trend_freq[trend_freq[col] == cat].sort_values(year_col)
            ax.plot(sub[year_col], sub["share_pct"], marker="o", ms=4, lw=1.8, 
                    color=category_colors[cat], label=str(cat))
                    
        ax.set_xlabel("Jahr")
        ax.set_ylabel("Anteil an allen Nennungen (%)")
        tr_title_str = f"{trend_years[0]}-{trend_years[1]}" if trend_years else "Gesamtzeitraum"
        ax.set_title(f"Entwicklung der Marktanteile ({tr_title_str})", fontweight="bold", pad=10)
        
        # ИСПРАВЛЕНО: Легенда для тренда выведена в один столбик (ncol=1) справа от графика
        ax.legend(fontsize=8, ncol=1, loc="upper left", bbox_to_anchor=(1.02, 1))
        
        if year_col in plot_data_trend.columns and not plot_data_trend.empty:
            ax.set_xticks(sorted(plot_data_trend[year_col].unique()))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(axis='both', linestyle=':', alpha=0.5)

    # ════════════════════════════════════════════════════════════════════════
    # [1,0] KUBUS 3: Gehaltsverteilung за весь период (Boxplot)
    # ════════════════════════════════════════════════════════════════════════
    ax = axes[1, 0]
    
    # Используем matplotlib напрямую — обходим баг seaborn 0.13.x с boxprops
    # matplotlib boxplot рисует снизу вверх (позиция 1 = нижний),
    # поэтому передаём order[::-1] чтобы порядок совпал с барчартом (сверху вниз)
    box_order_rev = order[::-1]
    box_data  = [
        plot_data_all_years.loc[plot_data_all_years[col] == cat, target].dropna().values
        for cat in box_order_rev
    ]
    bp = ax.boxplot(
        box_data,
        vert=False,
        patch_artist=True,
        widths=0.55,
        flierprops={"marker": ".", "alpha": 0.25, "markersize": 3,
                    "markeredgecolor": "none", "markerfacecolor": "#555555"},
        medianprops={"linewidth": 2.0},
        whiskerprops={"linewidth": 1.2},
        capprops={"linewidth": 1.2},
        boxprops={"linewidth": 0.8},
    )
    ax.set_yticks(range(1, len(box_order_rev) + 1))
    ax.set_yticklabels(box_order_rev)

    for i, (patch, whisker_pair, cap_pair, median_line) in enumerate(
        zip(bp["boxes"], zip(*[iter(bp["whiskers"])] * 2),
            zip(*[iter(bp["caps"])] * 2), bp["medians"])
    ):
        color = category_colors[box_order_rev[i]]
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
        patch.set_edgecolor("white")
        for w in whisker_pair:
            w.set_color(color)
            w.set_linewidth(1.2)
        for c in cap_pair:
            c.set_color(color)
            c.set_linewidth(1.2)
        median_line.set_color("white")
        median_line.set_linewidth(2.0)

    global_median_all = data_base[target].median() if target in data_base.columns else 0
    ax.axvline(global_median_all, color=C_RED, lw=1.5, ls="--", label=f"Gesamt-Median: ${global_median_all:.0f}k")

    if target in data_base.columns:
        x_max = data_base[target].quantile(0.97)
        x_min = max(0, data_base[target].quantile(0.03))
        ax.set_xlim(x_min, x_max * 1.05)
        ax.get_xaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:.0f}k" if x < 1000 else f"${int(x/1000)}k")
        )
    ax.set_title("Historische Gehaltsspanne (Gesamtperiode)", fontweight="bold", pad=10)
    ax.set_xlabel("Jahresgehalt (USD)")
    ax.set_ylabel(col)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis='x', linestyle=':', alpha=0.5)

    # ════════════════════════════════════════════════════════════════════════
    # [1,1] KUBUS 4: Vertikaler Balkenchart (Median-Gehalt: 2024 vs. 2025)
    # ════════════════════════════════════════════════════════════════════════
    ax = axes[1, 1]
    
    med_2024 = plot_data_2024.groupby(col)[target].median().reindex(order).fillna(0) if not plot_data_2024.empty else pd.Series(0, index=order)
    med_2025 = plot_data_2025.groupby(col)[target].median().reindex(order).fillna(0) if not plot_data_2025.empty else pd.Series(0, index=order)

    x_positions = np.arange(len(order))
    v_bar_width = 0.35

    bars_v_2024 = ax.bar(x_positions - v_bar_width/2, med_2024, width=v_bar_width, 
                         color=color_list_main, alpha=0.9, edgecolor="white", label="Median 2024")
    bars_v_2025 = ax.bar(x_positions + v_bar_width/2, med_2025, width=v_bar_width, 
                         color=color_list_main, alpha=0.45, edgecolor="white", label="Median 2025")

    global_med_24_k = (data_2024[target].median()) if not data_2024.empty else 0
    global_med_25_k = (data_2025[target].median()) if not data_2025.empty else 0
    
    if global_med_24_k > 0:
        ax.axhline(global_med_24_k, color="#4682B4", lw=1.2, ls="--", label=f"Gesamt-Median 24: ${global_med_24_k:.0f}k")
    if global_med_25_k > 0:
        ax.axhline(global_med_25_k, color=C_RED, lw=1.2, ls="-.", label=f"Gesamt-Median 25: ${global_med_25_k:.0f}k")

    label_fontsize = 7 if top_n > 8 else 8
    for bar in bars_v_2024:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, height + max(med_2024.max(), med_2025.max()) * 0.015,
                    f"${height:.0f}k", ha="center", va="bottom", fontsize=label_fontsize, fontweight="bold", color="#222222")

    for bar in bars_v_2025:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, height + max(med_2024.max(), med_2025.max()) * 0.015,
                    f"${height:.0f}k", ha="center", va="bottom", fontsize=label_fontsize, color="#555555")

    ax.set_xticks(x_positions)
    ax.set_xticklabels(order, rotation=45, ha="right")
    ax.set_ylim(0, max(med_2024.max(), med_2025.max(), 1) * 1.25)
    ax.set_title("Median-Gehalt im Vergleich: 2024 vs. 2025", fontweight="bold", pad=10)
    ax.set_ylabel("Median-Gehalt (in Tsd. USD)")
    ax.set_xlabel(col)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis='y', linestyle=':', alpha=0.5)

    # 4. Layout-Finishing
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"💾 Dashboard erfolgreich gespeichert unter: {save_path}")
    plt.show()
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def eda_numeric(
    df: pd.DataFrame,
    col: str,
    *,
    target: str = "salary",
    country: str | None = None,
    year_col: str = "year",
    country_col: str = "country",
    figsize: tuple = (18, 12),
    save_path: str | None = None,
) -> None:
    """
    EDA-Dashboard für numerische Features — 2×2 Grafik-Raster.
    
    Layout
    ------
    [0,0] Histogramm + KDE — Gesamtverteilung des Merkmals.
    [0,1] Scatter Plot — Merkmal vs. Gehalt (Target) mit Regressionslinie.
    [1,0] Horizontaler Boxplot nach Jahren — Распределение целевой переменной по годам в палитре tab20.
    [1,1] Linienchart — Historische Entwicklung des Medians über die Jahre.
    """
    # Базовые константы оформления
    MAIN_COLOR = "#2C7BB6"      
    ACCENT_RED = "#D7191C"      
    GREEN_MEAN = "#1A9641"      
    
    # 1. Фильтрация по стране
    data_base = df.copy()
    if country is not None and country_col in data_base.columns: 
        data_base = data_base[data_base[country_col] == country]

    if data_base.empty or col not in data_base.columns:
        print(f"⚠️ DataFrame ist leer oder Spalte '{col}' nicht gefunden.")
        return

    # Очистка от NaN в исследуемом признаке и таргете
    cols_to_clean = [col]
    if target in data_base.columns:
        cols_to_clean.append(target)
    data_base = data_base.dropna(subset=cols_to_clean)

    # 2. Подготовка перемешанной палитры tab20 для среза по ГОДАМ в [1,0]
    box_order = sorted(data_base[year_col].unique()) if year_col in data_base.columns else []
    n_years = len(box_order)
    
    # Генерируем и перемешиваем tab20
    base_colors = list(sns.color_palette("tab20", 20 if n_years <= 20 else n_years).as_hex())
    rng = np.random.default_rng(seed=42)
    rng.shuffle(base_colors)
    
    # Маппинг: Год -> Уникальный цвет из tab20
    year_colors = {yr: base_colors[i % len(base_colors)] for i, yr in enumerate(box_order)}

    meta = [f"Feature: {col}"]
    if country: meta.append(country)
    meta_str = "  |  " + "  |  ".join(meta) if meta else ""

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle(f"EDA-Dashboard: {col} vs. {target}{meta_str}", fontsize=16, fontweight="bold", y=1.02)

    # ════════════════════════════════════════════════════════════════════════
    # [0,0] КУБ 1: Гистограмма + KDE (Распределение признака)
    # ════════════════════════════════════════════════════════════════════════
    ax = axes[0, 0]
    sns.histplot(data=data_base, x=col, kde=True, ax=ax, color=MAIN_COLOR, alpha=0.6, edgecolor="white")
    
    global_median = data_base[col].median()
    global_mean = data_base[col].mean()
    ax.axvline(global_median, color=ACCENT_RED, lw=1.5, ls="--", label=f"Median: {global_median:,.1f}")
    ax.axvline(global_mean, color=GREEN_MEAN, lw=1.5, ls=":", label=f"Mean: {global_mean:,.1f}")
    
    ax.set_title(f"Gesamtverteilung von {col}", fontweight="bold", pad=10)
    ax.set_xlabel(col)
    ax.set_ylabel("Anzahl (Frequency)")
    ax.legend(loc="upper right")
    ax.grid(True, linestyle=':', alpha=0.5)

    # ════════════════════════════════════════════════════════════════════════
    # [0,1] КУБ 2: Scatter Plot (Признак vs Зарплата) строго за ОДИН ГОД
    # ════════════════════════════════════════════════════════════════════════
    ax = axes[0, 1]
    year = 2025
    if target in data_base.columns:
        # Определяем целевой год: берем переданный параметр или самый свежий год из данных
        plot_year = year if year is not None else int(data_base[year_col].max())
        data_single_year = data_base[data_base[year_col] == plot_year]
        
        if not data_single_year.empty and len(data_single_year) > 1:
            # Строим точки с небольшим jitter (разбросом), чтобы они не сливались в плотную стену
            sns.regplot(
                data=data_single_year, x=col, y=target, ax=ax,
                x_jitter=0.25, 
                scatter_kws={"color": MAIN_COLOR, "alpha": 0.35, "s": 20},
                line_kws={"color": ACCENT_RED, "lw": 2.5, "label": "Trendlinie"},
                ci=None
            )
            
            # Лаконичный заголовок без r-коэффициента
            ax.set_title(f"Fokus {plot_year}: {col} vs. {target}", fontweight="bold", pad=10)
            ax.set_xlabel(col)
            ax.set_ylabel(f"{target} (USD)")
            
            # Форматирование оси Y под формат тысяч долларов ($150k)
            ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"${int(x/1000)}k" if x > 0 else "0"))
            ax.legend(loc="upper left")
        else:
            ax.text(0.5, 0.5, f"Keine Daten für das Jahr {plot_year}", ha="center", va="center", color="gray")
    else:
        ax.text(0.5, 0.5, f"Target '{target}' nicht gefunden", ha="center", va="center", color="gray")
        
    ax.grid(True, linestyle=':', alpha=0.5)

    # ════════════════════════════════════════════════════════════════════════
    # [1,0] КУБ 3: ИСПРАВЛЕНО -> Боксплот по годам, где каждый год покрашен в tab20
    # ════════════════════════════════════════════════════════════════════════
    ax = axes[1, 0]
    if target in data_base.columns and len(box_order) > 0:
        box_data_yr = [
            data_base.loc[data_base[year_col] == yr, target].dropna().values
            for yr in box_order
        ]
        bp_yr = ax.boxplot(
            box_data_yr,
            vert=False,
            patch_artist=True,
            widths=0.45,
            flierprops={"marker": ".", "alpha": 0.3, "markersize": 4,
                        "markeredgecolor": "none", "markerfacecolor": "#222222"},
            medianprops={"linewidth": 2.0},
            whiskerprops={"linewidth": 1.2},
            capprops={"linewidth": 1.2},
            boxprops={"linewidth": 0.8},
        )
        ax.set_yticks(range(1, len(box_order) + 1))
        ax.set_yticklabels(box_order)

        for i, (patch, whisker_pair, cap_pair, median_line) in enumerate(
            zip(bp_yr["boxes"], zip(*[iter(bp_yr["whiskers"])] * 2),
                zip(*[iter(bp_yr["caps"])] * 2), bp_yr["medians"])
        ):
            color = year_colors[box_order[i]]
            patch.set_facecolor(color)
            patch.set_alpha(0.85)
            patch.set_edgecolor("white")
            for w in whisker_pair:
                w.set_color(color)
                w.set_linewidth(1.2)
            for c in cap_pair:
                c.set_color(color)
                c.set_linewidth(1.2)
            median_line.set_color("white")
            median_line.set_linewidth(2.0)
                        
        ax.set_title(f"{target}-Verteilung nach Jahren (Boxplot)", fontweight="bold", pad=10)
        ax.set_xlabel(f"{target} (USD)")
        ax.set_ylabel("Jahr")
        ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"${int(x/1000)}k" if x > 0 else "0"))
    else:
        ax.text(0.5, 0.5, "Daten für Jahresvergleich nicht ausreichend", ha="center", va="center", color="gray")
    ax.grid(True, linestyle=':', alpha=0.5)



    # ════════════════════════════════════════════════════════════════════════
    # [1,1] КУБ 4: Линейный график (Исторический тренд медианы)
    # ════════════════════════════════════════════════════════════════════════
    ax = axes[1, 1]
    if year_col in data_base.columns and data_base[year_col].nunique() > 1:
        stats_by_year = data_base.groupby(year_col)[col].median().reset_index()
        
        ax.plot(stats_by_year[year_col], stats_by_year[col], marker='o', ms=6, color=MAIN_COLOR, 
                lw=2.5, label=f"Median {col}")
        
        for _, row in stats_by_year.iterrows():
            ax.text(row[year_col], row[col] + (stats_by_year[col].max() * 0.015), 
                    f"{row[col]:,.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

        ax.set_xticks(sorted(stats_by_year[year_col].unique()))
        ax.set_ylim(0, stats_by_year[col].max() * 1.2) 
        ax.set_title(f"Historischer Trend (Median von {col} über Jahre)", fontweight="bold", pad=10)
        ax.set_xlabel("Jahr")
        ax.set_ylabel(f"Median {col}")
        ax.legend(loc="upper left")
    else:
        ax.text(0.5, 0.5, "Nicht genügend historische Daten\nfür Jahrestrend", 
                ha="center", va="center", fontsize=12, color="gray")
        ax.set_title(f"Trend über Zeit", fontweight="bold", pad=10)
    ax.grid(True, linestyle=':', alpha=0.5)

    # 4. Финишная компоновка
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"💾 Dashboard erfolgreich gespeichert unter: {save_path}")
    plt.show()
# ══════════════════════════════════════════════════════════════════════════════

import plotly.express as px
import pandas as pd
import numpy as np

def plot_salary_bubble_map(
    df: pd.DataFrame, 
    country_col: str = "country", 
    salary_col: str = "salary",
    save_html_path: str | None = None
) -> None:
    """
    Строит интерактивную карту мира (Bubble Map).
    Размер пузыря = Количество респондентов в стране.
    Цвет пузыря = Медианная зарплата в этой стране.
    """
    # 1. Агрегируем данные по странам
    geo_data = df.groupby(country_col).agg(
        median_salary=(salary_col, 'median'),
        count=(salary_col, 'count')
    ).reset_index()
    
    # Исключаем пустые строки, если они есть
    geo_data = geo_data.dropna(subset=[country_col])
    
    # 2. Строим Bubble Map
    fig = px.scatter_geo(
        geo_data,
        locations=country_col,        # Колонка со странами
        locationmode="country names",   # Режим: поиск по полным названиям на англ.
        color="median_salary",         # Цвет зависит от медианной зарплаты
        size="count",                  # Размер зависит от количества людей
        hover_name=country_col,       # Заголовок подсказки при наведении
        
        # Настраиваем всплывающую подсказку (hover data)
        hover_data={
            "median_salary": ":,.0f",  # Формат зарплаты с разделителем тысяч
            "count": ":,d",            # Формат количества (целое число)
            country_col: False         # Дублировать имя страны внутри не нужно
        },
        
        # Используем красивую плавную палитру от голубого к глубокому синему
        color_continuous_scale=px.colors.sequential.Blues,
        size_max=45,                   # Максимальный радиус самого большого пузыря (настройте под себя)
        title="<b>Globale Gehaltsverteilung & Marktgröße</b><br>Размер: кол-во анкет | Цвет: медианная зарплата (USD)"
    )
    
    # 3. Настройка внешнего вида карты и подложки
    fig.update_layout(
        # Оформление заголовка
        title=dict(font=dict(size=16), y=0.95, x=0.05),
        
        # Настройка географического движка
        geo=dict(
            showframe=False,           # Убираем квадратную рамку вокруг земли
            showcoastlines=True,       # Показываем линии берегов
            coastlinecolor="#CCCCCC",  # Делаем берега аккуратными светло-серыми
            showland=True,             # Включаем заливку суши
            landcolor="#F9F9F9",       # Суша — нейтрального почти белого цвета
            showocean=True,            # Включаем заливку океана
            oceancolor="#F5F8FA",      # Океан — блеклый голубой оттенок
            projection_type="equirectangular" # Стандартная плоская проекция мира
        ),
        
        margin=dict(l=0, r=0, t=60, b=0) # Убираем лишние пустые поля по краям
    )
    
    # ИСПРАВЛЕНО: Настройка заголовка цветовой шкалы и формата ($100k) через корректный coloraxes
    fig.update_coloraxes(
        colorbar_title=dict(text="Median Salary", font=dict(size=11)),
        colorbar_tickprefix="$", 
        colorbar_ticksuffix=""
    )
    
    # 4. Вывод или сохранение (ИСПРАВЛЕНО ДЛЯ НАДЕЖНОСТИ)
    import os
    import webbrowser

    # Принудительно сохраняем во временный или указанный файл
    html_file = save_html_path if save_html_path else "temp_salary_map.html"
    fig.write_html(html_file)
    print(f"💾 Интерактивная карта успешно сохранена: {html_file}")
    
    # Открываем файл напрямую как локальный объект (без сервера 127.0.0.1)
    file_path = os.path.abspath(html_file)
    webbrowser.open(f"file:///{file_path}")


import plotly.express as px
import pandas as pd

def plot_salary_choropleth_map(
    df: pd.DataFrame, 
    country_col: str = "country", 
    salary_col: str = "salary",
    save_html_path: str | None = None
) -> None:
    # 1. Агрегируем данные: считаем и медиану, и количество ответов
    geo_data = df.groupby(country_col).agg(
        median_salary=(salary_col, 'median'),
        count=(salary_col, 'count')
    ).reset_index()
    
    # 2. Строим карту
    fig = px.choropleth(
        geo_data,
        locations=country_col,
        locationmode="country names",
        color="median_salary",
        hover_name=country_col,
        # Добавляем в подсказку оба параметра
        hover_data={
            "median_salary": ":,.0f", # Формат зарплаты
            "count": ":,d",          # Формат количества (целое число)
            country_col: False       # Имя страны уже есть в hover_name
        },
        labels={ # Переименовываем названия в подсказке для красоты
            "median_salary": "Медианная зарплата",
            "count": "Кол-во анкет"
        },
        color_continuous_scale=px.colors.sequential.Blues,
        title="<b>Globale Gehalts-Heatmap</b>"
    )
    
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular'),
        margin=dict(l=0, r=0, t=60, b=0)
    )
    
    fig.update_coloraxes(
        colorbar_title=dict(text="Зарплата (USD)", font=dict(size=11)),
        colorbar_tickprefix="$"
    )
    
    # 4. Вывод или сохранение (ИСПРАВЛЕНО ДЛЯ НАДЕЖНОСТИ)
    import os
    import webbrowser

    # Принудительно сохраняем во временный или указанный файл
    html_file = save_html_path if save_html_path else "temp_salary_map.html"
    fig.write_html(html_file)
    print(f"💾 Интерактивная карта успешно сохранена: {html_file}")
    
    # Открываем файл напрямую как локальный объект (без сервера 127.0.0.1)
    file_path = os.path.abspath(html_file)
    webbrowser.open(f"file:///{file_path}")





# 
# ══════════════════════════════════════════════════════════════════════════════


def data_split(df):
    # features = df.drop('salary', axis=1)
    # target = df.loc[:, 'salary']
    # features_train, features_test, target_train, target_test = train_test_split(features, 
    #                                                                             target,
    #                                                                             test_size = 0.1,
    #                                                                             random_state = 42)
    
    features_train = df[df['year'] <= 2024]
    target_train = df[df['year'] <= 2024]
    
    features_test = df[df['year'] >= 2025]
    target_test = df[df['year'] >= 2025]



    features_train = features_train.drop('salary', axis=1)
    features_test = features_test.drop('salary', axis=1)
    target_train = target_train.loc[:, 'salary']
    target_test = target_test.loc[:, 'salary']

    return features_train, features_test, target_train, target_test








# ОЦЕНКА МОДЕЛЕЙ
# ══════════════════════════════════════════════════════════════════════════════

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def result(results_df, model_name, y_true, y_pred):
    """
    Функция считает метрики и добавляет их в общую таблицу результатов.
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import numpy as np
    
    # Считаем метрики
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    # Добавляем строку (или перезаписываем, если модель с таким именем уже есть)
    results_df.loc[model_name] = [mae, rmse, r2]
    
    return results_df



def generate_skill_meta(feature_names):
    """
    Строит словарь метаданных для каждого признака после препроцессора.

    Препроцессор даёт имена вида:
        "multi_language__Python"   → prefix="multi_language", skill="Python"
        "cat__education"           → prefix="cat",            skill="education"
        "num__work_exp"            → prefix="num",            skill="work_exp"
        "remainder__year"          → prefix="remainder",      skill="year"

    Разделитель — двойное подчёркивание "__" (sklearn-стандарт).
    """
    skill_meta = {}
    for col in feature_names:
        if "__" in col:
            prefix, skill = col.split("__", maxsplit=1)
        else:
            prefix, skill = col, col
        skill_meta[col] = {"level": prefix, "skill": skill}
    return skill_meta

# ============================================================
# 1. СЛОВАРЬ КАТЕГОРИЙ РОЛЕЙ
# ============================================================
# Lokale Projektmodule
import importlib
import config_mappings as cfg

importlib.reload(cfg)


# ============================================================
# 2. БАЗОВЫЕ ФУНКЦИИ ОБРАБОТКИ
# ============================================================

def parse_roles(devtype_str):
    """Разбивает строку devtype на список ролей."""
    if not devtype_str or str(devtype_str).strip() in ('Unknown', 'nan', 'NaN', ''):
        return []
    return [r.strip() for r in str(devtype_str).split(';') if r.strip()]


def get_role_categories(devtype_str, mapping=cfg.role_category_mapping):
    """Возвращает список уникальных категорий для строки devtype."""
    roles = parse_roles(devtype_str)
    cats = [mapping.get(r, 'Other') for r in roles]
    seen = set()
    return [c for c in cats if not (c in seen or seen.add(c))]


def classify_data_role_v2(devtype_str, data_role_mapping):
    """Определяет основную дата-роль. Возвращает None если дата-роли нет."""
    roles = parse_roles(devtype_str)
    for role in roles:
        mapped = data_role_mapping.get(role)
        if mapped:
            return mapped
    return None


def compute_role_count(devtype_str):
    """Общее количество ролей в строке."""
    return len(parse_roles(devtype_str))


def compute_data_role_purity(devtype_str, mapping=cfg.role_category_mapping):
    """
    Доля дата-ролей от общего числа ролей.
    1.0 — чистый дата-специалист, 0.0 — нет дата-ролей вообще.
    """
    roles = parse_roles(devtype_str)
    if not roles:
        return 0.0
    data_count = sum(1 for r in roles if mapping.get(r) == 'Data')
    return data_count / len(roles)


def compute_category_flags(devtype_str, mapping=cfg.role_category_mapping):
    """Бинарные флаги наличия каждой категории (has_data, has_developer, ...)."""
    cats = set(get_role_categories(devtype_str, mapping))
    all_cats = ['Data', 'Developer', 'Manager', 'Other']
    return {f'has_{c.lower().replace("/", "_")}': int(c in cats) for c in all_cats}


# ============================================================
# 3. НОВЫЕ ФУНКЦИИ: мультиколонки и счётчики
# ============================================================

def extract_data_roles_str(devtype_str, mapping=cfg.role_category_mapping):
    """
    Возвращает строку с дата-ролями через ';'.
    Используется как мультизначная колонка для CountVectorizer.

    Пример:
        "Data scientist; Developer, back-end; DevOps specialist"
        → "Data scientist"

        "Data or business analyst; Engineer, data; Developer, full-stack"
        → "Data or business analyst;Engineer, data"
    """
    roles = parse_roles(devtype_str)
    data_roles = [r for r in roles if mapping.get(r) == 'Data']
    return ';'.join(data_roles) if data_roles else 'None'


def extract_other_roles_str(devtype_str, mapping=cfg.role_category_mapping):
    """
    Возвращает строку с НЕ-дата ролями через ';'.
    Используется как мультизначная колонка для CountVectorizer.

    Пример:
        "Data scientist; Developer, back-end; DevOps specialist"
        → "Developer, back-end;DevOps specialist"

        "Data or business analyst"  (единственная роль — дата)
        → "None"
    """
    roles = parse_roles(devtype_str)
    other_roles = [r for r in roles if mapping.get(r) != 'Data']
    return ';'.join(other_roles) if other_roles else 'None'


def compute_role_counts_by_category(devtype_str, mapping=cfg.role_category_mapping):
    """
    Возвращает dict с количеством ролей в каждой категории.

    Пример:
        "Data scientist; Developer, back-end; Developer, full-stack; DevOps specialist"
        → {'count_data': 1, 'count_developer': 2, 'count_devops_infrastructure': 1,
           'count_manager': 0, ...}
    """
    roles = parse_roles(devtype_str)
    all_cats = ['Data', 'Developer', 'Manager', 'Other']
    counts = {f'count_{c.lower().replace("/", "_")}': 0 for c in all_cats}
    for r in roles:
        cat = mapping.get(r, 'Other')
        key = f'count_{cat.lower().replace("/", "_")}'
        counts[key] += 1
    return counts


# ============================================================
# 4. ОСНОВНАЯ ФУНКЦИЯ ОБОГАЩЕНИЯ DataFrame
# ============================================================

def enrich_devtype_features(df, devtype_col='devtype', mapping=cfg.role_category_mapping):
    """
    Добавляет все производные признаки из devtype в DataFrame.

    Новые колонки:
      Числовые (для num_cols):
        role_count          — общее кол-во ролей
        data_role_purity    — доля дата-ролей (0.0–1.0)
        count_data          — кол-во дата-ролей
        count_developer     — кол-во developer-ролей
        count_manager       — ... и т.д. для каждой категории

      Бинарные флаги (для num_cols, уже 0/1):
        has_data, has_developer, has_manager, ...

      Мультизначные строки (для multi_cols + CountVectorizer):
        devtype_data        — дата-роли через ';' ("Data scientist;Engineer, data")
        devtype_other       — остальные роли через ';' ("Developer, back-end;DevOps specialist")
    """
    df = df.copy()

    # ── Числовые: общий счётчик и purity ─────────────────────────────────────
    df['role_count']       = df[devtype_col].apply(compute_role_count)
    df['data_role_purity'] = df[devtype_col].apply(
        lambda x: compute_data_role_purity(x, mapping)
    )

    # # ── Числовые: счётчики по категориям (count_data, count_developer, ...) ──
    # counts_df = df[devtype_col].apply(
    #     lambda x: pd.Series(compute_role_counts_by_category(x, mapping))
    # )
    # df = pd.concat([df, counts_df], axis=1)

    # # ── Бинарные флаги (has_data, has_developer, ...) ─────────────────────────
    # flags_df = df[devtype_col].apply(
    #     lambda x: pd.Series(compute_category_flags(x, mapping))
    # )
    # df = pd.concat([df, flags_df], axis=1)

    # ── Мультизначные строки для CountVectorizer ─────────────────────────────
    df['devtype_data']  = df[devtype_col].apply(
        lambda x: extract_data_roles_str(x, mapping)
    )
    df['devtype_other'] = df[devtype_col].apply(
        lambda x: extract_other_roles_str(x, mapping)
    )

    return df


# ============================================================
# 5. SAMPLE WEIGHTS
# ============================================================

def compute_sample_weights(df, strategy='purity'):
    """
    Вычисляет sample_weight для обучения.

    strategy='purity'  — вес = доля дата-ролей (рекомендуется)
    strategy='inverse' — вес = 1 / role_count
    strategy='binary'  — 1 если чистый дата, 0.3 иначе
    """
    if strategy == 'purity':
        return df['data_role_purity'].clip(lower=0.1)
    elif strategy == 'inverse':
        return (1 / df['role_count']).clip(upper=1.0)
    elif strategy == 'binary':
        return df['data_role_purity'].apply(lambda p: 1.0 if p == 1.0 else 0.3)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


# ============================================================
# 6. БЫСТРАЯ ПРОВЕРКА
# ============================================================

if __name__ == '__main__':
    import pandas as pd

    test_cases = [
        "Data or business analyst",
        "Data scientist or machine learning specialist;Developer, back-end",
        "Data or business analyst;Engineer, data;Developer, full-stack;DevOps specialist",
        "Academic researcher;Data scientist or machine learning specialist;Developer, QA or test;Engineering manager",
        "Database administrator;Designer;Developer, back-end;Developer, front-end;Developer, full-stack;System administrator",
    ]

    print(f"{'Строка':<70} {'data_roles':<40} {'other_roles':<50} {'count_d':>7} {'count_dev':>9} {'purity':>7}")
    print("-" * 190)
    for t in test_cases:
        short   = (t[:67] + '...') if len(t) > 70 else t
        dr      = extract_data_roles_str(t)
        oroles  = extract_other_roles_str(t)
        counts  = compute_role_counts_by_category(t)
        purity  = compute_data_role_purity(t)
        print(f"{short:<70} {dr:<40} {oroles:<50} {counts['count_data']:>7} {counts['count_developer']:>9} {purity:>7.0%}")






def categorize_age(val):
    # 1. Сначала приводим всё к строке и убираем лишние пробелы
    val = str(val).strip()
    
    # 2. Обработка уже готовых категорий
    mapping = {
        'Under 18 years old': 'Under 18',
        '18-24 years old': '18-24',
        '25-34 years old': '25-34',
        '35-44 years old': '35-44',
        '45-54 years old': '45-54',
        '55-64 years old': '55-64',
        '65 years or older': '65+',
        'Prefer not to say': 'Unknown',
        'nan': 'Unknown',
        'Unknown': 'Unknown'
    }
    
    if val in mapping:
        return mapping[val]
    
    # 3. Обработка числовых значений
    try:
        age = float(val)
        if age < 18: return 'Under 18'
        elif 18 <= age <= 24: return '18-24'
        elif 25 <= age <= 34: return '25-34'
        elif 35 <= age <= 44: return '35-44'
        elif 45 <= age <= 54: return '45-54'
        elif 55 <= age <= 64: return '55-64'
        elif age >= 65: return '65+'
        else: return 'Unknown'
    except:
        return 'Unknown'




# ════════════════════════════════════════════════════════════════════════════
# Дополнение к utils.py
# ════════════════════════════════════════════════════════════════════════════

def fix_apostrophes(mapping: dict) -> dict:
    """
    Ersetzt typografische Apostrophe ' (U+2019) durch Standard ' (U+0027).
    Einmalig beim Laden der cfg-Mappings aufrufen.
    """
    return {
        k.replace("\u2019", "'").replace("\u2018", "'"): v
        for k, v in mapping.items()
    }


def shap_log_to_usd_skill(feat, shap_df, median_salary,
                           source_features=None, min_rows=10):
    """
    Berechnet den mittleren SHAP-Wert nur für Zeilen,
    in denen der Skill tatsächlich vorhanden ist (Quelldaten vor dem Preprocessor).

    TreeExplainer liefert für ALLE Zeilen Nicht-Null-SHAP-Werte,
    daher filtern wir über source_features statt shap != 0.

    Parameters
    ----------
    feat            : str   — z.B. "multi_language__Python"
    shap_df         : pd.DataFrame — SHAP-Werte (Zeilen = Samples, Spalten = Features)
    median_salary   : float — globaler oder kontextueller Median in Tausend USD
    source_features : pd.DataFrame — Originaldaten vor dem Preprocessor
    min_rows        : int   — Mindestanzahl Zeilen mit dem Skill (0 = kein Filter)

    Returns
    -------
    float — Gehaltseinfluss in Tausend USD (positiv = erhöht, negativ = senkt)
    """
    if feat not in shap_df.columns:
        return 0.0

    if source_features is not None and "__" in feat:
        prefix, skill_name = feat.split("__", 1)
        col_name = prefix.replace("multi_", "")

        if col_name in source_features.columns:
            has_skill = source_features[col_name].str.contains(
                skill_name, regex=False, na=False
            )
            idx = shap_df.index.intersection(source_features[has_skill].index)
        else:
            idx = shap_df.index
    else:
        idx = shap_df.index

    if min_rows > 0 and len(idx) < min_rows:
        return 0.0

    mean_shap = shap_df.loc[idx, feat].mean()
    return float(np.exp(np.log1p(median_salary) + mean_shap) - median_salary)