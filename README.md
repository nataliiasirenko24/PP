# 📊 Gehaltsprognose & Interpretation für Data-Berufe (ML-Projekt)

---

### 📌 Projekt-Metadaten

* **Datenquelle:** [Stack Overflow Developer Survey](https://survey.stackoverflow.co/)
* **Untersuchungszeitraum:** 2020–2025
* **Datensatzgröße** ~198 600 Datensätze aus 180+ Ländern

---

### 🔍 Kurzbeschreibung

Dieses Projekt entwickelt eine vollständige End-to-End-Pipeline zur **Vorhersage und Interpretation von Gehältern** auf dem internationalen Markt für Data-Berufe.

Auf Basis von Stack Overflow Developer Surveys (2020–2025) wird ein robustes Regressionsmodell trainiert, das Gehälter in Abhängigkeit von Land, Rolle, Erfahrung, Bildungsabschluss und technischen Skills vorhersagt. SHAP-Analysen sorgen für vollständige Transparenz (White-Box-Ansatz) und isolieren den wirtschaftlichen Effekt einzelner Skills.

Das Endergebnis ist ein interaktives **Data Career Advisor**-System, das personalisierte Gehaltsschätzungen und Skill-Empfehlungen mit quantifizierbarem Einkommenspotenzial liefert.

---

### 📘 Projektstruktur
0. Bibliotheksimport, Datenladen und allgemeine Datenstrukturen
1. EDA + Idee für Features Engineering  
2. Base Model 
3. Train-Test-Split
4. ML 
5. SHAP-Analyse & Modellinterpretation
6. Data Career Advisor — Empfehlungssystem

---

### 🛠️ Technologie-Stack

`Python` · `CatBoost` · `Optuna` · `SHAP` · `scikit-learn` · `Pandas` · `Matplotlib` · `Seaborn`

---

### ✨ Wichtigste Ergebnisse

* **Bestes Modell** CatBoostRegressor (Optuna-optimiert)
* **MAE** ~$25 900 / Jahr 
* **R²**  0.59 