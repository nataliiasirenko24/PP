# ============================================================
# 1. СЛОВАРЬ КАТЕГОРИЙ РОЛЕЙ
# ============================================================
import pandas as pd
ROLE_CATEGORY_MAPPING = {
    # Data
    "Data engineer":                              "Data",
    "Data or business analyst":                   "Data",
    "Data scientist":                             "Data",
    "Data scientist or machine learning specialist": "Data",
    "Database administrator":                     "Data",
    "Database administrator or engineer":         "Data",
    "Engineer, data":                             "Data",
    "Scientist":                                  "Data",
    "AI/ML engineer":                             "Data",
    "Applied scientist":                          "Data",
    "Financial analyst or engineer":              "Data",

    # Developer
    "Developer Advocate":                         "Developer",
    "Developer Experience":                       "Developer",
    "Developer, AI":                              "Developer",
    "Developer, AI apps or physical AI":          "Developer",
    "Developer, back-end":                        "Developer",
    "Developer, desktop or enterprise applications": "Developer",
    "Developer, embedded applications or devices": "Developer",
    "Developer, front-end":                       "Developer",
    "Developer, full-stack":                      "Developer",
    "Developer, game or graphics":                "Developer",
    "Developer, mobile":                          "Developer",
    "Developer, QA or test":                      "Developer",
    "Architect, software or solutions":           "Developer",
    "Blockchain":                                 "Developer",
    "Engineer, site reliability":                 "Developer",

    # Manager
    "Engineering manager":                        "Manager",
    "Product manager":                            "Manager",
    "Project manager":                            "Manager",
    "Senior Executive (C-Suite, VP, etc.)":       "Manager",
    "Senior executive/VP":                        "Manager",
    "Founder, technology or otherwise":           "Manager",

    # Other
    "Other (please specify):":                    "Other",
    "Student":                                    "Other",
    "Unknown":                                    "Other",
    "Educator":                                   "Other",
    "Retired":                                    "Other",
    "Academic researcher":                        "Other",
    "Research & Development role":                "Other",

    # DevOps/Infrastructure
    "DevOps engineer or professional":            "Other",
    "DevOps specialist":                          "Other",
    "System administrator":                       "Other",
    "Cloud infrastructure engineer":              "Other",

    # Design
    "Designer":                                   "Other",
    "UX, Research Ops or UI design professional": "Other",

    # Marketing
    "Marketing or sales professional":            "Other",

    # Engineering
    "Hardware Engineer":                          "Other",

    # Security
    "Cybersecurity or InfoSec professional":      "Other",
    "Security professional":                      "Other",

    # Support
    "Support engineer or analyst":                "Other",
}

# ============================================================
# 2. БАЗОВЫЕ ФУНКЦИИ ОБРАБОТКИ
# ============================================================

def parse_roles(devtype_str):
    """Разбивает строку devtype на список ролей."""
    if not devtype_str or str(devtype_str).strip() in ('Unknown', 'nan', 'NaN', ''):
        return []
    return [r.strip() for r in str(devtype_str).split(';') if r.strip()]


def get_role_categories(devtype_str, mapping=ROLE_CATEGORY_MAPPING):
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


def compute_data_role_purity(devtype_str, mapping=ROLE_CATEGORY_MAPPING):
    """
    Доля дата-ролей от общего числа ролей.
    1.0 — чистый дата-специалист, 0.0 — нет дата-ролей вообще.
    """
    roles = parse_roles(devtype_str)
    if not roles:
        return 0.0
    data_count = sum(1 for r in roles if mapping.get(r) == 'Data')
    return data_count / len(roles)


def compute_category_flags(devtype_str, mapping=ROLE_CATEGORY_MAPPING):
    """Бинарные флаги наличия каждой категории (has_data, has_developer, ...)."""
    cats = set(get_role_categories(devtype_str, mapping))
    all_cats = ['Data', 'Developer', 'Manager', 'Other']
    return {f'has_{c.lower().replace("/", "_")}': int(c in cats) for c in all_cats}


# ============================================================
# 3. НОВЫЕ ФУНКЦИИ: мультиколонки и счётчики
# ============================================================

def extract_data_roles_str(devtype_str, mapping=ROLE_CATEGORY_MAPPING):
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


def extract_other_roles_str(devtype_str, mapping=ROLE_CATEGORY_MAPPING):
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


def compute_role_counts_by_category(devtype_str, mapping=ROLE_CATEGORY_MAPPING):
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

def enrich_devtype_features(df, devtype_col='devtype', mapping=ROLE_CATEGORY_MAPPING):
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
