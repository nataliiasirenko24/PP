# ════════════════════════════════════════════════════════════════════════════
# advisor.py — DataCareerAdvisor
#
# Abhängigkeiten: config_mappings.py, utils.py
#
# Abschnitte:
#   1. Importe
#   2. Klasse DataCareerAdvisor
#      2.1  __init__          — Initialisierung & Skill-Precomputation
#      2.2  Hilfsmethoden     — _fix_input, _normalize_role, _get_role_group
#      2.3  available_*       — Listet verfügbare Profilwerte auf
#      2.4  Kernmethoden      — Vorhersage, Empfehlungen, Berichte
# ════════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════════
# 1. IMPORTE
# ════════════════════════════════════════════════════════════════════════════

import numpy as np
import pandas as pd
import config_mappings as cfg
from utils import shap_log_to_usd_skill


# ════════════════════════════════════════════════════════════════════════════
# 2. KLASSE DataCareerAdvisor
# ════════════════════════════════════════════════════════════════════════════

class DataCareerAdvisor:
    """
    Personalisiertes Gehaltsvorhersage- und Skill-Empfehlungssystem
    für IT & Data-Spezialisten auf Basis des Stack Overflow Developer Survey.

    Unterstützte Rollengruppen:
        Data      — Data Scientist, Data Engineer, Analyst, AI/ML Engineer …
        Developer — back-end, full-stack, front-end, mobile, AI …
        DevOps    — DevOps, Cloud, SRE, System Administrator …
        Manager   — Engineering Manager, Product Manager, VP …
        Security  — InfoSec, Security professional …
        Designer  — UX, UI, Designer …

    Workflow:
        1. Nutzerprofil übergeben (Rolle, Land, Skills, Erfahrung, …)
        2. predict_salary()            → erwartetes Jahresgehalt in USD
        3. recommend_skills_to_learn() → Top-N Skills mit Gehaltseffekt
        4. recommend_country()         → Top-N Länder nach Mediangehalt
        5. full_report()               → vollständiger Gehaltsreport
        6. diagnose()                  → Profildiagnose für Debugging
    """

    # ── 2.1 Initialisierung ───────────────────────────────────────────────

    def __init__(
        self,
        df: pd.DataFrame,
        skill_meta: dict,
        pipeline,
        shap_df: pd.DataFrame,
        median_salary_global: float,
        num_cols: list,
        cat_cols: list,
        source_features: pd.DataFrame = None,
    ):
        """
        Parameters
        ----------
        df                   : pd.DataFrame    — Vollständiger Datensatz nach features_engineering
        skill_meta           : dict            — Feature-Metadaten aus generate_skill_meta()
        pipeline             : sklearn Pipeline — Trainierte Pipeline (preprocessor + regressor)
        shap_df              : pd.DataFrame    — SHAP-Werte für Skill-Empfehlungen
        median_salary_global : float           — Globaler Gehaltsmedian in Tausend USD
        num_cols             : list            — Numerische Modellspalten
        cat_cols             : list            — Kategoriale Modellspalten
        source_features      : pd.DataFrame   — Originaldaten vor dem Preprocessor (für SHAP-Filter)
        """
        self.df                   = df.copy()
        self.skill_meta           = skill_meta
        self.pipeline             = pipeline
        self.shap_df              = shap_df
        self.median_salary_global = median_salary_global
        self.num_cols             = num_cols
        self.cat_cols             = cat_cols
        self.source_features      = source_features

        # Vorberechnung des Gehaltseffekts je Skill (globaler Median als Basis)
        self.skill_price = {}
        for feat, meta in skill_meta.items():
            if not meta["level"].startswith("multi_"):
                continue
            if feat not in shap_df.columns:
                continue
            usd = shap_log_to_usd_skill(
                feat, shap_df, median_salary_global,
                source_features=self.source_features,
            )
            self.skill_price[meta["skill"]] = usd

    # ── 2.2 Hilfsmethoden ────────────────────────────────────────────────

    @staticmethod
    def _fix_input(s: str) -> str:
        """Bereinigt Eingabe-Strings: entfernt führende und nachfolgende Leerzeichen."""
        return str(s).strip()

    def _normalize_role(self, role: str) -> str:
        """
        Übersetzt einen SO-Survey-Rollennamen in den internen Anzeigenamen
        aus cfg.role_name_mapping. Unbekannte Rollen werden unverändert zurückgegeben.
        """
        return cfg.role_name_mapping.get(role, role)

    def _get_role_group(self, role: str) -> str:
        """
        Gibt die Rollengruppe aus cfg.role_category_mapping zurück.
        Sucht zuerst nach dem Original-Namen, dann nach dem normalisierten Namen.
        Fallback: 'Other'.
        """
        group = cfg.role_category_mapping.get(role)
        if group:
            return group
        return cfg.role_category_mapping.get(self._normalize_role(role), "Other")

    def _get_allowed_skills(self, role: str) -> set:
        """
        Gibt die Skill-Whitelist für eine Rolle zurück.
        Sucht zuerst nach dem normalisierten Namen, dann nach dem Originalnamen,
        zuletzt alle bekannten Skills als Fallback.

        Parameters
        ----------
        role : str — Rollenname

        Returns
        -------
        set — Menge erlaubter Skills (lowercase)
        """
        role_normalized = self._normalize_role(role)

        if role_normalized in cfg.data_role_skills:
            return {s.lower() for s in cfg.data_role_skills[role_normalized]}

        if role in cfg.data_role_skills:
            return {s.lower() for s in cfg.data_role_skills[role]}

        return {s.lower() for s in cfg.all_data_skills}

    def _get_sample_weight(self, country: str, primary_role: str) -> float:
        """
        Berechnet sample_weight für ein Profil analog zur Trainingslogik:
        1 / log1p(Anzahl Zeilen für diese Land+Rolle-Kombination).

        Verhindert sample_weight=0 beim Advisor-Aufruf, da das Modell
        diesen Wert beim Training nie gesehen hat.

        Parameters
        ----------
        country      : str — Ländername (normalisiert)
        primary_role : str — Normalisierter Rollenname

        Returns
        -------
        float — sample_weight > 0
        """
        role_col = "primary_role" if "primary_role" in self.df.columns else "devtype"
        combo_mask = (
            (self.df["country"] == country) &
            (self.df[role_col] == primary_role)
        )
        combo_count = int(combo_mask.sum())
        # Fallback auf globale Zeilenzahl wenn Kombination nicht gefunden
        if combo_count == 0:
            combo_count = max(1, len(self.df[self.df[role_col] == primary_role]))
        return float(1.0 / np.log1p(combo_count))

    # ── 2.3 available_* — Verfügbare Profilwerte ausgeben ────────────────

    def available_roles(self) -> None:
        """
        Gibt alle verfügbaren Rollen aus dem Datensatz aus,
        gruppiert nach Rollengruppe. Zeigt originale SO-Survey-Namen
        zur direkten Verwendung in profile['role'].
        """
        print("Verfügbare Rollen (in profile['role'] eingeben):\n")

        role_col = "primary_role" if "primary_role" in self.df.columns else "devtype"
        role_counts = self.df[role_col].value_counts()

        # Obratny mapping: normalisierter Name → Original SO-Survey-Name
        norm_to_original = {v: k for k, v in cfg.role_name_mapping.items()}

        group_order = [
            "Data", "Developer Software Engineering", "Developer AI",
            "Developer Platform & Infrastructure", "Developer Hardware & Systems",
            "Developer Community & Specialized", "DevOps & SRE",
            "Management", "Research", "Security", "Designer", "Student", "Other",
        ]

        printed = set()
        for group in group_order:
            group_roles = []
            for norm_role in role_counts.index:
                if norm_role in printed or norm_role in ("None", "Unknown", ""):
                    continue
                original = norm_to_original.get(norm_role, norm_role)
                role_group = cfg.role_category_mapping.get(
                    original,
                    cfg.role_category_mapping.get(norm_role, "Other")
                )
                if role_group == group:
                    group_roles.append((norm_role, original))

            if not group_roles:
                continue
            print(f"  ── {group} ──")
            for norm_role, original in group_roles:
                print(f"    {original}  ({role_counts[norm_role]:,})")
                printed.add(norm_role)
        print()

    def available_countries(self) -> None:
        """Gibt alle im Datensatz vorhandenen Länder aus."""
        print("Verfügbare Länder (in profile['country'] eingeben):\n")
        for val in self.df["country"].dropna().value_counts().index:
            print(f"  {val}")

    def available_education(self) -> None:
        """Gibt alle verfügbaren Bildungsabschlüsse aus dem Datensatz aus."""
        print("Verfügbare Bildungsabschlüsse (in profile['education'] eingeben):\n")
        for val in self.df["education"].dropna().value_counts().index:
            print(f"  {val}")

    def available_remote(self) -> None:
        """Gibt alle verfügbaren Arbeitsformate (Remote, Hybrid, On-site) aus."""
        print("Verfügbare Arbeitsformate (in profile['remote'] eingeben):\n")
        for val in self.df["remote"].dropna().value_counts().index:
            print(f"  {val}")

    def available_org_sizes(self) -> None:
        """Gibt alle verfügbaren Unternehmensgrößen aus dem Datensatz aus."""
        print("Verfügbare Unternehmensgrößen (in profile['orgsize'] eingeben):\n")
        for val in self.df["orgsize"].dropna().value_counts().index:
            print(f"  {val}")

    def available_industries(self) -> None:
        """Gibt alle verfügbaren Branchen aus dem Datensatz aus."""
        print("Verfügbare Branchen (in profile['industry'] eingeben):\n")
        for val in self.df["industry"].dropna().value_counts().index:
            print(f"  {val}")

    def available_icorpm(self) -> None:
        """Gibt die verfügbaren IC/Manager-Kategorien aus."""
        print("Verfügbare icorpm-Werte (in profile['icorpm'] eingeben):\n")
        for val in self.df["icorpm"].dropna().value_counts().index:
            print(f"  {val}")

    def available_ages(self) -> None:
        """Gibt alle verfügbaren Altersgruppen aus dem Datensatz aus."""
        print("Verfügbare Altersgruppen (in profile['age'] eingeben):\n")
        for val in self.df["age"].dropna().value_counts().index:
            print(f"  {val}")

    def available_skills(self, role: str = None) -> None:
        """
        Gibt die Skill-Whitelist für eine bestimmte Rolle aus.
        Ohne Rollenangabe werden alle bekannten Skills angezeigt.

        Parameters
        ----------
        role : str | None — Rollenname
        """
        if role:
            skills = self._get_allowed_skills(role)
            label  = f"'{self._normalize_role(role)}'"
        else:
            skills = {s.lower() for s in cfg.all_data_skills}
            label  = "alle Rollen"
        print(f"Skills für {label}:\n")
        for skill in sorted(skills):
            print(f"  {skill}")

    # ── 2.4 Kernmethoden ─────────────────────────────────────────────────

    def get_context_median(self, country: str, role: str) -> float:
        """
        Gibt den Gehaltsmedian in Tausend USD für eine Land-Rollen-Kombination zurück.

        Fallback-Kaskade:
            1. Median für Land + primary_role  (min. 30 Zeilen)
            2. Median für Land + role (string-Suche) (min. 30 Zeilen)
            3. Median für Land gesamt          (min. 30 Zeilen)
            4. Globaler Median

        Parameters
        ----------
        country : str — Ländername (wie in df["country"])
        role    : str — Rollenname

        Returns
        -------
        float — Median in Tausend USD
        """
        df       = self.df
        primary  = self._normalize_role(role)
        role_col = "primary_role" if "primary_role" in df.columns else "devtype"

        for mask in [
            (df["country"] == country) & (df[role_col] == primary),
            (df["country"] == country) & (df[role_col].str.contains(role, regex=False, na=False)),
            (df["country"] == country),
        ]:
            sub = df.loc[mask, "salary"].dropna()
            if len(sub) >= 30:
                return float(sub.median())
        return float(self.median_salary_global)

    def _build_profile_row(self, profile: dict) -> pd.DataFrame:
        """
        Konvertiert ein Nutzerprofil-Dictionary in eine einzelne DataFrame-Zeile,
        die direkt in die sklearn-Pipeline übergeben werden kann.

        Verarbeitung:
            1. Mapping aller Eingabewerte über cfg.*_mapping
            2. Ländernormalisierung
            3. Berechnung der Target-Encoding-Mediane (Land, Rolle, Region)
            4. Berechnung von sample_weight analog zur Trainingslogik
            5. Zuordnung der Rolle zur devtype-Spalte
            6. Zuordnung der Skills zu den Multi-Spalten

        Parameters
        ----------
        profile : dict — Nutzerprofil

        Returns
        -------
        pd.DataFrame — Einzelzeile mit allen Modellspalten
        """
        country      = profile.get("country", "Germany")
        role         = profile.get("role", "Data or business analyst")
        years_exp    = int(profile.get("years_experience", 3))
        year_profile = int(profile.get("year", 2025))
        age          = profile.get("age", "25-34 years old")

        # ── Bildung & Unternehmensgröße → Mapping + Rang ─────────────────
        edu_raw  = self._fix_input(profile.get("education",
                   "Bachelor's degree (B.A., B.S., B.Eng., etc.)"))
        edu_can  = cfg.education_mapping.get(edu_raw, edu_raw)
        edu_rank = cfg.education_rank_mapping.get(edu_can, 0)

        org_raw  = self._fix_input(profile.get("orgsize", "Large 1 (1-5k)"))
        org_can  = cfg.orgsize_mapping.get(org_raw, org_raw)
        org_rank = cfg.orgsize_rank_mapping.get(org_can, 0)

        # ── Sonstige kategoriale Felder ───────────────────────────────────
        remote_can   = cfg.remote_mapping.get(
                        self._fix_input(profile.get("remote", "Hybrid")), "Hybrid")
        industry_can = cfg.industry_mapping.get(
                        self._fix_input(profile.get("industry",
                        "IT, Telecom & Tech")), "IT, Telecom & Tech")
        icorpm_can   = cfg.icorpm_mapping.get(
                        self._fix_input(profile.get("icorpm", "IC")), "IC")

        # ── Ländernormalisierung ──────────────────────────────────────────
        country_can = country
        if country_can == "United States of America":
            country_can = "United States"
        elif country_can == "United Kingdom of Great Britain and Northern Ireland":
            country_can = "Great Britain"
        country_can = cfg.country_mapping.get(country_can, country_can)

        # Währung: häufigste Währung des Landes aus dem Datensatz
        currency_mask = self.df["country"] == country_can
        currency_can  = (
            self.df.loc[currency_mask, "currency"].mode()[0]
            if currency_mask.sum() > 0 else "USD US Dollar"
        )

        region       = cfg.region_mapping.get(country, "Other")
        primary_role = self._normalize_role(role)
        role_col     = "primary_role" if "primary_role" in self.df.columns else "devtype"

        # ── Target Encoding — Mediane als Features ────────────────────────
        def _safe_median(mask, fallback: float) -> float:
            """Gibt Median zurück, falls mind. 10 Zeilen vorhanden, sonst Fallback."""
            sub = self.df.loc[mask, "salary"].dropna()
            return float(sub.median()) if len(sub) >= 10 else fallback

        global_med = float(self.median_salary_global)

        country_med      = _safe_median(
            self.df["country"] == country_can, global_med)
        country_role_med = _safe_median(
            (self.df["country"] == country_can) &
            (self.df[role_col] == primary_role),
            country_med,
        )
        region_med       = _safe_median(
            self.df["country_region"] == region, global_med)
        region_role_med  = _safe_median(
            (self.df["country_region"] == region) &
            (self.df[role_col] == primary_role),
            region_med,
        )

        # Rollen-Encoding (global, länderunabhängig)
        role_med = _safe_median(
            self.df[role_col] == primary_role, global_med)
        role_p75 = float(
            self.df.loc[self.df[role_col] == primary_role, "salary"].quantile(0.75)
        ) if (self.df[role_col] == primary_role).sum() >= 10 else global_med

        # ── Erfahrungsjahre ───────────────────────────────────────────────
        years_code  = years_exp + 2
        hobby_years = max(0, years_code - years_exp)

        # ── sample_weight analog zur Trainingslogik ───────────────────────
        # Verhindert sample_weight=0 beim Advisor — Modell sah diesen Wert nie
        sample_weight = self._get_sample_weight(country_can, primary_role)

        # ── Profilzeile zusammenbauen ─────────────────────────────────────
        row = {
            # Numerische Spalten (num_cols)
            "year":                  year_profile,
            "education_rank":        edu_rank,
            "orgsize_rank":          org_rank,
            "workexp":               years_exp,
            "yearscode":             years_code,
            "hobbyyears":            hobby_years,
            "country_salary_median": country_med,
            "country_role_median":   country_role_med,
            "region_salary_median":  region_med,
            "region_role_median":    region_role_med,
            "role_salary_median":    role_med,
            "role_salary_p75":       role_p75,
            "sample_weight":         sample_weight,

            # Kategoriale Spalten (cat_cols)
            "country":               country_can,
            "currency":              currency_can,
            "remote":                remote_can,
            "branch":                "Professional",
            "employment":            "Employed, full-time",
            "industry":              industry_can,
            "icorpm":                icorpm_can,
            "education":             edu_can,
            "orgsize":               org_can,
            "country_region":        region,
            "age":                   age,
            "primary_role":          primary_role,
        }

        # ── devtype — Rolle für CountVectorizer ───────────────────────────
        # Übergibt den normalisierten Rollennamen (wie im Training nach Normalisierung)
        row["devtype"] = primary_role
        row["country_role"] = f"{country_can}_{primary_role}"

        # ── Skills → Mehrfachwert-Spalten (multi_cols) ────────────────────
        user_skills = [s.strip() for s in profile.get("skills", [])]

        row["language"]      = ";".join(s for s in user_skills if s in cfg.lang_known)
        row["database"]      = ";".join(s for s in user_skills if s in cfg.db_known)
        row["platform"]      = ";".join(s for s in user_skills if s in cfg.plat_known)
        row["webframe"]      = ";".join(s for s in user_skills if s in cfg.web_known)
        row["tech"]          = ";".join(s for s in user_skills if s in cfg.tech_known)
        row["ai"]            = ";".join(s for s in user_skills if s in cfg.ai_known)
        row["aiselect"]      = "Yes" if row["ai"] else "No"

        # Spalten ohne Profilbezug — leer lassen
        row["activities"]    = ""
        row["opsys"]         = ""
        row["office_stack"]  = ""
        row["aiagents"]      = ""

        # Fehlende num_cols mit 0 auffüllen
        for col in self.num_cols:
            if col not in row:
                row[col] = 0

        return pd.DataFrame([row])

    def predict_salary(self, profile: dict) -> float:
        """
        Sagt das Jahresgehalt in USD für ein gegebenes Nutzerprofil vorher.

        Parameters
        ----------
        profile : dict — Nutzerprofil

        Returns
        -------
        float — Erwartetes Jahresgehalt in USD
        """
        X    = self._build_profile_row(profile)
        pred = self.pipeline.predict(X)[0]
        return float(np.expm1(pred)) * 1000

    def recommend_skills_to_learn(self, profile: dict, top_n: int = 5) -> list:
        """
        Empfiehlt Skills mit dem höchsten positiven Gehaltseffekt.

        Prioritätsreihenfolge:
            1. Primärgruppen:   language, database, tech, ai
            2. Sekundärgruppen: platform, webframe
               (nur wenn aus Gruppe 1 weniger als top_n Empfehlungen)

        Parameters
        ----------
        profile : dict — Nutzerprofil
        top_n   : int  — Maximale Anzahl Empfehlungen (Standard: 5)

        Returns
        -------
        list of (skill, usd_effect) — Sortiert nach Gehaltseffekt absteigend
        """
        user_skills    = {s.lower() for s in profile.get("skills", [])}
        role           = profile.get("role", "")
        country        = profile.get("country", "Germany")
        allowed        = self._get_allowed_skills(role)
        context_median = self.get_context_median(country, role)

        PRIMARY_GROUPS   = {"language", "database", "tech", "ai"}
        SECONDARY_GROUPS = {"platform", "webframe"}

        def _collect(groups: set) -> list:
            """Sammelt Skill-Kandidaten aus den angegebenen Feature-Gruppen."""
            candidates = {}
            for feat, meta in self.skill_meta.items():
                level = meta["level"]
                if not level.startswith("multi_"):
                    continue
                if feat not in self.shap_df.columns:
                    continue
                group = level.replace("multi_", "")
                if group not in groups:
                    continue
                skill = meta["skill"]
                if skill.lower() in user_skills:
                    continue
                if skill.lower() not in allowed:
                    continue
                usd = shap_log_to_usd_skill(
                    feat, self.shap_df, context_median,
                    source_features=self.source_features,
                )
                if usd > 0:
                    candidates[skill] = usd
            return sorted(candidates.items(), key=lambda x: -x[1])

        result = _collect(PRIMARY_GROUPS)[:top_n]

        if len(result) < top_n:
            already   = {s for s, _ in result}
            secondary = [(s, u) for s, u in _collect(SECONDARY_GROUPS)
                         if s not in already]
            result   += secondary[:top_n - len(result)]

        return result

    def recommend_country(self, profile: dict, min_n: int = 30, top_n: int = 5) -> pd.DataFrame:
        """
        Gibt die Top-N Länder nach Mediangehalt für die angegebene Rolle zurück.

        Parameters
        ----------
        profile : dict — Nutzerprofil (nur 'role' wird verwendet)
        min_n   : int  — Mindestanzahl Befragter je Land (Standard: 30)
        top_n   : int  — Anzahl der zurückgegebenen Länder (Standard: 5)

        Returns
        -------
        pd.DataFrame — Spalten: median, count — nach Median absteigend sortiert
        """
        role     = profile.get("role", "Data or business analyst")
        primary  = self._normalize_role(role)
        role_col = "primary_role" if "primary_role" in self.df.columns else "devtype"

        mask = self.df[role_col] == primary
        if mask.sum() < min_n:
            mask = self.df["devtype"].str.contains(role, regex=False, na=False)

        return (
            self.df[mask]
            .groupby("country")["salary"]
            .agg(["median", "count"])
            .query(f"count >= {min_n}")
            .sort_values("median", ascending=False)
            .head(top_n)
        )

    def full_report(self, profile: dict) -> None:
        """
        Gibt einen vollständigen Gehaltsreport für ein Nutzerprofil aus.

        Inhalt:
            - Profilzusammenfassung mit Rollengruppe und Seniorität
            - Erwartetes Jahresgehalt vs. Marktmedian
            - Top-5 Skill-Empfehlungen mit Gehaltseffekt

        Parameters
        ----------
        profile : dict — Nutzerprofil
        """
        SEP          = "—" * 62
        country      = profile.get("country", "—")
        role         = profile.get("role", "—")
        role_display = self._normalize_role(role)
        role_group   = self._get_role_group(role)

        # Seniorität aus Erfahrungsjahren
        exp = int(profile.get("years_experience", 0))
        seniority = (
            "Junior"  if exp <= 2 else
            "Mid"     if exp <= 5 else
            "Senior"  if exp <= 10 else
            "Senior+"
        )

        # Validierung: Rolle muss im Datensatz vorhanden sein
        role_col    = "primary_role" if "primary_role" in self.df.columns else "devtype"
        primary     = self._normalize_role(role)
        valid_roles = set(self.df[role_col].dropna().unique())
        valid_roles |= set(
            self.df["devtype"].dropna().str.split(";").explode().str.strip().unique()
        )
        valid_roles.discard("None")
        valid_roles.discard("Unknown")
        valid_roles.discard("")

        if role not in valid_roles and primary not in valid_roles:
            print(f"⚠ Rolle '{role}' nicht in den Daten gefunden.")
            print("  Verwende advisor.available_roles() für die Rollenliste.")
            return

        # ── Profilkopf ────────────────────────────────────────────────────
        print(SEP)
        print("  📊 IT & Data Career Advisor — GEHALTSREPORT")
        print(SEP)
        print(f"  Rolle:        {role_display}  [{role_group}]")
        print(f"  Seniorität:   {seniority}  ({exp} Jahre Erfahrung)")
        print(f"  Skills:       {', '.join(profile.get('skills', []))}")
        print(f"  Alter:        {profile.get('age', '—')}")
        print(f"  Land:         {country}")
        print(f"  Abschluss:    {profile.get('education', '—')}")
        print(f"  Arbeitsform:  {profile.get('remote', '—')}")

        # ── Gehaltsvorhersage & Marktvergleich ────────────────────────────
        salary     = self.predict_salary(profile)
        ctx_median = self.get_context_median(country, role)

        print(f"\n  💰 Erwartetes Gehalt:  ${salary:,.0f} / Jahr")
        print(f"  📍 Marktmedian ({country}, {role_display}):"
              f"  ${ctx_median * 1000:,.0f} / Jahr")

        # ── Skill-Empfehlungen ────────────────────────────────────────────
        recs = self.recommend_skills_to_learn(profile, top_n=5)
        if recs:
            print(f"\n  💡 Top-5 Skills zum Erlernen:")
            for skill, usd in recs:
                meta  = next(
                    (m for m in self.skill_meta.values() if m["skill"] == skill), {}
                )
                level = meta.get("level", "").replace("multi_", "")
                print(f"     {skill:<24}  +${usd * 1000:>8,.0f}/Jahr   [{level}]")
        else:
            print(f"\n  ℹ️  Keine Skill-Empfehlungen für '{role_display}'.")
            print(f"     Füge cfg.data_role_skills['{role_display}'] hinzu.")

        print(SEP)

    def diagnose(self, profile: dict) -> None:
        """
        Gibt eine detaillierte Profildiagnose aus — zeigt exakt welche Werte
        das Modell erhält. Nützlich zum Debuggen bei unerwarteten Vorhersagen.

        Parameters
        ----------
        profile : dict — Nutzerprofil
        """
        role    = profile.get("role", "—")
        country = profile.get("country", "—")
        X_row   = self._build_profile_row(profile)

        # ── Rolleninfo ────────────────────────────────────────────────────
        print("=== Rolleninformation ===")
        print(f"  Rolle (Eingabe):  {role}")
        print(f"  primary_role:     {self._normalize_role(role)}")
        print(f"  Gruppe:           {self._get_role_group(role)}")
        print(f"  devtype (Modell): {X_row['devtype'].values[0]}")
        print(f"  sample_weight:    {X_row['sample_weight'].values[0]:.6f}")

        # ── Numerische Merkmale ───────────────────────────────────────────
        print("\n=== Numerische Merkmale ===")
        for col in self.num_cols:
            if col in X_row.columns:
                print(f"  {col:<30} = {X_row[col].values[0]}")

        # ── Kategoriale Merkmale ──────────────────────────────────────────
        print("\n=== Kategorische Merkmale ===")
        for col in self.cat_cols:
            if col in X_row.columns:
                print(f"  {col:<30} = {X_row[col].values[0]}")

        # ── Target Encoding ───────────────────────────────────────────────
        print("\n=== Target Encoding (Mediane) ===")
        for col in ["country_salary_median", "country_role_median",
                    "role_salary_median",    "role_salary_p75",
                    "region_salary_median",  "region_role_median"]:
            if col in X_row.columns:
                val = X_row[col].values[0]
                print(f"  {col:<30} = {val:.2f}k  (= ${val * 1000:,.0f})")

        # ── Modellvorhersage ──────────────────────────────────────────────
        print("\n=== Vorhersage ===")
        raw = self.pipeline.predict(X_row)[0]
        print(f"  Rohvorhersage (log1p): {raw:.4f}")
        print(f"  expm1(raw):            {np.expm1(raw):.2f}k")
        print(f"  Ergebnis $:            ${np.expm1(raw) * 1000:,.0f}")

        # ── Vergleich mit realen Daten ────────────────────────────────────
        print("\n=== Vergleich mit realen Daten ===")
        role_col = "primary_role" if "primary_role" in self.df.columns else "devtype"
        primary  = self._normalize_role(role)

        mask = (self.df["country"] == country) & (self.df[role_col] == primary)
        if mask.sum() < 10:
            mask = (
                (self.df["country"] == country) &
                (self.df["devtype"].str.contains(role, regex=False, na=False))
            )

        sub = self.df[mask]
        print(f"  {country} + '{primary}': {len(sub)} Zeilen")
        if len(sub) > 0:
            print(f"  Median:        {sub['salary'].median():.1f}k"
                  f"  (= ${sub['salary'].median() * 1000:,.0f})")
            print(f"  25. Perzentil: {sub['salary'].quantile(0.25):.1f}k"
                  f"  (= ${sub['salary'].quantile(0.25) * 1000:,.0f})")
            print(f"  75. Perzentil: {sub['salary'].quantile(0.75):.1f}k"
                  f"  (= ${sub['salary'].quantile(0.75) * 1000:,.0f})")