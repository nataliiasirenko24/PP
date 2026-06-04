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
1. Bibliotheksimport, Datenladen und allgemeine Datenstrukturen
2. EDA + Idee für Features Engineering  
3. Base Model 
4. Train-Test-Split
5. ML 
6. SHAP-Analyse & Modellinterpretation
7. Data Career Advisor — Empfehlungssystem
8. Fazit

---

### 🛠️ Technologie-Stack

`Python` · `CatBoost` · `Optuna` · `SHAP` · `scikit-learn` · `Pandas` · `Matplotlib` · `Seaborn`

---

### ✨ Wichtigste Ergebnisse

* **Bestes Modell** CatBoostRegressor (Optuna-optimiert)
* **MAE** ~$25 300 / Jahr 
* **R²**  0.62 

---
