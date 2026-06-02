import pandas as pd
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Функция 1: нормализация синонимов и объединение подкатегорий
# ─────────────────────────────────────────────────────────────────────────────

def normalize_multivalue_column(
    df: pd.DataFrame,
    column_name: str,
    mapping: dict[str, str],
    sep: str = ";",
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Заменяет синонимы и объединяет подкатегории в мультизначной колонке.

    Логика:
    -------
    - Разбивает каждую ячейку по разделителю sep
    - Применяет mapping: старое_значение → новое_значение
    - Убирает дубликаты внутри одной строки (после схлопывания синонимов)
    - Собирает обратно через sep

    Parameters
    ----------
    df : pd.DataFrame
        Исходный датафрейм
    column_name : str
        Колонка для нормализации
    mapping : dict[str, str]
        Словарь замен. Ключ — исходное значение, значение — целевое.
        Несколько ключей могут указывать на одно значение (синонимы).
        Пример:
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
        Разделитель значений в ячейке (по умолчанию ';')
    inplace : bool
        True  — модифицирует df на месте
        False — возвращает копию (безопасный режим по умолчанию)

    Returns
    -------
    pd.DataFrame
        Датафрейм с нормализованной колонкой
    """
    result = df if inplace else df.copy()

    def _normalize_row(val):
        if pd.isna(val):
            return val
        parts = [p.strip() for p in str(val).split(sep) if p.strip()]
        # Применяем маппинг; если значения нет в словаре — оставляем как есть
        mapped = [mapping.get(p, p) for p in parts]
        # Убираем дубликаты, сохраняя порядок первого вхождения
        seen, deduped = set(), []
        for item in mapped:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return sep.join(deduped)

    result[column_name] = result[column_name].apply(_normalize_row)

    # Считаем сколько строк реально изменилось
    changed = (result[column_name] != df[column_name]).sum()
    print(f"✅ normalize_multivalue_column('{column_name}')")
    print(f"   Применено замен в маппинге: {len(mapping)}")
    print(f"   Строк изменено:             {changed:,}")
    print()

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Функция 2: редкие значения (<1%) → Other
# ─────────────────────────────────────────────────────────────────────────────

def replace_rare_with_other(
    df: pd.DataFrame,
    column_name: str,
    mapping: Optional[dict[str, str]] = None,
    threshold_pct: float = 1.0,
    other_label: str = "Other",
    sep: str = ";",
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Заменяет редкие подкатегории (доля < threshold_pct %) на other_label.

    Логика:
    -------
    1. Считает долю каждого атомарного значения от числа заполненных строк
       (так же как explore_multivalue_column)
    2. Значения ниже порога заменяет на other_label
    3. Если в одной ячейке после замены оказывается несколько Other — схлопывает в одно
    4. Опциональный mapping позволяет принудительно оставить / переименовать
       конкретные значения ДО подсчёта (например, уже применённый нормализатор)

    Parameters
    ----------
    df : pd.DataFrame
        Исходный датафрейм
    column_name : str
        Колонка для обработки
    mapping : dict[str, str] | None
        Дополнительные принудительные замены (применяются ДО расчёта порога).
        Передавайте тот же словарь что и в normalize_multivalue_column,
        если функции вызываются по очереди — тогда None.
    threshold_pct : float
        Порог в процентах (по умолчанию 1.0, т.е. <1% → Other)
    other_label : str
        Метка для редких значений (по умолчанию 'Other')
    sep : str
        Разделитель значений в ячейке
    inplace : bool
        True — меняет df на месте; False — возвращает копию

    Returns
    -------
    pd.DataFrame
        Датафрейм с заменёнными редкими значениями
    """
    result = df if inplace else df.copy()

    # Шаг 0: применяем маппинг если передан
    if mapping:
        result = normalize_multivalue_column(
            result, column_name, mapping, sep=sep, inplace=True
        )

    # Шаг 1: считаем частоты на текущем (уже нормализованном) столбце
    clean = result[column_name].dropna().astype(str)
    total_valid = len(clean)

    if total_valid == 0:
        print(f"❌ Колонка '{column_name}' пуста.")
        return result

    flat = clean.str.split(sep).explode().str.strip()
    flat = flat[flat != ""]
    counts = flat.value_counts()
    share = (counts / total_valid) * 100

    rare = set(share[share < threshold_pct].index)
    # other_label сам никогда не становится "редким"
    rare.discard(other_label)

    print(f"✅ replace_rare_with_other('{column_name}', threshold={threshold_pct}%)")
    print(f"   Всего уникальных значений:  {len(counts)}")
    print(f"   Редких (< {threshold_pct}%):        {len(rare)}")
    if rare:
        print(f"   → будут заменены на '{other_label}':")
        for v in sorted(rare, key=lambda x: share.get(x, 0)):
            print(f"     {share.get(v, 0):>5.2f}%  {v}")
    print()

    # Шаг 2: применяем замену построчно
    def _replace_row(val):
        if pd.isna(val):
            return val
        parts = [p.strip() for p in str(val).split(sep) if p.strip()]
        replaced = [other_label if p in rare else p for p in parts]
        # Убираем дубликаты Other, сохраняем порядок
        seen, deduped = set(), []
        for item in replaced:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return sep.join(deduped)

    result[column_name] = result[column_name].apply(_replace_row)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Маппинги (примеры — редактируйте под свои данные)
# ─────────────────────────────────────────────────────────────────────────────

# Маппинг для колонки 'language'
LANGUAGE_MAPPING = {
    # Синонимы Bash/Shell/PowerShell
    "Bash/Shell":                "Bash/Shell/PowerShell",
    "PowerShell":                "Bash/Shell/PowerShell",
    "Bash/Shell (all shells)":   "Bash/Shell/PowerShell",

    # MATLAB — оба написания к одному
    "MATLAB":                    "Matlab",

    # Lisp-диалекты к одному написанию
    "Lisp":                      "LISP",

    # COBOL — разные капитализации
    "Cobol":                     "COBOL",

    # VBA и Visual Basic
    "Visual Basic (.Net)":       "VBA",

    # Unknown убираем (заменяем на Other через порог или прямо здесь)
    "Unknown":                   "Other",
}

# Маппинг для колонки 'database' (пример — дополняйте по результатам explore_)
DATABASE_MAPPING = {
    "Microsoft SQL Server":      "SQL Server",
    "MS SQL":                    "SQL Server",
    "MariaDB":                   "MySQL/MariaDB",
    "MySQL":                     "MySQL/MariaDB",
}

# Маппинг для колонки 'platform' (пример)
PLATFORM_MAPPING = {
    "Google Cloud Platform":     "Google Cloud",
    "GCP":                       "Google Cloud",
    "Amazon Web Services (AWS)": "AWS",
}


# ─────────────────────────────────────────────────────────────────────────────
# Применение
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Предполагаем что df_data уже загружен и прошёл фильтрацию

    # ── Шаг 1: нормализуем синонимы ────────────────────────────────────────
    df_data = normalize_multivalue_column(
        df_data,
        column_name="language",
        mapping=LANGUAGE_MAPPING,
    )

    # ── Шаг 2: редкие (<1%) → Other ────────────────────────────────────────
    # mapping=None т.к. нормализация уже применена на шаге 1
    df_data = replace_rare_with_other(
        df_data,
        column_name="language",
        mapping=None,
        threshold_pct=1.0,
        other_label="Other",
    )

    # ── Проверка ────────────────────────────────────────────────────────────
    from explore_multivalue_column import explore_multivalue_column  # ваша функция
    result = explore_multivalue_column(df_data, "language")
    print(result)

    # ── То же для других колонок ────────────────────────────────────────────
    df_data = normalize_multivalue_column(
        df_data, "database", mapping=DATABASE_MAPPING
    )
    df_data = replace_rare_with_other(
        df_data, "database", threshold_pct=1.0
    )

    df_data = normalize_multivalue_column(
        df_data, "platform", mapping=PLATFORM_MAPPING
    )
    df_data = replace_rare_with_other(
        df_data, "platform", threshold_pct=1.0
    )
