# ════════════════════════════════════════════════════════════════════════════
# utils.py — Hilfsfunktionen für das Data Career Salary Predictor Projekt
#
# Abschnitte:
#   1. Importe
#   2. Datenladen & Normalisierung
#   3. Datenbereinigung & Feature Engineering
#   4. Rollenklassifizierung (DevType)
#   5. EDA — Analyse & Visualisierung
#   6. Modellierung & Evaluation
#   7. SHAP — Interpretierbarkeit
# ════════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════════
# 1. IMPORTE
# ════════════════════════════════════════════════════════════════════════════

import os
import re
import textwrap
import importlib
import webbrowser
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder

import config_mappings as cfg
importlib.reload(cfg)


# ════════════════════════════════════════════════════════════════════════════
# 2. DATENLADEN & NORMALISIERUNG
# ════════════════════════════════════════════════════════════════════════════

def detect_encoding(path: str) -> str:
    """
    Erkennt die Zeichenkodierung einer CSV-Datei anhand der ersten Bytes (BOM-Erkennung).
    UTF-8 BOM ist häufig in Stack Overflow Survey CSV-Dateien vorhanden.
    """
    with open(path, "rb") as f:
        raw = f.read(4)
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "utf-16"
    return "utf-8"


def read_file(path: str) -> pd.DataFrame:
    """
    Liest eine CSV-Datei mit automatischer Erkennung von Kodierung und Trennzeichen.
    Probiert mehrere Kombinationen durch und gibt den ersten erfolgreichen Versuch zurück.
    """
    enc = detect_encoding(path)
    for encoding in dict.fromkeys([enc, "utf-8", "utf-8-sig", "latin-1"]):
        for sep in (",", ";", "\t"):
            try:
                return pd.read_csv(
                    path, sep=sep, encoding=encoding,
                    low_memory=False, on_bad_lines="skip",
                    na_values=["nan", "NaN", "<NA>", ""],
                )
            except Exception:
                continue
    raise ValueError(f"Datei konnte nicht gelesen werden: {path}")


def load_year(year: int, data_dir: str = "data"):
    """
    Sucht die Umfragedatei für ein bestimmtes Jahr im angegebenen Verzeichnis
    und liest sie ein. Gibt (DataFrame, Dateiname) oder (None, None) zurück,
    wenn keine passende Datei gefunden wurde.
    """
    candidates = [
        os.path.join(data_dir, f"so_{year}.csv"),
        os.path.join(data_dir, f"{year}.csv"),
        os.path.join(data_dir, f"so_{year}.xlsx"),
        os.path.join(data_dir, f"{year}.xlsx"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if path is None:
        return None, None
    return read_file(path), os.path.basename(path)


def normalize_year(df_raw: pd.DataFrame, year: int, schema: dict) -> pd.DataFrame:
    """
    Benennt Spalten eines Jahrgangs anhand des Schema-Mappings in kanonische Namen um.
    Fügt die Spalte 'year' hinzu und konvertiert 'salary' in einen numerischen Typ.

    Parameters
    ----------
    df_raw : pd.DataFrame — Rohdaten eines Umfragejahres
    year   : int          — Umfragejahr
    schema : dict         — cfg.schema mit kanonischen Spaltennamen pro Jahr

    Returns
    -------
    pd.DataFrame mit kanonischen Spaltennamen und der Spalte 'year'
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


# ════════════════════════════════════════════════════════════════════════════
# 3. DATENBEREINIGUNG & FEATURE ENGINEERING
# ════════════════════════════════════════════════════════════════════════════

def overview(data: pd.DataFrame) -> None:
    """
    Zeigt eine kompakte Übersicht über den DataFrame:
    Datentypen, Anzahl gültiger Werte, fehlende Werte (absolut und prozentual),
    Kardinalität sowie alle einzigartigen Werte je Spalte.
    """
    display(pd.DataFrame({
        "dtype":     data.dtypes,
        "count":     data.count(),
        "missing_n": data.isna().sum(),
        "missing_%": data.isna().mean() * 100,
        "uniques_n": data.nunique(),
        "uniques":   [data[c].unique() for c in data.columns],
    }))


def drop_columns(df: pd.DataFrame, columns_to_drop: list) -> pd.DataFrame:
    """
    Entfernt eine Liste von Spalten aus dem DataFrame, ohne einen Fehler zu werfen,
    wenn eine Spalte nicht vorhanden ist (errors='ignore').
    """
    return df.drop(columns=columns_to_drop, errors="ignore")


def optimize_types(data: pd.DataFrame, cat_cols: list, num_cols: list) -> pd.DataFrame:
    """
    Reduziert den Speicherbedarf des DataFrames durch Typoptimierung.
    Numerische Spalten werden auf den kleinstmöglichen Ganzzahl- oder Float-Typ
    herunterskaliert. Kategoriale Spalten werden in den Typ 'category' konvertiert.

    Parameters
    ----------
    data     : pd.DataFrame — Eingabe-DataFrame
    cat_cols : list         — Liste kategorialer Spaltennamen
    num_cols : list         — Liste numerischer Spaltennamen

    Returns
    -------
    pd.DataFrame mit optimierten Datentypen
    """
    for c in num_cols:
        if c not in data.columns:
            continue
        if not pd.api.types.is_numeric_dtype(data[c]):
            continue
        if (data[c] % 1 != 0).any():
            data[c] = data[c].astype("float32")
        else:
            if data[c].min() < 0:
                if data[c].min() >= -128 and data[c].max() <= 127:
                    data[c] = data[c].astype("int8")
                elif data[c].min() >= -32768 and data[c].max() <= 32767:
                    data[c] = data[c].astype("int16")
                else:
                    data[c] = data[c].astype("int32")
            else:
                if data[c].max() < 255:
                    data[c] = data[c].astype("uint8")
                elif data[c].max() < 65535:
                    data[c] = data[c].astype("uint16")
                else:
                    data[c] = data[c].astype("int32")
    for c in cat_cols:
        if c in data.columns:
            data[c] = data[c].astype("category")
    return data


def fix_apostrophes(mapping: dict) -> dict:
    """
    Ersetzt typografische Apostrophe ' (U+2019) und ' (U+2018) durch
    den Standard-Apostroph ' (U+0027) in allen Schlüsseln des Mappings.
    Einmalig beim Laden der cfg-Mappings aufrufen.
    """
    return {
        k.replace("\u2019", "'").replace("\u2018", "'"): v
        for k, v in mapping.items()
    }


def impute_work_exp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Erstellt den Indikator 'work_exp_is_missing' und füllt fehlende Werte
    in 'workexp' durch den gruppenspezifischen Median auf (gruppiert nach
    'education' und 'yearscode'). Verbleibende NaN-Werte werden durch
    den globalen Median ersetzt.
    """
    df = df.copy()
    df["work_exp_is_missing"] = df["workexp"].isna().astype(int)
    medians = df.groupby(
        ["education", "yearscode"], observed=True
    )["workexp"].transform("median")
    df["workexp"] = df["workexp"].fillna(medians)
    global_median = df["workexp"].median()
    df["workexp"] = df["workexp"].fillna(global_median)
    return df


def merge_feature_cols(
    df: pd.DataFrame,
    col_main: str,
    col_entry: str,
    col_result: str,
) -> pd.DataFrame:
    """
    Führt zwei Mehrfachwert-Spalten zusammen und schreibt das Ergebnis
    in 'col_result'. Doppelte Einträge innerhalb einer Zeile werden entfernt.
    Die Originalspalten bleiben unverändert.
    """
    df = df.copy()
    combined = (
        df[col_main].fillna("").astype(str) + ";" +
        df[col_entry].fillna("").astype(str)
    ).str.strip(";")

    def _clean(x: str) -> str:
        if not x:
            return ""
        parts = [p.strip() for p in x.split(";") if p.strip()]
        return ";".join(dict.fromkeys(parts))

    df[col_result] = combined.apply(_clean)
    return df


def normalize_multivalue_column(
    df: pd.DataFrame,
    column_name: str,
    mapping: dict,
    sep: str = ";",
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Wendet ein Wörterbuch-Mapping auf jede atomare Teilkategorie einer
    Mehrfachwert-Spalte an und dedupliziert die Ergebnisse zeilenweise.

    Parameters
    ----------
    df          : pd.DataFrame — Eingabe-DataFrame
    column_name : str          — Name der Mehrfachwert-Spalte
    mapping     : dict         — Ersetzungswörterbuch {alt: neu}
    sep         : str          — Trennzeichen innerhalb der Zellen
    inplace     : bool         — True = in-place, False = Kopie (Standard)

    Returns
    -------
    pd.DataFrame mit normalisierter Spalte
    """
    result = df if inplace else df.copy()

    def _normalize_row(val):
        if pd.isna(val):
            return val
        parts = [p.strip() for p in str(val).split(sep) if p.strip()]
        mapped = [mapping.get(p, p) for p in parts]
        seen, deduped = set(), []
        for item in mapped:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return sep.join(deduped)

    result[column_name] = result[column_name].apply(_normalize_row)
    changed = (result[column_name] != df[column_name]).sum()
    return result


def replace_rare_with_other(
    df: pd.DataFrame,
    column_name: str,
    mapping: Optional[dict] = None,
    threshold: float = 5,
    other_label: str = "Other",
    sep: str = ";",
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Ersetzt seltene Teilkategorien (Anteil < threshold %) in einer
    Mehrfachwert-Spalte durch 'other_label'.

    Ablauf:
    1. Optionales Mapping wird zuerst angewendet (normalize_multivalue_column).
    2. Frequenzberechnung je atomarem Wert.
    3. Werte unter dem Schwellenwert → 'other_label'.
    4. Mehrfach vorkommendes 'other_label' in einer Zelle wird dedupliziert.

    Parameters
    ----------
    df          : pd.DataFrame     — Eingabe-DataFrame
    column_name : str              — Zu verarbeitende Spalte
    mapping     : dict | None      — Optionale Vorverarbeitung (wie normalize_multivalue_column)
    threshold   : float            — Schwellenwert in Prozent (Standard: 5 %)
    other_label : str              — Label für seltene Werte (Standard: 'Other')
    sep         : str              — Trennzeichen innerhalb der Zellen
    inplace     : bool             — True = in-place, False = Kopie (Standard)

    Returns
    -------
    pd.DataFrame mit ersetzten seltenen Werten
    """
    result = df if inplace else df.copy()

    if mapping:
        result = normalize_multivalue_column(
            result, column_name, mapping, sep=sep, inplace=True
        )

    clean = result[column_name].dropna().astype(str)
    total_valid = len(clean)
    flat = clean.str.split(sep).explode().str.strip()
    flat = flat[flat != ""]
    counts = flat.value_counts()
    share = (counts / total_valid) * 100
    rare = set(share[share < threshold].index)
    rare.discard(other_label)

    def _replace_row(val):
        if pd.isna(val):
            return val
        parts = [p.strip() for p in str(val).split(sep) if p.strip()]
        replaced = [other_label if p in rare else p for p in parts]
        seen, deduped = set(), []
        for item in replaced:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return sep.join(deduped)

    result[column_name] = result[column_name].apply(_replace_row)
    return result


def clean_employment_status(text: str) -> str:
    """
    Klassifiziert einen Beschäftigungsstatus-String anhand von Schlüsselwörtern
    in eine von vier Kategorien: 'Full-time', 'Freelance', 'Part-time', 'Unknown'.
    """
    if not isinstance(text, str):
        return "Unknown"
    text_lower = text.lower()
    if "full-time" in text_lower or text_lower == "employed":
        return "Full-time"
    if any(k in text_lower for k in ("independent contractor", "freelancer", "self-employed")):
        return "Freelance"
    if "part-time" in text_lower:
        return "Part-time"
    return "Unknown"


def categorize_currency(text: str) -> str:
    """
    Ordnet eine Währungsbeschreibung (z. B. 'United States dollar') einem
    dreistelligen ISO-Währungscode zu (z. B. 'USD').
    Unbekannte Währungen werden als 'Other' klassifiziert.
    """
    text = str(text)
    currency_map = {
        "USD": ["United States", "USD"],
        "EUR": ["European Euro", "EUR"],
        "GBP": ["Pound sterling", "GBP"],
        "INR": ["Indian rupee", "INR"],
        "CAD": ["Canadian dollar", "CAD"],
        "BRL": ["Brazilian real", "BRL"],
        "AUD": ["Australian dollar", "AUD"],
        "PLN": ["Polish zloty", "PLN"],
        "SEK": ["Swedish krona", "SEK"],
        "CHF": ["Swiss franc", "CHF"],
        "RUB": ["Russian ruble", "RUB"],
        "CZK": ["Czech koruna", "CZK"],
        "ILS": ["Israeli new shekel", "ILS"],
        "UAH": ["Ukrainian hryvnia", "UAH"],
        "TRY": ["Turkish lira", "TRY"],
    }
    for code, keywords in currency_map.items():
        if any(kw in text for kw in keywords):
            return code
    return "Other"


def categorize_age(val) -> str:
    """
    Ordnet einen Alterswert (numerisch oder als Textbereich) einer
    standardisierten Altersgruppe zu, z. B. '25-34 years old' → '25-34'.
    Unbekannte oder fehlende Werte → 'Unknown'.
    """
    val = str(val).strip()
    mapping = {
        "Under 18 years old": "Under 18",
        "18-24 years old":    "18-24",
        "25-34 years old":    "25-34",
        "35-44 years old":    "35-44",
        "45-54 years old":    "45-54",
        "55-64 years old":    "55-64",
        "65 years or older":  "65+",
        "Prefer not to say":  "Unknown",
        "nan":                "Unknown",
        "Unknown":            "Unknown",
    }
    if val in mapping:
        return mapping[val]
    try:
        age = float(val)
        if age < 18:         return "Under 18"
        elif age <= 24:      return "18-24"
        elif age <= 34:      return "25-34"
        elif age <= 44:      return "35-44"
        elif age <= 54:      return "45-54"
        elif age <= 64:      return "55-64"
        elif age >= 65:      return "65+"
        else:                return "Unknown"
    except Exception:
        return "Unknown"


def group_rare_categories(data: pd.DataFrame, c: str, threshold: float = 5) -> pd.Series:
    """
    Fasst seltene Ausprägungen einer kategorischen Spalte (Anteil < threshold %)
    zur Gruppe 'Other' zusammen. Unterstützt sowohl 'category'- als auch 'object'-Dtype.

    Parameters
    ----------
    data      : pd.DataFrame — Eingabe-DataFrame
    c         : str          — Spaltenname
    threshold : float        — Schwellenwert in Prozent (Standard: 5 %)

    Returns
    -------
    pd.Series mit zusammengefassten seltenen Werten
    """
    series = data[c].copy()
    probs = series.value_counts(normalize=True)
    rare_categories = probs[probs < threshold / 100].index
    if str(series.dtype) == "category":
        if "Other" not in series.cat.categories:
            series = series.cat.add_categories("Other")
    return series.replace(rare_categories, "Other")


# ════════════════════════════════════════════════════════════════════════════
# 4. ROLLENKLASSIFIZIERUNG (DevType)
# ════════════════════════════════════════════════════════════════════════════

def parse_roles(devtype_str: str) -> list:
    """
    Zerlegt einen DevType-String (';'-getrennt) in eine Liste einzelner Rollen.
    Ungültige Werte ('Unknown', 'nan', leer) → leere Liste.
    """
    if not devtype_str or str(devtype_str).strip() in ("Unknown", "nan", "NaN", ""):
        return []
    return [r.strip() for r in str(devtype_str).split(";") if r.strip()]


def get_role_categories(
    devtype_str: str,
    mapping: dict = cfg.role_category_mapping,
) -> list:
    """
    Gibt eine geordnete Liste eindeutiger Rollenkategorien für einen DevType-String zurück,
    z. B. ['Data', 'Developer'].
    """
    roles = parse_roles(devtype_str)
    cats = [mapping.get(r, "Other") for r in roles]
    seen = set()
    return [c for c in cats if not (c in seen or seen.add(c))]


def classify_data_role(devtype, data_role_mapping: list):
    """
    Gibt die erste passende Data-Rollenkategorie zurück oder None,
    wenn keine Data-Rolle gefunden wurde.

    Parameters
    ----------
    devtype           : str | NaN       — DevType-Zellenwert
    data_role_mapping : list of tuples  — cfg.DATA_ROLE_MAPPING
    """
    if pd.isna(devtype):
        return None
    roles = {r.strip() for r in str(devtype).split(";")}
    for category, keywords in data_role_mapping:
        if any(kw in roles for kw in keywords):
            return category
    return None


def classify_data_role_v2(
    devtype_str: str,
    data_role_mapping: dict,
) -> Optional[str]:
    """
    Bestimmt die primäre Data-Rolle aus einem DevType-String anhand eines
    Wörterbuch-Mappings. Gibt None zurück, wenn keine Data-Rolle vorhanden ist.
    """
    roles = parse_roles(devtype_str)
    for role in roles:
        mapped = data_role_mapping.get(role)
        if mapped:
            return mapped
    return None


def compute_role_count(devtype_str: str) -> int:
    """
    Gibt die Gesamtzahl der Rollen in einem DevType-String zurück.
    """
    return len(parse_roles(devtype_str))


def compute_data_role_purity(
    devtype_str: str,
    mapping: dict = cfg.role_category_mapping,
) -> float:
    """
    Berechnet den Anteil der Data-Rollen an allen Rollen (0.0–1.0).
    1.0 = reiner Data-Spezialist, 0.0 = keine Data-Rollen vorhanden.
    """
    roles = parse_roles(devtype_str)
    if not roles:
        return 0.0
    data_count = sum(1 for r in roles if mapping.get(r) == "Data")
    return data_count / len(roles)


def compute_category_flags(
    devtype_str: str,
    mapping: dict = cfg.role_category_mapping,
) -> dict:
    """
    Erstellt binäre Flags (0/1) für das Vorhandensein jeder Rollenkategorie,
    z. B. {'has_data': 1, 'has_developer': 0, 'has_manager': 0, 'has_other': 0}.
    """
    cats = set(get_role_categories(devtype_str, mapping))
    all_cats = ["Data", "Developer", "Manager", "Other"]
    return {f"has_{c.lower().replace('/', '_')}": int(c in cats) for c in all_cats}


def compute_role_counts_by_category(
    devtype_str: str,
    mapping: dict = cfg.role_category_mapping,
) -> dict:
    """
    Gibt die Anzahl der Rollen je Kategorie als Dictionary zurück,
    z. B. {'count_data': 1, 'count_developer': 2, 'count_manager': 0, 'count_other': 1}.
    """
    roles = parse_roles(devtype_str)
    all_cats = ["Data", "Developer", "Manager", "Other"]
    counts = {f"count_{c.lower().replace('/', '_')}": 0 for c in all_cats}
    for r in roles:
        cat = mapping.get(r, "Other")
        key = f"count_{cat.lower().replace('/', '_')}"
        counts[key] += 1
    return counts


def extract_data_roles_str(
    devtype_str: str,
    mapping: dict = cfg.data_role_mapping,
                        ) -> str:
    """
    Gibt alle Data-Rollen als ';'-getrennten String zurück.
    Wird als Mehrfachwert-Spalte für den CountVectorizer verwendet.
    Beispiel: "Data scientist;Engineer, data" → "Data scientist;Engineer, data"
    Keine Data-Rollen → "None"
    """
    roles = parse_roles(devtype_str)
    data_roles = [r for r in roles if mapping.get(r) == "Data"]
    return ";".join(data_roles) if data_roles else "None"


def extract_other_roles_str(
    devtype_str: str,
    mapping: dict = cfg.role_category_mapping,
) -> str:
    """
    Gibt alle Nicht-Data-Rollen als ';'-getrennten String zurück.
    Wird als Mehrfachwert-Spalte für den CountVectorizer verwendet.
    Beispiel: "Data scientist;Developer, back-end" → "Developer, back-end"
    Nur Data-Rollen vorhanden → "None"
    """
    roles = parse_roles(devtype_str)
    other_roles = [r for r in roles if mapping.get(r) != "Data"]
    return ";".join(other_roles) if other_roles else "None"

def enrich_devtype_features(
    df: pd.DataFrame,
    devtype_col: str = "devtype",
    mapping: dict = {#cfg.role_category_mapping,

            # Data-Rollen
            "Data engineer":                                "Data",
            "Data or business analyst":                     "Data",
            "Data scientist":                               "Data",
            "Data scientist or machine learning specialist": "Data",
            "Database administrator":                       "Data",
            "Database administrator or engineer":           "Data",
            "Engineer, data":                               "Data",
            "AI/ML engineer":                               "Data",
            "Financial analyst or engineer":                "Data",
            "Developer, AI":                                "Data",
            "Developer, AI apps or physical AI":            "Data",
        
            # Developer-Rollen
            "Developer, front-end":                          "Developer Software Engineering",
            "Developer, full-stack":                         "Developer Software Engineering",
            "Developer, game or graphics":                   "Developer Software Engineering",
            "Developer, mobile":                             "Developer Software Engineering",
            "Developer, desktop or enterprise applications": "Developer Software Engineering",
            "Developer, back-end":                           "Developer Software Engineering",
            
            "Developer Experience":                          "Developer Platform & Infrastructure",
            "Developer, QA or test":                         "Developer Platform & Infrastructure",
            "Architect, software or solutions":              "Developer Platform & Infrastructure",
            
            "Developer, embedded applications or devices":   "Developer Hardware & Systems",
            "Hardware Engineer":                             "Developer Hardware & Systems",


            "Developer Advocate":                            "Developer Community & Specialized",
            "Blockchain":                                    "Developer Community & Specialized",

            "Engineering manager":                           "Management",
            "Product manager":                               "Management",
            "Project manager":                               "Management",
            "Senior Executive (C-Suite, VP, etc.)":          "Management",
            "Senior executive (C-suite, VP, etc.)":          "Management",
            "Senior executive/VP":                           "Management",
            "Founder, technology or otherwise":              "Management",

            "DevOps engineer or professional":               "DevOps & SRE",
            "DevOps specialist":                             "DevOps & SRE",
            "System administrator":                          "DevOps & SRE",
            "Cloud infrastructure engineer":                 "DevOps & SRE",
            "Engineer, site reliability":                    "DevOps & SRE",

            "Designer":                                      "Designer",
            "UX, Research Ops or UI design professional":    "Designer",
     
            "Cybersecurity or InfoSec professional":         "Security",
            "Security professional":                         "Security",

            "Academic researcher":                           "Research",
            "Research & Development role":                   "Research",
            "Scientist":                                     "Research",
            "Applied scientist":                             "Research",

            "Student":                                       "Student",

            "Marketing or sales professional":               "Other",
            "Support engineer or analyst":                   "Other",
            "Other (please specify):":                       "Other",
            "Unknown":                                       "Other",
            "Educator":                                      "Other",
            "Retired":                                       "Other" }



) -> pd.DataFrame:
    """
    Fügt alle abgeleiteten DevType-Merkmale zum DataFrame hinzu.

    Neue Spalten:
      Numerisch:
        role_count       — Gesamtzahl der Rollen
        data_role_purity — Anteil der Data-Rollen (0.0–1.0)
      Mehrfachwert-Strings (für CountVectorizer):
        devtype_data     — Data-Rollen durch ';' getrennt
        devtype_other    — Nicht-Data-Rollen durch ';' getrennt
    """
    df = df.copy()
    df["role_count"]       = df[devtype_col].apply(compute_role_count)
    df["data_role_purity"] = df[devtype_col].apply(lambda x: compute_data_role_purity(x, mapping))

    df["devtype_data"] = df[devtype_col].apply(lambda x: extract_data_roles_str(x, mapping))
    df["devtype_other"] = df[devtype_col].apply(lambda x: extract_other_roles_str(x, mapping))
   
    return df


def compute_sample_weights(df: pd.DataFrame, strategy: str = "purity") -> pd.Series:
    """
    Berechnet sample_weight für das Modelltraining basierend auf der gewählten Strategie.

    Strategien:
        'purity'  — Gewicht = Anteil der Data-Rollen (empfohlen)
        'inverse' — Gewicht = 1 / Rollenanzahl
        'binary'  — 1.0 für reine Data-Spezialisten, 0.3 für alle anderen
    """
    if strategy == "purity":
        return df["data_role_purity"].clip(lower=0.1)
    elif strategy == "inverse":
        return (1 / df["role_count"]).clip(upper=1.0)
    elif strategy == "binary":
        return df["data_role_purity"].apply(lambda p: 1.0 if p == 1.0 else 0.3)
    else:
        raise ValueError(f"Unbekannte Strategie: {strategy}")


# ════════════════════════════════════════════════════════════════════════════
# 5. EDA — ANALYSE & VISUALISIERUNG
# ════════════════════════════════════════════════════════════════════════════

def explore_unique_values(
    df: pd.DataFrame,
    columns,
    top_n: int = 5,
    show_trash_only: bool = False,
) -> None:
    """
    Analysiert eindeutige Werte einer oder mehrerer Spalten und gibt
    absolute sowie relative Häufigkeiten aus. Optional werden nur fehlerhafte
    Strings (mit Zeilenumbrüchen, Tabs oder Mehrfachleerzeichen) angezeigt.

    Parameters
    ----------
    df             : pd.DataFrame — Eingabe-DataFrame
    columns        : str | list   — Spaltenname oder Liste von Spaltennamen
    top_n          : int          — Anzahl der häufigsten Werte (Standard: 5)
    show_trash_only: bool         — Nur fehlerhafte Strings anzeigen
    """
    if isinstance(columns, str):
        columns = [columns]

    for col in columns:
        if col not in df.columns:
            print(f"❌ Spalte '{col}' ist im DataFrame nicht vorhanden.\n" + "-" * 60)
            continue

        print(f"🔍 Spaltenanalyse: '{col}'")
        print(
            f"Zeilen: {len(df[col]):,}     "
            f"Ausgefüllt (Nicht-NaN): {df[col].notna().sum():,}     "
            f"Eindeutige Werte: {df[col].nunique():,}"
        )

        counts = df[col].value_counts(dropna=False)
        percentages = df[col].value_counts(dropna=False, normalize=True) * 100
        report_df = pd.DataFrame({"Häufigkeit": counts, "Anteil (%)": percentages.round(2)})

        if show_trash_only:
            trash_mask = report_df.index.astype(str).str.contains(
                r"[\n\t\r]|\s{2,}", regex=True
            )
            report_df = report_df[trash_mask]
            print(f"⚠️ Fehlerhafte eindeutige Werte: {len(report_df)}")
            if len(report_df) == 0:
                print("Kein verdecktes Textrauschen erkannt!")
                continue

        print(f"Anzeige der ersten {min(top_n, len(report_df))} Zeilen:")
        print(report_df.head(top_n).to_string())

        if len(report_df) > top_n:
            print(f"... und weitere {len(report_df) - top_n} eindeutige Werte (top_n anpassen).")
        print("-" * 60 + "\n")


def explore_multivalue_column(
    df: pd.DataFrame,
    columns,
    top_n: int = 5,
    sep: str = ";",
    show_trash_only: bool = False,
) -> None:
    """
    Analysiert Mehrfachwert-Spalten (';'-getrennte Mehrfachantworten) und gibt
    Häufigkeiten der einzelnen atomaren Werte aus.

    Parameters
    ----------
    df             : pd.DataFrame — Eingabe-DataFrame
    columns        : str | list   — Spaltenname oder Liste von Spaltennamen
    top_n          : int          — Anzahl der häufigsten Werte (Standard: 5)
    sep            : str          — Trennzeichen innerhalb der Zellen (Standard: ';')
    show_trash_only: bool         — Nur fehlerhafte Strings anzeigen
    """
    if isinstance(columns, str):
        columns = [columns]

    for col in columns:
        if col not in df.columns:
            print(f"❌ Spalte '{col}' ist im DataFrame nicht vorhanden.\n" + "-" * 60)
            continue

        clean_series = df[col].dropna().astype(str)
        total_valid = len(clean_series)

        if total_valid == 0:
            print(f"⚠️ Spalte '{col}' enthält keine gültigen Werte.\n" + "-" * 60)
            continue

        print(f"🔍 Spaltenanalyse: '{col}'")
        print(
            f"Zeilen: {len(df[col]):,}     "
            f"Ausgefüllt (Nicht-NaN): {total_valid:,}     "
            f"Eindeutige Werte: {df[col].nunique():,}"
        )

        flat = clean_series.str.split(sep).explode().str.strip()
        flat = flat[flat != ""]
        counts = flat.value_counts()
        percentages = (counts / total_valid * 100).round(2)
        report_df = pd.DataFrame({"Häufigkeit": counts, "Anteil (%)": percentages})
        report_df.index.name = col

        if show_trash_only:
            trash_mask = report_df.index.astype(str).str.contains(
                r"[\n\t\r]|\s{2,}", regex=True
            )
            report_df = report_df[trash_mask]
            print(f"⚠️ Fehlerhafte eindeutige Werte: {len(report_df)}")
            if len(report_df) == 0:
                print("Kein verdecktes Textrauschen erkannt!")
                continue

        print(f"Anzeige der ersten {min(top_n, len(report_df))} Zeilen:")
        print(report_df.head(top_n).to_string())

        if len(report_df) > top_n:
            print(f"... und weitere {len(report_df) - top_n} eindeutige Werte (top_n anpassen).")
        print("-" * 60 + "\n")


def eda_categorical(
    df: pd.DataFrame,
    col: str,
    *,
    plots: int | list[int] | None = None,
    year: Optional[int] = None,
    country: Optional[str] = None,
    top_n: int = 10,
    target: str = "salary",
    year_col: str = "year",
    country_col: str = "country",
    trend_years: Optional[tuple] = None,
    figsize_single: tuple = (10, 5),
    figsize_auto: bool = True,
    save_path: Optional[str] = None,
) -> None:
    """
    EDA-Dashboard für kategoriale Merkmale.

    Verfügbare Grafiken (plots-Parameter):
        1 — Marktanteile: Alle Jahre vs. 2025 (horizontale Balken)
        2 — Kreisdiagramm (bei year=) oder Jahrestrend (Marktanteile %)
        3 — Gehaltsverteilung je Kategorie (Boxplot)
        4 — Historischer Mediantrend über Jahre
        5 — Gehalts-Heatmap: Kategorie × Jahr (Median)
        6 — Violin-Plot: Gehaltsverteilung je Kategorie
        7 — Streudiagramm: Kategorie-Medianen über Jahre mit Konfidenzband
        8 — Kreisdiagramm: Anteil aller Daten (ohne Jahresfilter)
        9 — Balkendiagramm: Mediangehalt 2025 je Kategorie (sortiert)

    Parameters
    ----------
    df             : pd.DataFrame      — Eingabe-DataFrame
    col            : str               — Zu analysierendes Merkmal
    plots          : int | list | None — Grafik-Nr. (1–9), Liste davon, oder None (alle 1–4)
    year           : int | None        — Filterjahr (optional)
    country        : str | None        — Filterland (optional)
    top_n          : int               — Anzahl der Top-Kategorien (Standard: 10)
    target         : str               — Zielvariable (Standard: 'salary')
    year_col       : str               — Name der Jahresspalte
    country_col    : str               — Name der Länderspalte
    trend_years    : tuple | None      — Jahresbereich für Trend (start, end)
    figsize_single : tuple             — Größe für einzelne Grafik (Standard: (10, 6))
    figsize_auto   : bool              — Automatische Figurengröße bei mehreren Grafiken
    save_path      : str | None        — Speicherpfad für die Abbildung (optional)

    Beispiele
    ---------
    eda_categorical(df, "primary_role")               # alle 4 Standard-Grafiken
    eda_categorical(df, "primary_role", plots=3)      # nur Boxplot
    eda_categorical(df, "primary_role", plots=[1, 3]) # Marktanteile + Boxplot
    eda_categorical(df, "primary_role", plots=[3, 5, 6]) # Boxplot + Heatmap + Violin
    """

    # ── Normalisierung des plots-Parameters ──────────────────────────────
    ALL_PLOTS = [1, 2, 3, 4]
    if plots is None:
        plot_list = ALL_PLOTS
    elif isinstance(plots, int):
        plot_list = [plots]
    else:
        plot_list = sorted(set(plots))

    invalid = [p for p in plot_list if p not in range(1, 10)]
    if invalid:
        raise ValueError(f"Ungültige Grafik-Nr.: {invalid}. Gültig: 1–9.")

    # ── Datenaufbereitung ─────────────────────────────────────────────────
    data_base = df.copy()
    if country is not None and country_col in data_base.columns:
        data_base = data_base[data_base[country_col] == country]

    if data_base.empty:
        print("⚠️ DataFrame ist nach der Länderfilterung leer.")
        return

    data_2025 = (data_base[data_base[year_col] == 2025].copy()
                 if year_col in data_base.columns else pd.DataFrame())

    if year is not None:
        data_trend = data_base[data_base[year_col] == year].copy()
    elif trend_years is not None and year_col in data_base.columns:
        data_trend = data_base[
            (data_base[year_col] >= trend_years[0]) &
            (data_base[year_col] <= trend_years[1])
        ].copy()
    else:
        data_trend = data_base.copy()

    counts_all = data_base[col].value_counts()
    top_cats   = counts_all.head(top_n).index.tolist()
    n_hidden   = max(0, counts_all.shape[0] - top_n)
    order      = top_cats

    # ── Farben ────────────────────────────────────────────────────────────
    if top_n <= 20:
        base_colors = list(sns.color_palette("tab20", 20).as_hex())
        rng = np.random.default_rng(seed=4)
        rng.shuffle(base_colors)
        base_colors = base_colors[:top_n]
    else:
        base_colors = sns.color_palette("husl", top_n).as_hex()

    category_colors = {cat: base_colors[i] for i, cat in enumerate(order)}
    color_list_main = [category_colors[cat] for cat in order]

    plot_data_all      = data_base[data_base[col].isin(top_cats)].copy()
    plot_data_trend    = data_trend[data_trend[col].isin(top_cats)].copy()
    plot_data_2025     = (data_2025[data_2025[col].isin(top_cats)].copy()
                          if not data_2025.empty else pd.DataFrame())
    # Für Grafiken 3–7: gefilterter Datensatz wenn year= oder trend_years= angegeben
    plot_data_filtered = plot_data_trend if (year is not None or trend_years is not None) \
                         else plot_data_all

    # ── Figurengröße und Layout ───────────────────────────────────────────
    n_plots = len(plot_list)
    if n_plots == 1:
        fig, axes_flat = plt.subplots(1, 1, figsize=figsize_single)
        axes_flat = [axes_flat]
    else:
        ncols = 2
        nrows = (n_plots + 1) // 2
        if figsize_auto:
            figsize = (ncols * 9, nrows * max(4, top_n * 0.45))
        else:
            figsize = (18, nrows * 6)
        fig, axes_grid = plt.subplots(nrows, ncols, figsize=figsize)
        axes_flat = axes_grid.flatten().tolist()
        # Лишние оси скрываем
        for ax in axes_flat[n_plots:]:
            ax.set_visible(False)

    # ── Заголовок фигуры ──────────────────────────────────────────────────
    meta = []
    if year:          meta.append(f"Jahr: {year}")
    elif trend_years: meta.append(f"Trend: {trend_years[0]}-{trend_years[1]}")
    if country:       meta.append(country)
    meta_str   = "  |  " + "  |  ".join(meta) if meta else ""
    hidden_str = f"  (Top-{top_n} von {counts_all.shape[0]} Klassen)" if n_hidden > 0 else ""
    fig.suptitle(
        f"EDA: {col}{meta_str}{hidden_str}",
        fontsize=14, fontweight="bold", y=1.01,
    )

    # ── Zeichenfunktionen ─────────────────────────────────────────────────

    def draw_market_share(ax):
        """Plot 1 — Marktanteile: Alle Jahre vs. 2025."""
        freq_all  = plot_data_all[col].value_counts().reindex(order).fillna(0)
        pct_all   = (freq_all / len(data_base) * 100).values
        count_all = freq_all.values

        if not plot_data_2025.empty:
            freq_2025 = plot_data_2025[col].value_counts().reindex(order).fillna(0)
            pct_2025  = (freq_2025 / len(data_2025) * 100).values
            cnt_2025  = freq_2025.values
        else:
            pct_2025, cnt_2025 = np.zeros(len(order)), np.zeros(len(order))

        y_rev      = np.arange(len(order))[::-1]
        bar_width  = 0.38
        bars_all   = ax.barh(y_rev + bar_width / 2, pct_all,  height=bar_width,
                             color=color_list_main, alpha=0.9,  edgecolor="white",
                             label="Alle Jahre")
        bars_2025  = ax.barh(y_rev - bar_width / 2, pct_2025, height=bar_width,
                             color=color_list_main, alpha=0.45, edgecolor="white",
                             label="Jahr 2025")

        max_pct = max(pct_all.max(), pct_2025.max(), 1)
        for bar, cv, pv in zip(bars_all, count_all, pct_all):
            if pv > 0:
                ax.text(bar.get_width() + max_pct * 0.015,
                        bar.get_y() + bar.get_height() / 2,
                        f"{int(cv):,} ({pv:.1f}%)",
                        va="center", fontsize=7.5, color="#222222", fontweight="bold")
        for bar, cv, pv in zip(bars_2025, cnt_2025, pct_2025):
            if pv > 0:
                ax.text(bar.get_width() + max_pct * 0.015,
                        bar.get_y() + bar.get_height() / 2,
                        f"{int(cv):,} ({pv:.1f}%)",
                        va="center", fontsize=7.5, color="#555555")

        ax.set_yticks(y_rev)
        ax.set_yticklabels(order)
        ax.set_xlim(0, max_pct * 1.35)
        ax.set_title("Marktanteile: Gesamt vs. 2025", fontweight="bold", pad=8)
        ax.set_xlabel("Anteil an der Stichprobe (%)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="x", linestyle=":", alpha=0.5)

    def draw_pie_or_trend(ax):
        """Plot 2 — Kreisdiagramm (bei year=) oder Jahrestrend (bei trend_years= oder ohne Filter)."""
        # Einzelnes Jahr → Kreisdiagramm
        if year is not None or (trend_years is not None and
                                trend_years[0] == trend_years[1]):
            source   = data_trend[data_trend[col].isin(top_cats)]
            freq_pie = (source[col].value_counts()
                        .reindex(order).fillna(0).reset_index())
            freq_pie.columns = [col, "count"]
            freq_pie["pct"]  = freq_pie["count"] / len(data_trend) * 100
            pie_colors = [category_colors[cat] for cat in freq_pie[col]]
            wedges, _  = ax.pie(
                freq_pie["count"].values, labels=None, colors=pie_colors,
                startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 0.8},
            )
            pie_labels = [f"{c} ({p:.1f}%)" if p > 0 else ""
                          for c, p in zip(freq_pie[col], freq_pie["pct"])]
            ax.legend(wedges, pie_labels,
                      loc="center left", bbox_to_anchor=(1.02, 0.5),
                      fontsize=8, ncol=1)
            current_yr = year if year else trend_years[0]
            ax.set_title(f"Verteilung {current_yr}", fontweight="bold", pad=8)

        # Jahresbereich oder alle Jahre → Trendlinie
        else:
            # Bei trend_years: nur den angegebenen Bereich zeigen
            source = data_trend[data_trend[col].isin(top_cats)]

            if year_col in source.columns and source[year_col].nunique() > 1:
                trend_data = (source.groupby([year_col, col])
                              .size().unstack(fill_value=0))
                trend_pct  = trend_data.div(trend_data.sum(axis=1), axis=0) * 100
                for cat in order:
                    if cat in trend_pct.columns:
                        ax.plot(trend_pct.index, trend_pct[cat], marker="o", ms=4,
                                label=cat, color=category_colors[cat], lw=2)
                title_suffix = (f" ({trend_years[0]}–{trend_years[1]})"
                                if trend_years else "")
                ax.set_title(f"Jahrestrend (Marktanteile %){title_suffix}",
                             fontweight="bold", pad=8)
                ax.set_xlabel("Jahr")
                ax.set_ylabel("Anteil (%)")
                ax.legend(loc="upper left", fontsize=7, ncol=1)
                ax.grid(True, linestyle=":", alpha=0.5)
            else:
                ax.text(0.5, 0.5, "Nicht genügend Jahresdaten",
                        ha="center", va="center", color="gray")

    def draw_boxplot(ax):
        """Plot 3 — Gehaltsverteilung je Kategorie (Boxplot)."""
        if target not in data_base.columns:
            ax.text(0.5, 0.5, f"Target '{target}' nicht gefunden",
                    ha="center", va="center", color="gray")
            return
        box_data = [
            plot_data_filtered.loc[plot_data_filtered[col] == cat, target].dropna().values
            for cat in order
        ]
        bp = ax.boxplot(
            box_data, vert=False, patch_artist=True, widths=0.5,
            flierprops={"marker": ".", "alpha": 0.3, "markersize": 4,
                        "markeredgecolor": "none", "markerfacecolor": "#222222"},
            medianprops={"linewidth": 2.0, "color": "white"},
            whiskerprops={"linewidth": 1.2},
            capprops={"linewidth": 1.2},
            boxprops={"linewidth": 0.8},
        )
        ax.set_yticks(range(1, len(order) + 1))
        ax.set_yticklabels(order)
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(color_list_main[i])
            patch.set_alpha(0.85)
            patch.set_edgecolor("white")
        ax.set_title(f"{target}-Verteilung nach {col}", fontweight="bold", pad=8)
        ax.set_xlabel(f"{target} (USD)")
        ax.get_xaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${int(x/1000)}k" if x > 0 else "0")
        )
        ax.grid(axis="x", linestyle=":", alpha=0.5)

    def draw_median_trend(ax):
        """Plot 4 — Historischer Mediantrend über Jahre."""
        if target not in data_base.columns or year_col not in data_base.columns:
            ax.text(0.5, 0.5, "Nicht genügend historische Daten",
                    ha="center", va="center", color="gray")
            return
        # Bei trend_years: nur den angegebenen Bereich zeigen
        source = data_trend if (year is not None or trend_years is not None) \
                 else data_base
        plot_source = source[source[col].isin(top_cats)]

        stats = (plot_source.groupby([year_col, col])[target]
                 .median().unstack(fill_value=np.nan))
        for cat in order:
            if cat in stats.columns:
                ax.plot(stats.index, stats[cat], marker="o", ms=5,
                        label=cat, color=category_colors[cat], lw=2)
        title_suffix = (f" ({trend_years[0]}–{trend_years[1]})"
                        if trend_years else "")
        ax.set_title(f"Historischer Median ({target}) nach {col}{title_suffix}",
                     fontweight="bold", pad=8)
        ax.set_xlabel("Jahr")
        ax.set_ylabel(f"Median {target} (k USD)")
        ax.get_yaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:.0f}k" if x > 0 else "0")
        )
        ax.legend(loc="upper left", fontsize=7, ncol=1)
        ax.grid(True, linestyle=":", alpha=0.5)

    def draw_heatmap(ax):
        """Plot 5 — Heatmap: Median-Gehalt Kategorie × Jahr."""
        if target not in data_base.columns or year_col not in data_base.columns:
            ax.text(0.5, 0.5, "Nicht genügend Daten", ha="center", va="center")
            return
        pivot = (plot_data_filtered.groupby([col, year_col])[target]
                 .median().unstack(fill_value=np.nan))
        pivot = pivot.reindex(order)
        im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, fontsize=8)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels(order, fontsize=8)
        # Werte in Zellen
        for i in range(len(order)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                if not np.isnan(val):
                    ax.text(j, i, f"${int(val)}k",
                            ha="center", va="center", fontsize=7,
                            color="black" if val < pivot.values.max() * 0.7 else "white")
        plt.colorbar(im, ax=ax, label=f"Median {target} (k USD)", shrink=0.8)
        ax.set_title(f"Heatmap: Median {target} nach {col} × Jahr",
                     fontweight="bold", pad=8)

    def draw_violin(ax):
        """Plot 6 — Violin-Plot: Gehaltsverteilung je Kategorie."""
        if target not in data_base.columns:
            ax.text(0.5, 0.5, f"Target '{target}' nicht gefunden",
                    ha="center", va="center", color="gray")
            return
        # Nur Kategorien mit genug Daten
        valid_cats = [cat for cat in order
                      if len(plot_data_filtered[plot_data_filtered[col] == cat][target].dropna()) >= 10]
        data_violin = [
            plot_data_filtered.loc[plot_data_filtered[col] == cat, target].dropna().values
            for cat in valid_cats
        ]
        parts = ax.violinplot(data_violin, vert=False, showmedians=True,
                              showextrema=False)
        for i, pc in enumerate(parts["bodies"]):
            pc.set_facecolor(category_colors.get(valid_cats[i], "#888888"))
            pc.set_alpha(0.75)
        parts["cmedians"].set_color("white")
        parts["cmedians"].set_linewidth(2)
        ax.set_yticks(range(1, len(valid_cats) + 1))
        ax.set_yticklabels(valid_cats, fontsize=8)
        ax.get_xaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${int(x/1000)}k" if x > 0 else "0")
        )
        ax.set_title(f"Violin: {target}-Verteilung nach {col}",
                     fontweight="bold", pad=8)
        ax.set_xlabel(f"{target} (USD)")
        ax.grid(axis="x", linestyle=":", alpha=0.5)

    def draw_scatter_ci(ax):
        """Plot 7 — Streudiagramm: Median ± IQR über Jahre je Kategorie."""
        if target not in data_base.columns or year_col not in data_base.columns:
            ax.text(0.5, 0.5, "Nicht genügend Daten", ha="center", va="center")
            return
        for cat in order:
            sub = plot_data_filtered[plot_data_filtered[col] == cat]
            stats = sub.groupby(year_col)[target].agg(
                median="median",
                q25=lambda x: x.quantile(0.25),
                q75=lambda x: x.quantile(0.75),
            )
            if len(stats) < 2:
                continue
            ax.plot(stats.index, stats["median"], marker="o", ms=5,
                    label=cat, color=category_colors[cat], lw=2)
            ax.fill_between(stats.index, stats["q25"], stats["q75"],
                            color=category_colors[cat], alpha=0.15)
        ax.set_title(f"Median ± IQR: {target} nach {col} über Jahre",
                     fontweight="bold", pad=8)
        ax.set_xlabel("Jahr")
        ax.set_ylabel(f"{target} (k USD)")
        ax.get_yaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:.0f}k" if x > 0 else "0")
        )
        ax.legend(loc="upper left", fontsize=7, ncol=1)
        ax.grid(True, linestyle=":", alpha=0.5)

    def draw_pie_all(ax):
        """Plot 8 — Kreisdiagramm: Anteil der Daten (mit Jahresfilter wenn angegeben)."""
        # Quelle: gefilterter Zeitraum wenn year= oder trend_years= angegeben
        source      = data_trend if (year is not None or trend_years is not None) \
                      else data_base
        freq        = source[col].value_counts().reindex(order).fillna(0)
        total       = len(source)                    # ← ganzer gefilterter Datensatz
        pct         = (freq / total * 100).values
        counts      = freq.values
        colors      = [category_colors[cat] for cat in order]

        # Sonstige — alles was nicht in top_n ist
        other_count = int(source[~source[col].isin(order)][col].count())
        other_pct   = other_count / total * 100 if total > 0 else 0

        if other_count > 0:
            pie_vals   = np.append(counts, other_count)
            pie_labels = [
                f"{cat}\n{p:.1f}%" for cat, p in zip(order, pct)
            ] + [f"Sonstige ({n_hidden})\n{other_pct:.1f}%"]
            pie_colors = colors + ["#cccccc"]
        else:
            pie_vals   = counts
            pie_labels = [f"{cat}\n{p:.1f}%" for cat, p in zip(order, pct)]
            pie_colors = colors

        wedges, _ = ax.pie(
            pie_vals,
            labels=None,
            colors=pie_colors,
            startangle=90,
            wedgeprops={"edgecolor": "white", "linewidth": 0.8},
        )
        ax.legend(
            wedges, pie_labels,
            loc="center left", bbox_to_anchor=(1.02, 0.5),
            fontsize=8, ncol=1,
        )
        # Titel mit Jahresinfo
        if year is not None:
            period = str(year)
        elif trend_years is not None:
            period = f"{trend_years[0]}–{trend_years[1]}"
        else:
            period = "alle Jahre"
        ax.set_title(
            f"Anteil nach {col} ({period}, N={total:,})",
            fontweight="bold", pad=8,
        )

    def draw_salary_bar_2025(ax):
        """Plot 9 — Balkendiagramm: Mediangehalt 2025 je Kategorie (sortiert)."""
        if target not in data_base.columns:
            ax.text(0.5, 0.5, f"Target '{target}' nicht gefunden",
                    ha="center", va="center", color="gray")
            return

        # 2025-Daten — falls nicht vorhanden, aktuellstes Jahr verwenden
        yr = 2025
        src_2025 = data_base[data_base[year_col] == yr] if year_col in data_base.columns \
                   else data_base
        if len(src_2025) < 10 and year_col in data_base.columns:
            yr = int(data_base[year_col].max())
            src_2025 = data_base[data_base[year_col] == yr]

        src_2025 = src_2025[src_2025[col].isin(top_cats)]

        medians = (src_2025.groupby(col)[target]
                   .agg(median="median", count="count")
                   .reindex(order)
                   .dropna(subset=["median"])
                   .sort_values("median", ascending=True))

        if medians.empty:
            ax.text(0.5, 0.5, f"Keine Daten für {yr}",
                    ha="center", va="center", color="gray")
            return

        # Für vertikale Balken: absteigend sortieren (höchste links)
        medians = medians.sort_values("median", ascending=False)

        bars = ax.bar(
            range(len(medians)),
            medians["median"],
            color=[category_colors.get(cat, "#888888") for cat in medians.index],
            alpha=0.85,
            edgecolor="white",
            width=0.65,
        )

        # Beschriftung: Median über dem Balken
        y_max = medians["median"].max()
        for bar, (cat, row) in zip(bars, medians.iterrows()):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + y_max * 0.01,
                f"${row['median']:.0f}k",
                ha="center", va="bottom", fontsize=8,
                color="#222222", fontweight="bold",
            )
            # Anzahl unter dem Balken
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_max * 0.01,
                f"n={int(row['count']):,}",
                ha="center", va="bottom", fontsize=7, color="#555555",
            )

        # Globaler Median als Referenzlinie
        global_med_2025 = src_2025[target].median()
        ax.axhline(global_med_2025, color="#D62728", lw=1.5,
                   linestyle="--", label=f"Gesamt Median ${global_med_2025:.0f}k")

        ax.set_xticks(range(len(medians)))
        ax.set_xticklabels(medians.index, rotation=30, ha="right", fontsize=8)
        ax.set_ylim(0, y_max * 1.2)
        ax.get_yaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:.0f}k" if x > 0 else "0")
        )
        ax.set_title(f"Mediangehalt {yr} nach {col}",
                     fontweight="bold", pad=8)
        ax.set_ylabel(f"Median {target} (k USD)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", linestyle=":", alpha=0.5)

    # ── Dispatch: Zeichne nur angeforderte Grafiken ───────────────────────
    draw_fn = {
        1: draw_market_share,
        2: draw_pie_or_trend,
        3: draw_boxplot,
        4: draw_median_trend,
        5: draw_heatmap,
        6: draw_violin,
        7: draw_scatter_ci,
        8: draw_pie_all,
        9: draw_salary_bar_2025,
    }

    for ax, plot_num in zip(axes_flat, plot_list):
        draw_fn[plot_num](ax)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"💾 Dashboard gespeichert: {save_path}")
    plt.show()

def eda_numeric(
    df: pd.DataFrame,
    col: str,
    *,
    plots: int | list[int] | None = None,
    target: str = "salary",
    country: Optional[str] = None,
    year_col: str = "year",
    country_col: str = "country",
    figsize_single: tuple = (12, 5),
    figsize_auto: bool = True,
    save_path: Optional[str] = None,
) -> None:
    """
    EDA-Dashboard für numerische Merkmale.

    Verfügbare Grafiken (plots-Parameter):
        1 — Histogramm + KDE — Gesamtverteilung des Merkmals
        2 — Scatter Plot — Merkmal vs. Zielvariable (aktuellstes Jahr) mit Regressionslinie
        3 — Boxplot nach Jahren — Gehaltsverteilung je Jahr
        4 — Historischer Mediantrend über Jahre
        5 — Zielverteilung: Original vs. log1p (nur wenn col == target)
        6 — Zeitliche Markttrends: Medianlohn + Rollenbesetzung nach Jahren

    Parameters
    ----------
    df             : pd.DataFrame      — Eingabe-DataFrame
    col            : str               — Zu analysierendes numerisches Merkmal
    plots          : int | list | None — Grafik-Nr. (1–6), Liste, oder None (alle 1–4)
    target         : str               — Zielvariable (Standard: 'salary')
    country        : str | None        — Filterland (optional)
    year_col       : str               — Name der Jahresspalte
    country_col    : str               — Name der Länderspalte
    figsize_single : tuple             — Größe für einzelne Grafik (Standard: (12, 5))
    figsize_auto   : bool              — Automatische Figurengröße bei mehreren Grafiken
    save_path      : str | None        — Speicherpfad (optional)

    Beispiele
    ---------
    eda_numeric(df, "salary")                          # alle 4 Standard-Grafiken
    eda_numeric(df, "salary", plots=5)                 # nur Zielverteilung
    eda_numeric(df, "salary", plots=[5, 6])            # Zielverteilung + Zeittrends
    eda_numeric(df, "workexp", plots=[1, 2, 3, 4])     # alle Standard-Grafiken
    """
    # ── Normalisierung des plots-Parameters ──────────────────────────────
    ALL_PLOTS = [1, 2, 3, 4]
    if plots is None:
        plot_list = ALL_PLOTS
    elif isinstance(plots, int):
        plot_list = [plots]
    else:
        plot_list = sorted(set(plots))

    invalid = [p for p in plot_list if p not in range(1, 7)]
    if invalid:
        raise ValueError(f"Ungültige Grafik-Nr.: {invalid}. Gültig: 1–6.")

    # ── Farben ────────────────────────────────────────────────────────────
    MAIN_COLOR = "#2C7BB6"
    ACCENT_RED = "#D7191C"
    GREEN_MEAN = "#1A9641"

    # ── Datenaufbereitung ─────────────────────────────────────────────────
    data_base = df.copy()
    if country is not None and country_col in data_base.columns:
        data_base = data_base[data_base[country_col] == country]

    if data_base.empty or col not in data_base.columns:
        print(f"⚠️ DataFrame ist leer oder Spalte '{col}' nicht gefunden.")
        return

    cols_to_clean = [col] + ([target] if target in data_base.columns else [])
    data_base = data_base.dropna(subset=cols_to_clean)

    box_order   = sorted(data_base[year_col].unique()) if year_col in data_base.columns else []
    n_years     = len(box_order)
    base_colors = list(sns.color_palette("tab20", max(20, n_years)).as_hex())
    rng = np.random.default_rng(seed=42)
    rng.shuffle(base_colors)
    year_colors = {yr: base_colors[i % len(base_colors)] for i, yr in enumerate(box_order)}

    # ── Figurengröße und Layout ───────────────────────────────────────────
    n_plots      = len(plot_list)
    DOUBLE_PLOTS = {5, 6}

    if n_plots == 1 and plot_list[0] in DOUBLE_PLOTS:
        # Единственный двойной график → 1×2
        fig, axes_pair = plt.subplots(1, 2, figsize=figsize_single)
        slot_axes = [(axes_pair[0], axes_pair[1])]

    elif n_plots == 1:
        # Единственный одиночный график
        fig, ax_single = plt.subplots(1, 1, figsize=(10, 6))
        slot_axes = [ax_single]

    else:
        # Несколько графиков — вычисляем точное количество строк
        # Каждый двойной занимает строку целиком (2 колонки)
        # Одиночные заполняют строки по 2 в ряд
        ncols        = 2
        single_list  = [p for p in plot_list if p not in DOUBLE_PLOTS]
        double_list  = [p for p in plot_list if p in DOUBLE_PLOTS]
        single_rows  = (len(single_list) + 1) // 2
        double_rows  = len(double_list)
        nrows        = single_rows + double_rows

        if figsize_auto:
            figsize = (ncols * 9, nrows * 5)
        else:
            figsize = (18, nrows * 5)

        fig       = plt.figure(figsize=figsize)
        slot_axes = []
        row_idx   = 0
        col_idx   = 0

        for p in plot_list:
            if p in DOUBLE_PLOTS:
                # Если одиночная ось открыта — закрываем строку
                if col_idx == 1:
                    row_idx += 1
                    col_idx  = 0
                ax_l = fig.add_subplot(nrows, ncols, row_idx * ncols + 1)
                ax_r = fig.add_subplot(nrows, ncols, row_idx * ncols + 2)
                slot_axes.append((ax_l, ax_r))
                row_idx += 1
                col_idx  = 0
            else:
                ax = fig.add_subplot(nrows, ncols, row_idx * ncols + col_idx + 1)
                slot_axes.append(ax)
                col_idx += 1
                if col_idx >= ncols:
                    col_idx  = 0
                    row_idx += 1

    # ── Заголовок фигуры ──────────────────────────────────────────────────
    meta = [f"Feature: {col}"]
    if country: meta.append(country)
    meta_str = "  |  " + "  |  ".join(meta)
    fig.suptitle(f"EDA: {col} vs. {target}{meta_str}",
                 fontsize=14, fontweight="bold", y=1.01)

    # ── Zeichenfunktionen ─────────────────────────────────────────────────

    def draw_histogram(ax):
        """Plot 1 — Histogramm + KDE."""
        sns.histplot(data=data_base, x=col, kde=True, ax=ax,
                     color=MAIN_COLOR, alpha=0.6, edgecolor="white")
        global_median = data_base[col].median()
        global_mean   = data_base[col].mean()
        ax.axvline(global_median, color=ACCENT_RED, lw=1.5, ls="--",
                   label=f"Median: {global_median:,.1f}")
        ax.axvline(global_mean,   color=GREEN_MEAN, lw=1.5, ls=":",
                   label=f"Mean: {global_mean:,.1f}")
        ax.set_title(f"Gesamtverteilung von {col}", fontweight="bold", pad=8)
        ax.set_xlabel(col)
        ax.set_ylabel("Häufigkeit")
        ax.legend(loc="upper right")
        ax.grid(True, linestyle=":", alpha=0.5)

    def draw_scatter(ax):
        """Plot 2 — Scatter Plot vs. Zielvariable."""
        if target not in data_base.columns:
            ax.text(0.5, 0.5, f"Target '{target}' nicht gefunden",
                    ha="center", va="center", color="gray")
            return
        plot_year = int(data_base[year_col].max()) if year_col in data_base.columns else None
        data_yr   = data_base[data_base[year_col] == plot_year] if plot_year else data_base
        if not data_yr.empty and len(data_yr) > 1:
            sns.regplot(
                data=data_yr, x=col, y=target, ax=ax,
                x_jitter=0.25,
                scatter_kws={"color": MAIN_COLOR, "alpha": 0.35, "s": 20},
                line_kws={"color": ACCENT_RED, "lw": 2.5, "label": "Trendlinie"},
                ci=None,
            )
            ax.set_title(f"Fokus {plot_year}: {col} vs. {target}",
                         fontweight="bold", pad=8)
            ax.set_xlabel(col)
            ax.set_ylabel(f"{target} (k USD)")
            ax.get_yaxis().set_major_formatter(
                plt.FuncFormatter(lambda x, _: f"${x:.0f}k" if x > 0 else "0")
            )
            ax.legend(loc="upper left")
        else:
            ax.text(0.5, 0.5, f"Keine Daten für {plot_year}",
                    ha="center", va="center", color="gray")
        ax.grid(True, linestyle=":", alpha=0.5)

    def draw_boxplot_years(ax):
        """Plot 3 — Boxplot nach Jahren."""
        if target not in data_base.columns or not box_order:
            ax.text(0.5, 0.5, "Daten für Jahresvergleich nicht ausreichend",
                    ha="center", va="center", color="gray")
            return
        box_data_yr = [
            data_base.loc[data_base[year_col] == yr, target].dropna().values
            for yr in box_order
        ]
        bp_yr = ax.boxplot(
            box_data_yr, vert=False, patch_artist=True, widths=0.45,
            flierprops={"marker": ".", "alpha": 0.3, "markersize": 4,
                        "markeredgecolor": "none", "markerfacecolor": "#222222"},
            medianprops={"linewidth": 2.0},
            whiskerprops={"linewidth": 1.2},
            capprops={"linewidth": 1.2},
            boxprops={"linewidth": 0.8},
        )
        ax.set_yticks(range(1, len(box_order) + 1))
        ax.set_yticklabels(box_order)
        for i, (patch, wh_pair, cap_pair, med_line) in enumerate(zip(
            bp_yr["boxes"],
            zip(*[iter(bp_yr["whiskers"])] * 2),
            zip(*[iter(bp_yr["caps"])]    * 2),
            bp_yr["medians"],
        )):
            color = year_colors[box_order[i]]
            patch.set_facecolor(color)
            patch.set_alpha(0.85)
            patch.set_edgecolor("white")
            for w in wh_pair: w.set_color(color); w.set_linewidth(1.2)
            for c in cap_pair: c.set_color(color); c.set_linewidth(1.2)
            med_line.set_color("white"); med_line.set_linewidth(2.0)
        ax.set_title(f"{target}-Verteilung nach Jahren", fontweight="bold", pad=8)
        ax.set_xlabel(f"{target} (k USD)")
        ax.set_ylabel("Jahr")
        ax.get_xaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:.0f}k" if x > 0 else "0")
        )
        ax.grid(True, linestyle=":", alpha=0.5)

    def draw_median_trend(ax):
        """Plot 4 — Historischer Mediantrend über Jahre."""
        if year_col not in data_base.columns or data_base[year_col].nunique() < 2:
            ax.text(0.5, 0.5, "Nicht genügend historische Daten",
                    ha="center", va="center", color="gray")
            return
        stats_by_year = data_base.groupby(year_col)[col].median().reset_index()
        ax.plot(stats_by_year[year_col], stats_by_year[col],
                marker="o", ms=6, color=MAIN_COLOR, lw=2.5,
                label=f"Median {col}")
        for _, row in stats_by_year.iterrows():
            ax.text(row[year_col],
                    row[col] + stats_by_year[col].max() * 0.015,
                    f"{row[col]:,.1f}", ha="center", va="bottom",
                    fontsize=9, fontweight="bold")
        ax.set_xticks(sorted(stats_by_year[year_col].unique()))
        ax.set_ylim(0, stats_by_year[col].max() * 1.2)
        ax.set_title(f"Historischer Trend (Median von {col})",
                     fontweight="bold", pad=8)
        ax.set_xlabel("Jahr")
        ax.set_ylabel(f"Median {col}")
        ax.legend(loc="upper left")
        ax.grid(True, linestyle=":", alpha=0.5)

    def draw_target_distribution(ax_l, ax_r):
        """Plot 5 — Zielverteilung: Original vs. log1p."""
        sal = data_base[target].dropna()
        fig.suptitle(
            f"Lohnverteilung: Ursprüngliche Skala vs. Logarithmische Skala",
            fontsize=14, fontweight="bold", y=1.01,
        )

        # Linkes Teilbild: Originalskala
        ax_l.hist(sal, bins=70, color=MAIN_COLOR, edgecolor="white", linewidth=0.4)
        ax_l.axvline(sal.median(), color=ACCENT_RED, lw=2, ls="--",
                     label=f"Median: ${sal.median():.1f}k")
        ax_l.axvline(sal.mean(),   color=GREEN_MEAN, lw=2, ls="--",
                     label=f"Mittelwert: ${sal.mean():.1f}k")
        ax_l.set_xlabel(f"{target} (k USD)")
        ax_l.set_ylabel("Häufigkeit")
        ax_l.set_title("Verteilung (Originalskala)", fontweight="bold", pad=8)
        ax_l.legend()
        ax_l.grid(True, linestyle=":", alpha=0.5)

        # Rechtes Teilbild: log1p-Skala
        log_sal = np.log1p(sal)
        ax_r.hist(log_sal, bins=70, color=GREEN_MEAN, edgecolor="white", linewidth=0.4)
        ax_r.axvline(log_sal.median(), color=ACCENT_RED, lw=2, ls="--",
                     label=f"Median: {log_sal.median():.2f}")
        ax_r.axvline(log_sal.mean(),   color=MAIN_COLOR, lw=2, ls=":",
                     label=f"Mittelwert: {log_sal.mean():.2f}")
        ax_r.set_xlabel(f"log1p({target})")
        ax_r.set_ylabel("Häufigkeit")
        ax_r.set_title("Logarithmische Verteilung (log1p)", fontweight="bold", pad=8)
        ax_r.legend()
        ax_r.grid(True, linestyle=":", alpha=0.5)

    def draw_market_trends(ax_l, ax_r):
        """Plot 6 — Zeitliche Markttrends: Medianlohn + Rollenbesetzung."""
        if year_col not in data_base.columns:
            ax_l.text(0.5, 0.5, "Keine Jahresdaten", ha="center", va="center")
            ax_r.text(0.5, 0.5, "Keine Jahresdaten", ha="center", va="center")
            return

        # ── Linkes Teilbild: Medianlohn-Entwicklung ───────────────────────
        yearly = (data_base.groupby(year_col)[target]
                  .median().reset_index())
        ax_l.plot(yearly[year_col], yearly[target],
                  marker="o", color=MAIN_COLOR, lw=2.5, ms=8,
                  label=f"Median {target} (k USD)")
        for _, row in yearly.iterrows():
            ax_l.annotate(
                f"${row[target]:.1f}k",
                (row[year_col], row[target]),
                textcoords="offset points", xytext=(0, 12),
                ha="center", fontsize=9, fontweight="bold",
            )
        ax_l.set_title("Entwicklung des Medianlohns", fontweight="bold", pad=8)
        ax_l.set_xlabel("Jahr")
        ax_l.set_ylabel(f"Median {target} (k USD)")
        ax_l.get_yaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:.0f}k" if x > 0 else "0")
        )
        ax_l.set_xticks(sorted(yearly[year_col].unique()))
        ax_l.grid(True, linestyle="--", alpha=0.5)
        ax_l.legend()

        # ── Rechtes Teilbild: Rollenbesetzung nach Jahren ─────────────────
        # Suche nach bester Rollenspalte
        role_col = next(
            (c for c in ["primary_role", "devtype_data", "devtype"] if c in data_base.columns),
            None,
        )
        if role_col is None:
            ax_r.text(0.5, 0.5, "Keine Rollenspalte gefunden",
                      ha="center", va="center", color="gray")
            return

        df_exploded = data_base.copy()
        df_exploded[role_col] = df_exploded[role_col].astype(str).str.split(";")
        df_exploded = df_exploded.explode(role_col)
        df_exploded[role_col] = df_exploded[role_col].str.strip()
        df_exploded = df_exploded[
            df_exploded[role_col].notna() &
            ~df_exploded[role_col].isin(["", "nan", "None", "Unknown"])
        ]

        top_roles = df_exploded[role_col].value_counts().head(8).index.tolist()
        roles_by_year = (
            df_exploded[df_exploded[role_col].isin(top_roles)]
            .groupby([year_col, role_col])[target]
            .count().unstack(fill_value=0)
        )
        tab20 = list(sns.color_palette("tab20", 20).as_hex())
        role_colors = {r: tab20[i % 20] for i, r in enumerate(top_roles)}

        roles_by_year.plot(
            kind="bar", ax=ax_r,
            color=[role_colors.get(c, "#888888") for c in roles_by_year.columns],
            edgecolor="white", linewidth=0.5, width=0.8,
        )
        ax_r.set_title("Dynamik der Befragten nach Rollen", fontweight="bold", pad=8)
        ax_r.set_xlabel("Jahr")
        ax_r.set_ylabel("Anzahl der Befragten")
        ax_r.tick_params(axis="x", rotation=0)
        ax_r.grid(True, axis="y", linestyle="--", alpha=0.5)
        ax_r.legend(title=role_col, bbox_to_anchor=(1.05, 1),
                    loc="upper left", fontsize=7)

    # ── Dispatch ──────────────────────────────────────────────────────────
    SINGLE_FN = {
        1: draw_histogram,
        2: draw_scatter,
        3: draw_boxplot_years,
        4: draw_median_trend,
    }
    DOUBLE_FN = {
        5: draw_target_distribution,
        6: draw_market_trends,
    }

    for slot, p in zip(slot_axes, plot_list):
        if p in DOUBLE_FN:
            DOUBLE_FN[p](slot[0], slot[1])
        else:
            SINGLE_FN[p](slot)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"💾 Dashboard gespeichert: {save_path}")
    plt.show()


def eda_numeric_bins(
    df: pd.DataFrame,
    col: str,
    *,
    bins: list[int] | None = None,
    target: str = "salary",
    year_col: str = "year",
    target_year: int = 2025,
    figsize: tuple = (10, 5),
    color_counts: str = "#AEC7E8",
    color_median: str = "#2E86C1",
    color_ref: str = "#D62728",
    save_path: str | None = None,
) -> None:
    """
    Zwei vertikale Balkendiagramme für numerische Merkmale mit Bin-Gruppierung.

    Links  — Anzahl der Befragten je Bin (alle Jahre)
    Rechts — Medianlohn je Bin (nur Zieljahr, Standard: 2025)

    Parameters
    ----------
    df           : pd.DataFrame  — Eingabe-DataFrame
    col          : str           — Zu analysierendes numerisches Merkmal
    bins         : list | None   — Bin-Grenzen, z. B. [0, 1, 3, 6, 10, 20, 50]
                                   None → automatische Bins (10 gleichbreite)
    target       : str           — Zielvariable (Standard: 'salary')
    year_col     : str           — Name der Jahresspalte
    target_year  : int           — Jahr für Median-Grafik (Standard: 2025)
    figsize      : tuple         — Abbildungsgröße (Standard: (14, 5))
    color_counts : str           — Farbe für Anzahl-Balken (pастельный синий)
    color_median : str           — Farbe für Median-Balken (насыщенный синий)
    color_ref    : str           — Farbe für Referenzlinie (rot)
    save_path    : str | None    — Speicherpfad (optional)

    Beispiele
    ---------
    eda_numeric_bins(df, "workexp",
                     bins=[0, 1, 3, 6, 10, 15, 20, 30, 50])
    eda_numeric_bins(df, "yearscode",
                     bins=[0, 1, 3, 6, 10, 15, 20, 30, 50])
    eda_numeric_bins(df, "yearscodepro",
                     bins=[0, 1, 3, 6, 10, 15, 20, 50])
    eda_numeric_bins(df, "role_count",
                     bins=[1, 2, 3, 4, 5, 10])
    """
    data = df[[col, target] + ([year_col] if year_col in df.columns else [])].dropna()

    if data.empty:
        print(f"⚠️ Keine Daten für '{col}'.")
        return

    # ── Bins bestimmen ────────────────────────────────────────────────────
    if bins is None:
        bins = list(range(int(data[col].min()),
                          int(data[col].max()) + 2,
                          max(1, int((data[col].max() - data[col].min()) / 10))))

    bin_labels = [f"{bins[i]}–{bins[i+1]-1}" for i in range(len(bins) - 1)]
    # Letztes Bin offen: z.B. "20+"
    bin_labels[-1] = f"{bins[-2]}+"

    data["_bin"] = pd.cut(
        data[col],
        bins=bins,
        labels=bin_labels,
        right=False,
        include_lowest=True)

    # ── Aggregation ───────────────────────────────────────────────────────
    counts  = data.groupby("_bin", observed=True).size()

    if year_col in data.columns:
        data_yr = data[data[year_col] == target_year]
        # Fallback auf letztes verfügbares Jahr
        if len(data_yr) < 10:
            target_year = int(data[year_col].max())
            data_yr = data[data[year_col] == target_year]
    else:
        data_yr = data

    medians = data_yr.groupby("_bin", observed=True)[target].median()

    # ── Figur ─────────────────────────────────────────────────────────────
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=figsize)
    fig.suptitle(
        f"Verteilung nach {col}: Anzahl & Mediangehalt {target_year}",
        fontsize=13, fontweight="bold", y=1.02,
    )

    x      = range(len(bin_labels))
    x_ticks = list(x)

    # ── Links: Anzahl ─────────────────────────────────────────────────────
    bars_l = ax_l.bar(x, counts.reindex(bin_labels).fillna(0),
                      color=color_counts, edgecolor="white",
                      linewidth=0.6, width=0.7)

    for bar in bars_l:
        h = bar.get_height()
        if h > 0:
            ax_l.text(bar.get_x() + bar.get_width() / 2,
                      h + counts.max() * 0.01,
                      f"{int(h):,}",
                      ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax_l.set_xticks(x_ticks)
    ax_l.set_xticklabels(bin_labels, rotation=30, ha="right", fontsize=9)
    ax_l.set_title(f"Anzahl Befragter nach {col}", fontweight="bold", pad=8)
    ax_l.set_xlabel(f"{col} (Jahre)")
    ax_l.set_ylabel("Anzahl")
    ax_l.set_ylim(0, counts.max() * 1.15)
    ax_l.grid(axis="y", linestyle=":", alpha=0.5)

    # ── Rechts: Medianlohn ────────────────────────────────────────────────
    med_vals = medians.reindex(bin_labels)
    bars_r   = ax_r.bar(x, med_vals.fillna(0),
                        color=color_median, edgecolor="white",
                        linewidth=0.6, width=0.7, alpha=0.85)

    for bar, val in zip(bars_r, med_vals):
        if pd.notna(val) and val > 0:
            ax_r.text(bar.get_x() + bar.get_width() / 2,
                      val + med_vals.max() * 0.01,
                      f"${val:.0f}k",
                      ha="center", va="bottom", fontsize=8, fontweight="bold",
                      color="#1A2F3F")

    # Referenzlinie: globaler Median für target_year
    global_med = data_yr[target].median()
    ax_r.axhline(global_med, color=color_ref, lw=1.5, ls="--",
                 label=f"Gesamt Median ${global_med:.0f}k")

    ax_r.set_xticks(x_ticks)
    ax_r.set_xticklabels(bin_labels, rotation=30, ha="right", fontsize=9)
    ax_r.set_title(f"Medianlohn {target_year} nach {col}", fontweight="bold", pad=8)
    ax_r.set_xlabel(f"{col} (Jahre)")
    ax_r.set_ylabel(f"Median {target} (k USD)")
    ax_r.get_yaxis().set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:.0f}k" if x > 0 else "0")
    )
    ax_r.set_ylim(0, med_vals.max() * 1.2 if med_vals.max() > 0 else 1)
    ax_r.legend(loc="upper left", fontsize=8)
    ax_r.grid(axis="y", linestyle=":", alpha=0.5)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"💾 Gespeichert: {save_path}")
    plt.show()


def plot_salary_choropleth_map(
    df: pd.DataFrame,
    country_col: str = "country",
    salary_col: str = "salary",
    save_html_path: Optional[str] = None,
) -> None:
    """
    Erstellt eine interaktive Choropleth-Karte (Heatmap) der weltweiten Gehaltsverteilung.
    Farbintensität = Medianlohn je Land (USD).
    Wird als HTML-Datei gespeichert und im Browser geöffnet.
    """
    geo_data = df.groupby(country_col).agg(
        median_salary=(salary_col, "median"),
        count=(salary_col, "count"),
    ).reset_index()

    fig = px.choropleth(
        geo_data,
        locations=country_col,
        locationmode="country names",
        color="median_salary",
        hover_name=country_col,
        hover_data={
            "median_salary": ":,.0f",
            "count": ":,d",
            country_col: False,
        },
        labels={"median_salary": "Medianlohn", "count": "Anzahl Befragter"},
        color_continuous_scale=px.colors.sequential.Blues,
        title="<b>Globale Gehalts-Heatmap</b>",
    )
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True,
                 projection_type="equirectangular"),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    fig.update_coloraxes(
        colorbar_title=dict(text="Gehalt (USD)", font=dict(size=11)),
        colorbar_tickprefix="$",
    )
    html_file = save_html_path or "temp_salary_map.html"
    fig.write_html(html_file)
    print(f"💾 Choropleth-Karte gespeichert: {html_file}")
    webbrowser.open(f"file:///{os.path.abspath(html_file)}")


# ════════════════════════════════════════════════════════════════════════════
# 6. MODELLIERUNG & EVALUATION
# ════════════════════════════════════════════════════════════════════════════

def data_split(df: pd.DataFrame):
    """
    Teilt den DataFrame zeitbasiert in Trainings- und Testmengen auf.
    Trainingsmenge: Jahre ≤ 2024. Testmenge: Jahre ≥ 2025.
    Gibt (features_train, features_test, target_train, target_test) zurück.
    """
    features_train = df[df["year"] <= 2024].drop("salary", axis=1)
    features_test  = df[df["year"] >= 2025].drop("salary", axis=1)
    target_train   = df[df["year"] <= 2024]["salary"]
    target_test    = df[df["year"] >= 2025]["salary"]
    return features_train, features_test, target_train, target_test


def result(
    results_df: pd.DataFrame,
    model_name: str,
    y_true,
    y_pred,
) -> pd.DataFrame:
    """
    Berechnet MAE, RMSE und R² und fügt die Ergebnisse der Vergleichstabelle hinzu.
    Überschreibt eine bestehende Zeile, falls der Modellname bereits vorhanden ist.

    Parameters
    ----------
    results_df : pd.DataFrame — Bestehende Ergebnistabelle
    model_name : str          — Name des Modells (Zeilenindex)
    y_true     : array-like   — Wahre Zielwerte
    y_pred     : array-like   — Vorhergesagte Werte

    Returns
    -------
    pd.DataFrame mit aktualisierter Ergebnistabelle
    """
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    results_df.loc[model_name] = [mae, rmse, r2]
    return results_df


def generate_skill_meta(feature_names) -> dict:
    """
    Erstellt ein Metadaten-Wörterbuch für alle Merkmale nach dem Preprocessor.

    Namensformat des Preprocessors:
        "multi_language__Python"  → level="multi_language", skill="Python"
        "cat__education"          → level="cat",            skill="education"
        "num__work_exp"           → level="num",            skill="work_exp"

    Returns
    -------
    dict: {feature_name: {"level": str, "skill": str}}
    """
    skill_meta = {}
    for col in feature_names:
        if "__" in col:
            prefix, skill = col.split("__", maxsplit=1)
        else:
            prefix, skill = col, col
        skill_meta[col] = {"level": prefix, "skill": skill}
    return skill_meta


# ════════════════════════════════════════════════════════════════════════════
# 7. SHAP — INTERPRETIERBARKEIT
# ════════════════════════════════════════════════════════════════════════════

def shap_log_to_usd_skill(
    feat: str,
    shap_df: pd.DataFrame,
    median_salary: float,
    source_features: Optional[pd.DataFrame] = None,
    min_rows: int = 10,
) -> float:
    """
    Berechnet den durchschnittlichen Gehaltseinfluss eines Skills in USD
    auf Basis der SHAP-Werte — nur für Zeilen, in denen der Skill tatsächlich
    in den Ursprungsdaten vorhanden ist.

    Hintergrund: TreeExplainer liefert für ALLE Zeilen Nicht-Null-SHAP-Werte,
    auch wenn der Skill fehlt. Daher wird nach source_features gefiltert
    und nicht nach shap_df[feat] != 0.

    Parameters
    ----------
    feat            : str           — Feature-Name, z. B. "multi_language__Python"
    shap_df         : pd.DataFrame  — SHAP-Werte (Zeilen = Samples, Spalten = Features)
    median_salary   : float         — Globaler oder kontextueller Median in Tausend USD
    source_features : pd.DataFrame  — Originaldaten vor dem Preprocessor (für Filterung)
    min_rows        : int           — Mindestanzahl Zeilen mit dem Skill (0 = kein Filter)

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


# ════════════════════════════════════════════════════════════════════════════
# Schnelltest (python utils.py)
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_cases = [
        "Data or business analyst",
        "Data scientist or machine learning specialist;Developer, back-end",
        "Data or business analyst;Engineer, data;Developer, full-stack;DevOps specialist",
        "Academic researcher;Data scientist or machine learning specialist;Developer, QA or test;Engineering manager",
        "Database administrator;Designer;Developer, back-end;Developer, front-end;Developer, full-stack;System administrator",
    ]

    print(f"{'String':<70} {'data_roles':<40} {'other_roles':<50} {'count_d':>7} {'count_dev':>9} {'purity':>7}")
    print("-" * 190)
    for t in test_cases:
        short  = (t[:67] + "...") if len(t) > 70 else t
        dr     = extract_data_roles_str(t)
        oroles = extract_other_roles_str(t)
        counts = compute_role_counts_by_category(t)
        purity = compute_data_role_purity(t)
        print(
            f"{short:<70} {dr:<40} {oroles:<50} "
            f"{counts['count_data']:>7} {counts['count_developer']:>9} {purity:>7.0%}"
        )
