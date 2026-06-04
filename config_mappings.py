# ════════════════════════════════════════════════════════════════════════════
# config_mappings.py — Konfiguration & Mappings für das Projekt
#
# Abschnitte:
#   1.  Schema          — Spaltennamen je Umfragejahr
#   2.  Länder          — Normalisierung & Regionen
#   3.  Demografie      — Alter, Bildung, Beschäftigung
#   4.  Unternehmen     — Größe, Branche, IC/Manager
#   5.  Tech-Stack      — Sprachen, Datenbanken, Plattformen, KI
#   6.  Rollen          — DevType-Klassifizierung & Skill-Whitelists
#   7.  Advisor         — Skill-Kategorien für DataCareerAdvisor
# ════════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════════
# 1. SCHEMA — Spaltennamen je Umfragejahr (2020–2025)
#
# Kanonischer Name → originaler Spaltenname im jeweiligen Jahrgang.
# None = Spalte im betreffenden Jahr nicht vorhanden.
# ════════════════════════════════════════════════════════════════════════════

schema = {yr: dict(
    # ── Zielvariable & Währung ────────────────────────────────────────────
    salary       = "ConvertedCompYearly" if yr >= 2021 else "ConvertedComp",
    currency     = "Currency"            if yr >= 2021 else "CurrencyDesc",

    # ── Demografie & Basisprofil ─────────────────────────────────────────
    country      = "Country",
    age          = "Age",
    workexp      = "WorkExp"       if yr >= 2022 else None,
    yearscode    = "YearsCode",
    yearscodepro = "YearsCodePro",
    remote       = "RemoteWork"    if yr >= 2022 else None,

    # ── Beruflicher Werdegang ────────────────────────────────────────────
    branch       = "MainBranch",
    devtype      = "DevType",
    education    = "EdLevel",
    employment   = "Employment",
    industry     = "Industry"      if yr >= 2022 else None,
    orgsize      = "OrgSize",
    icorpm       = "ICorPM"        if yr >= 2022 else None,

    # ── Programmiersprachen ───────────────────────────────────────────────
    language_have  = "LanguageHaveWorkedWith" if yr >= 2021 else "LanguageWorkedWith",
    language_entry = "LanguagesHaveEntry"     if yr >= 2021 else None,

    # ── Datenbanken ───────────────────────────────────────────────────────
    database_have  = "DatabaseHaveWorkedWith" if yr >= 2021 else "DatabaseWorkedWith",
    database_entry = "DatabaseHaveEntry"      if yr >= 2021 else None,

    # ── Plattformen & Cloud ───────────────────────────────────────────────
    platform_have  = "PlatformHaveWorkedWith" if yr >= 2021 else "PlatformWorkedWith",
    platform_entry = "PlatformHaveEntry"      if yr == 2025 else None,

    # ── Web-Frameworks ────────────────────────────────────────────────────
    webframe_have  = "WebframeHaveWorkedWith" if yr >= 2021 else "WebframeWorkedWith",
    webframe_entry = "WebframeHaveEntry"      if yr == 2025 else None,

    # ── Tools & Bibliotheken ──────────────────────────────────────────────
    tech_have  = ("SOTagsHaveWorkedWith"   if yr >= 2025 else
                  "MiscTechHaveWorkedWith" if yr >= 2021 else
                  "MiscTechWorkedWith"     if yr == 2020 else None),
    tech_entry = ("SOTagsHaveEntry"        if yr == 2025 else None),

    # ── KI-Tools ─────────────────────────────────────────────────────────
    ai_have  = ("AIModelsHaveWorkedWith"    if yr >= 2025 else
                "AISearchDevHaveWorkedWith" if yr == 2024 else
                "AISearchHaveWorkedWith"    if yr == 2023 else None),
    ai_entry = ("AIModelsWantEntry"         if yr == 2025 else None),
    aiselect = ("AISelect"                  if yr >= 2023 else None),
    aiagents = ("AIAgentExternal"           if yr >= 2025 else None),

    # ── Sonstige Aktivitäten ─────────────────────────────────────────────
    activities   = "CodingActivities"                if yr >= 2022 else None,
    opsys        = "OpSysProfessional use"           if yr >= 2022 else None,
    office_stack = "OfficeStackAsyncHaveWorkedWith"  if yr >= 2022 else None,

) for yr in range(2020, 2026)}


# ════════════════════════════════════════════════════════════════════════════
# 2. LÄNDER — Normalisierung & Regionen
# ════════════════════════════════════════════════════════════════════════════

# ── Ländernamen normalisieren (lange / veraltete Bezeichnungen → Standard) ──
country_mapping = {
    "United States of America":                              "United States",
    "United Kingdom of Great Britain and Northern Ireland":  "United Kingdom",
    "Russian Federation":                                    "Russia",
    "Iran, Islamic Republic of...":                          "Iran",
    "Republic of Korea":                                     "South Korea",
    "North Korea":                                           "South Korea",
    "Venezuela, Bolivarian Republic of...":                  "Venezuela",
    "The former Yugoslav Republic of Macedonia":             "Republic of North Macedonia",
    "Republic of North Macedonia":                           "North Macedonia",
    "Republic of Moldova":                                   "Moldova",
    "Syrian Arab Republic":                                  "Syria",
    "Viet Nam":                                              "Vietnam",
    "United Republic of Tanzania":                           "Tanzania",
    "Congo, Republic of the...":                             "Republic of the Congo",
    "Democratic Republic of the Congo":                      "DR Congo",
    "Libyan Arab Jamahiriya":                                "Libya",
}

# ── Länder → Makroregionen ────────────────────────────────────────────────
region_mapping = {
    # ── Nordamerika ───────────────────────────────────────────────────────
    "United States":                                         "North America",
    "United States of America":                              "North America",
    "Canada":                                                "North America",

    # ── UK & Irland ───────────────────────────────────────────────────────
    "United Kingdom":                                        "UK",
    "United Kingdom of Great Britain and Northern Ireland":  "UK",
    "Ireland":                                               "UK",
    "Isle of Man":                                           "UK",

    # ── DACH ──────────────────────────────────────────────────────────────
    "Germany":                                               "DACH",
    "Switzerland":                                           "DACH",
    "Austria":                                               "DACH",
    "Liechtenstein":                                         "DACH",

    # ── Nordics ───────────────────────────────────────────────────────────
    "Sweden":                                                "Nordics",
    "Norway":                                                "Nordics",
    "Denmark":                                               "Nordics",
    "Finland":                                               "Nordics",
    "Iceland":                                               "Nordics",
    "Estonia":                                               "Nordics",
    "Latvia":                                                "Nordics",
    "Lithuania":                                             "Nordics",

    # ── Westeuropa ────────────────────────────────────────────────────────
    "France":                                                "W_Europe",
    "Netherlands":                                           "W_Europe",
    "Belgium":                                               "W_Europe",
    "Spain":                                                 "W_Europe",
    "Italy":                                                 "W_Europe",
    "Portugal":                                              "W_Europe",
    "Luxembourg":                                            "W_Europe",
    "Monaco":                                                "W_Europe",
    "Andorra":                                               "W_Europe",
    "San Marino":                                            "W_Europe",
    "Malta":                                                 "W_Europe",

    # ── Osteuropa ─────────────────────────────────────────────────────────
    "Poland":                                                "E_Europe",
    "Czech Republic":                                        "E_Europe",
    "Slovakia":                                              "E_Europe",
    "Hungary":                                               "E_Europe",
    "Romania":                                               "E_Europe",
    "Bulgaria":                                              "E_Europe",
    "Slovenia":                                              "E_Europe",
    "Croatia":                                               "E_Europe",
    "Serbia":                                                "E_Europe",
    "Bosnia and Herzegovina":                                "E_Europe",
    "Montenegro":                                            "E_Europe",
    "Kosovo":                                                "E_Europe",
    "Albania":                                               "E_Europe",
    "Greece":                                                "E_Europe",
    "Cyprus":                                                "E_Europe",
    "Ukraine":                                               "E_Europe",
    "Belarus":                                               "E_Europe",
    "Republic of Moldova":                                   "E_Europe",
    "Moldova":                                               "E_Europe",
    "Republic of North Macedonia":                           "E_Europe",
    "The former Yugoslav Republic of Macedonia":             "E_Europe",

    # ── GUS ───────────────────────────────────────────────────────────────
    "Russian Federation":                                    "CIS",
    "Kazakhstan":                                            "CIS",
    "Azerbaijan":                                            "CIS",
    "Armenia":                                               "CIS",
    "Georgia":                                               "CIS",
    "Uzbekistan":                                            "CIS",
    "Kyrgyzstan":                                            "CIS",
    "Tajikistan":                                            "CIS",
    "Turkmenistan":                                          "CIS",

    # ── Naher Osten ───────────────────────────────────────────────────────
    "Israel":                                                "Middle East",
    "Turkey":                                                "Middle East",
    "United Arab Emirates":                                  "Middle East",
    "Saudi Arabia":                                          "Middle East",
    "Kuwait":                                                "Middle East",
    "Qatar":                                                 "Middle East",
    "Bahrain":                                               "Middle East",
    "Oman":                                                  "Middle East",
    "Jordan":                                                "Middle East",
    "Lebanon":                                               "Middle East",
    "Iraq":                                                  "Middle East",
    "Iran":                                                  "Middle East",
    "Iran, Islamic Republic of...":                          "Middle East",
    "Palestine":                                             "Middle East",
    "Syrian Arab Republic":                                  "Middle East",
    "Yemen":                                                 "Middle East",

    # ── Indien ────────────────────────────────────────────────────────────
    "India":                                                 "India",

    # ── Ostasien ──────────────────────────────────────────────────────────
    "China":                                                 "East Asia",
    "Japan":                                                 "East Asia",
    "Republic of Korea":                                     "East Asia",
    "South Korea":                                           "East Asia",
    "Hong Kong (S.A.R.)":                                    "East Asia",
    "Taiwan":                                                "East Asia",
    "Mongolia":                                              "East Asia",
    "North Korea":                                           "East Asia",
    "Democratic People's Republic of Korea":                 "East Asia",

    # ── Südostasien & Südasien ────────────────────────────────────────────
    "Singapore":                                             "SE Asia",
    "Malaysia":                                              "SE Asia",
    "Indonesia":                                             "SE Asia",
    "Philippines":                                           "SE Asia",
    "Viet Nam":                                              "SE Asia",
    "Thailand":                                              "SE Asia",
    "Myanmar":                                               "SE Asia",
    "Cambodia":                                              "SE Asia",
    "Sri Lanka":                                             "SE Asia",
    "Bangladesh":                                            "SE Asia",
    "Nepal":                                                 "SE Asia",
    "Pakistan":                                              "SE Asia",
    "Afghanistan":                                           "SE Asia",
    "Maldives":                                              "SE Asia",
    "Bhutan":                                                "SE Asia",
    "Lao People's Democratic Republic":                      "SE Asia",
    "Brunei Darussalam":                                     "SE Asia",
    "Timor-Leste":                                           "SE Asia",

    # ── Lateinamerika ─────────────────────────────────────────────────────
    "Brazil":                                                "Latin America",
    "Mexico":                                                "Latin America",
    "Argentina":                                             "Latin America",
    "Colombia":                                              "Latin America",
    "Chile":                                                 "Latin America",
    "Peru":                                                  "Latin America",
    "Venezuela, Bolivarian Republic of...":                  "Latin America",
    "Ecuador":                                               "Latin America",
    "Uruguay":                                               "Latin America",
    "Bolivia":                                               "Latin America",
    "Paraguay":                                              "Latin America",
    "Panama":                                                "Latin America",
    "Costa Rica":                                            "Latin America",
    "Guatemala":                                             "Latin America",
    "Honduras":                                              "Latin America",
    "El Salvador":                                           "Latin America",
    "Nicaragua":                                             "Latin America",
    "Dominican Republic":                                    "Latin America",
    "Cuba":                                                  "Latin America",
    "Haiti":                                                 "Latin America",
    "Jamaica":                                               "Latin America",
    "Trinidad and Tobago":                                   "Latin America",
    "Bahamas":                                               "Latin America",
    "Barbados":                                              "Latin America",
    "Guyana":                                                "Latin America",
    "Suriname":                                              "Latin America",
    "Grenada":                                               "Latin America",
    "Saint Vincent and the Grenadines":                      "Latin America",
    "Saint Lucia":                                           "Latin America",
    "Saint Kitts and Nevis":                                 "Latin America",
    "Dominica":                                              "Latin America",
    "Antigua and Barbuda":                                   "Latin America",
    "Belize":                                                "Latin America",

    # ── Afrika ────────────────────────────────────────────────────────────
    "Nigeria":                                               "Africa",
    "South Africa":                                          "Africa",
    "Kenya":                                                 "Africa",
    "Ghana":                                                 "Africa",
    "Egypt":                                                 "Africa",
    "Morocco":                                               "Africa",
    "Tunisia":                                               "Africa",
    "Algeria":                                               "Africa",
    "Ethiopia":                                              "Africa",
    "Tanzania":                                              "Africa",
    "United Republic of Tanzania":                           "Africa",
    "Uganda":                                                "Africa",
    "Cameroon":                                              "Africa",
    "Senegal":                                               "Africa",
    "Côte d'Ivoire":                                         "Africa",
    "Democratic Republic of the Congo":                      "Africa",
    "Congo, Republic of the...":                             "Africa",
    "Rwanda":                                                "Africa",
    "Zambia":                                                "Africa",
    "Zimbabwe":                                              "Africa",
    "Mozambique":                                            "Africa",
    "Madagascar":                                            "Africa",
    "Sudan":                                                 "Africa",
    "Somalia":                                               "Africa",
    "Namibia":                                               "Africa",
    "Botswana":                                              "Africa",
    "Swaziland":                                             "Africa",
    "Angola":                                                "Africa",
    "Libyan Arab Jamahiriya":                                "Africa",
    "Mauritius":                                             "Africa",
    "Togo":                                                  "Africa",
    "Benin":                                                 "Africa",
    "Malawi":                                                "Africa",
    "Guinea":                                                "Africa",
    "Guinea-Bissau":                                         "Africa",
    "Gambia":                                                "Africa",
    "Niger":                                                 "Africa",
    "Mali":                                                  "Africa",
    "Burkina Faso":                                          "Africa",
    "Mauritania":                                            "Africa",
    "Djibouti":                                              "Africa",
    "Cape Verde":                                            "Africa",
    "Lesotho":                                               "Africa",
    "Gabon":                                                 "Africa",

    # ── Ozeanien ──────────────────────────────────────────────────────────
    "Australia":                                             "Oceania",
    "New Zealand":                                           "Oceania",
    "Fiji":                                                  "Oceania",
    "Papua New Guinea":                                      "Oceania",
    "Samoa":                                                 "Oceania",
    "Palau":                                                 "Oceania",

    # ── Sonstiges ─────────────────────────────────────────────────────────
    "Nomadic":                                               "Other",
}


# ════════════════════════════════════════════════════════════════════════════
# 3. DEMOGRAFIE — Alter, Bildung, Beschäftigung, Arbeitsmodus
# ════════════════════════════════════════════════════════════════════════════

# ── Bildungsabschlüsse → kanonische Kurzbezeichnungen ─────────────────────
education_mapping = {
    # Promotion
    "Other doctoral degree (Ph.D., Ed.D., etc.)":               "PhD",
    "Professional degree (JD, MD, Ph.D, Ed.D, etc.)":           "PhD",

    # Master
    "Master\u2019s degree (M.A., M.S., M.Eng., MBA, etc.)":     "Master",
    "Master's degree (M.A., M.S., M.Eng., MBA, etc.)":          "Master",
    "Professional degree (JD, MD, etc.)":                        "Master",

    # Bachelor
    "Bachelor\u2019s degree (B.A., B.S., B.Eng., etc.)":        "Bachelor",
    "Bachelor's degree (B.A., B.S., B.Eng., etc.)":             "Bachelor",

    # College / Teilstudium
    "Some college/university study without earning a degree":    "College / Undergrad",
    "Associate degree (A.A., A.S., etc.)":                       "College / Undergrad",

    # Schule
    "Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)": "School",
    "Primary/elementary school":                                 "School",

    # Sonstiges
    "I never completed any formal education":                    "Other",
    "Something else":                                            "Other",
    "Other (please specify):":                                   "Other",
    "Unknown":                                                   "Other",
}

# ── Bildungsabschlüsse → Ordinalrang (für numerische Modelle) ─────────────
education_rank_mapping = {
    "PhD":               5,
    "Master":            4,
    "Bachelor":          3,
    "College / Undergrad": 2,
    "School":            1,
    "Other":             0,
}

# ── Arbeitsmodus → kanonische Kategorien ──────────────────────────────────
remote_mapping = {
    # Remote
    "Fully remote":                                              "Remote",
    "Remote":                                                    "Remote",

    # Hybrid
    "Hybrid (some remote, some in-person)":                      "Hybrid",
    "Hybrid (some remote, leans heavy to in-person)":            "Hybrid",
    "Hybrid (some in-person, leans heavy to flexibility)":       "Hybrid",
    "Your choice (very flexible, you can come in when you want or just as needed)": "Hybrid",

    # Vor Ort
    "In-person":                                                 "On-site",
    "Full in-person":                                            "On-site",

    # Unbekannt
    "Unknown":                                                   "Unknown",
}

# ── Hauptbeschäftigung (MainBranch) → kanonische Kategorien ──────────────
branch_mapping = {
    # Berufliche Entwickler
    "I am a developer by profession":                            "Professional",

    # Code als Teil anderer Tätigkeit
    "I am not primarily a developer, but I write code sometimes as part of my work":           "Coding at Work/Studies",
    "I am not primarily a developer, but I write code sometimes as part of my work/studies":   "Coding at Work/Studies",
    "I am a student who is learning to code":                    "Coding at Work/Studies",

    # Sonstiges
    "I work with developers or my work supports developers but am not a developer by profession": "Other",
    "I used to be a developer by profession, but no longer am":  "Other",
    "I am learning to code":                                     "Other",
    "I code primarily as a hobby":                               "Other",
    "Unknown":                                                   "Other",
}

# ── Coding-Aktivitäten außerhalb der Arbeit ───────────────────────────────
activities_mapping = {
    "Hobby":                                                     "Hobby",
    "Contribute to open-source projects":                        "Open Source",
    "Professional development or self-paced learning from online courses": "Learning",
    "School or academic work":                                   "Learning",
    "Freelance/contract work":                                   "Professional",
    "Bootstrapping a business":                                  "Professional",
    "I don\u2019t code outside of work":                         "Inactive",
    "Other (please specify):":                                   "Other",
    "Unknown":                                                   "Other",
}


# ════════════════════════════════════════════════════════════════════════════
# 4. UNTERNEHMEN — Größe, Branche, IC/Manager
# ════════════════════════════════════════════════════════════════════════════

# ── Unternehmensgröße → kanonische Gruppen ────────────────────────────────
orgsize_mapping = {
    "10,000 or more employees":                                  "10k+",
    "5,000 to 9,999 employees":                                  "Large 2 (5-9k)",
    "1,000 to 4,999 employees":                                  "Large 1 (1-5k)",
    "500 to 999 employees":                                      "Medium 2 (500-999)",
    "100 to 499 employees":                                      "Medium 1 (100-499)",
    "20 to 99 employees":                                        "Small (20-99)",
    "10 to 19 employees":                                        "Micro (2-19)",
    "2 to 9 employees":                                          "Micro (2-19)",
    "Less than 20 employees":                                    "Micro (2-19)",
    "Just me - I am a freelancer, sole proprietor, etc.":        "Feelancer (1)",
    "I don\u2019t know":                                         "Other",
    "I don't know":                                              "Other",
    "Unknown":                                                   "Other",
}

# ── Unternehmensgröße → Ordinalrang (für numerische Modelle) ──────────────
orgsize_rank_mapping = {
    "10k+":              9,
    "Large 2 (5-9k)":   8,
    "Large 1 (1-5k)":   7,
    "Medium 2 (500-999)": 6,
    "Medium 1 (100-499)": 5,
    "Small (20-99)":    3,
    "Micro (2-19)":     2,
    "Feelancer (1)":    1,
    "Other":            0,
}

# ── Branche → kanonische Gruppen ─────────────────────────────────────────
industry_mapping = {
    # Technologie & IT
    "Information Services, IT, Software Development, or other Technology": "IT, Telecom & Tech",
    "Software Development":                                      "IT, Telecom & Tech",
    "Internet, Telecomm or Information Services":                "IT, Telecom & Tech",
    "Computer Systems Design and Services":                      "IT, Telecom & Tech",

    # Finanzen & Versicherung
    "Financial Services":                                        "Banking, Finance & Insurance",
    "Banking/Financial Services":                                "Banking, Finance & Insurance",
    "Fintech":                                                   "Banking, Finance & Insurance",
    "Insurance":                                                 "Banking, Finance & Insurance",

    # Gesundheit & Bildung
    "Healthcare":                                                "Healthcare & Medicine",
    "Higher Education":                                          "Education",

    # Handel, Logistik & Staat
    "Retail and Consumer Services":                              "Retail & Consumer Services",
    "Government":                                                "Government & Public Sector",
    "Manufacturing, Transportation, or Supply Chain":            "Manufacturing, Logistics & Supply Chain",
    "Manufacturing":                                             "Manufacturing, Logistics & Supply Chain",
    "Transportation, or Supply Chain":                           "Manufacturing, Logistics & Supply Chain",

    # Energie & Medien
    "Energy":                                                    "Energy & Utilities",
    "Oil & Gas":                                                 "Energy & Utilities",
    "Media & Advertising Services":                              "Media & Advertising",
    "Advertising Services":                                      "Media & Advertising",

    # Sonstiges
    "Wholesale":                                                 "Wholesale & Trade",
    "Legal Services":                                            "Legal Services",
    "Other":                                                     "Other",
    "Other:":                                                    "Other",
    "Unknown":                                                   "Other",
}

# ── IC oder Manager ───────────────────────────────────────────────────────
icorpm_mapping = {
    "Individual contributor":   "IC",
    "Independent contributor":  "IC",
    "People manager":           "Manager",
    "Unknown":                  "Unknown",
}


# ════════════════════════════════════════════════════════════════════════════
# 5. TECH-STACK — Sprachen, Datenbanken, Plattformen, Frameworks, KI
# ════════════════════════════════════════════════════════════════════════════

# ── Programmiersprachen → kanonische Namen ────────────────────────────────
language_mapping = {
    "Bash/Shell":                "Bash/Shell/PowerShell",
    "PowerShell":                "Bash/Shell/PowerShell",
    "Bash/Shell (all shells)":   "Bash/Shell/PowerShell",
    "MATLAB":                    "Matlab",
    "LISP":                      "Lisp",
    "COBOL":                     "Cobol",
    "Objective C":               "Objective-C",
    "clojure":                   "Clojure",
    "Clojure, ClojureScript":    "Clojure",
    "haskell":                   "Haskell",
    "nix":                       "Nix",
    "Visual Basic (.Net)":       "VBA",
    "Unknown":                   "Other",
}

# ── Datenbanken → kanonische Namen ────────────────────────────────────────
database_mapping = {
    "sqlite":                    "SQLite",
    "Dynamodb":                  "DynamoDB",
    "Couch DB":                  "CouchDB",
    "Couchbase":                 "CouchDB",
    "Firebase Realtime Database": "Firebase",
    "Cloud Firestore":           "Firebase",
    "FirebirdSQL":               "Firebird",
    "firebird":                  "Firebird",
    "Firebird SQL":              "Firebird",
    "Neo4j":                     "Neo4J",
    "Azure SQL":                 "SQL Server",
    "Microsoft SQL Server":      "SQL Server",
    "Opensearch":                "OpenSearch",
    "RavenDb":                   "RavenDB",
    "neon":                      "Neon",
    "SAP HANA":                  "HANA",
    "Cockroachdb":               "CockroachDB",
    "Unknown": "Other"
}

# ── Plattformen & Cloud → kanonische Namen ────────────────────────────────
platform_mapping = {
    "Amazon Web Services (AWS)":           "AWS",
    "Google Cloud Platform":               "Google Cloud",
    "Digital Ocean":                       "DigitalOcean",
    "Linode, now Akamai":                  "Linode",
    "Oracle Cloud Infrastructure (OCI)":   "Oracle Cloud",
    "Oracle Cloud Infrastructure":         "Oracle Cloud",
    "IBM Cloud or Watson":                 "IBM Cloud",
    "IBM Cloud Or Watson":                 "IBM Cloud",
    "fly.io":                              "Fly.io",
    "Podman":                              "Docker",
    "conda":                               "Conda",
    "nix":                                 "Nix",
    "cmake":                               "CMake",
    "uv":                                  "UV",
    "Uv":                                  "UV",
    "helm":                                "Helm",
    "Unknown": "Other"
}

# ── Web-Frameworks → kanonische Namen ────────────────────────────────────
webframe_mapping = {
    "React.js":       "React",
    "ASP.NET CORE":   "ASP.NET Core",
    "Angular.js":     "Angular",
    "AngularJS":      "Angular",
    "Spring Boot":    "Spring Framework",
    "Unknown": "Other"
}

# ── Tools & Bibliotheken → kanonische Namen ───────────────────────────────
# Regex-Muster für komplexe Umbenennungen (wird in normalize_multivalue_column verwendet)
tech_map = {
    r".NET.*":        ".NET",
    r"Scikit-learn.*": "Scikit-Learn",
    r"Torch.*":       "PyTorch",
    r"Teraform":      "Terraform",
}

# Exakte Umbenennungen für häufige Varianten
tech_mapping = {
    # .NET-Familie → einheitlich .NET
    ".NET Framework":          ".NET",
    ".NET Core / .NET 5":      ".NET",
    ".NET Core":               ".NET",
    ".NET (5+)":               ".NET",
    ".NET Framework (1.0 - 4.8)": ".NET",
    ".NET MAUI":               ".NET",
    ".NET 8 or higher":        ".NET",

    # Bibliotheken
    "Torch/PyTorch":           "PyTorch",
    "Scikit-learn":            "Scikit-Learn",
    "Opencv":                  "OpenCV",
    "Spring Framework":        "Spring",

    "Unknown": "Other"
}

# ── KI-Tools → kanonische Namen ───────────────────────────────────────────
ai_mapping = {
    # OpenAI
    "openAI GPT (chatbot models)":          "OpenAI / ChatGPT",
    "openAI Reasoning models":              "OpenAI / ChatGPT",
    "openAI Image generating models":       "OpenAI / ChatGPT",
    "OpenAI Codex":                         "OpenAI / ChatGPT",
    "ChatGPT":                              "OpenAI / ChatGPT",

    # Google
    "Google Bard AI":                       "Google Gemini",
    "Gemini (Flash general purpose models)": "Google Gemini",
    "Gemini (Pro Reasoning models)":         "Google Gemini",

    # Anthropic
    "Anthropic: Claude Sonnet":             "Claude",

    # DeepSeek
    "DeepSeek (R- Reasoning models)":       "DeepSeek",
    "DeepSeek (V- General purpose models)": "DeepSeek",

    # Perplexity
    "Perplexity Sonar models":              "Perplexity AI",

    # Meta
    "Meta Llama (all models)":              "Meta AI",

    "Unknown":                              "Other"
}

# ── Betriebssysteme (professionell) → kanonische Gruppen ──────────────────
opsys_mapping = {
    "Windows":                               "Windows",
    "MacOS":                                 "MacOS",
    "macOS":                                 "MacOS",
    "Ubuntu":                                "Ubuntu",
    "Windows Subsystem for Linux (WSL)":     "Linux",
    "Linux-based":                           "Linux",
    "Other Linux-based":                     "Linux",
    "Linux (non-WSL)":                       "Linux",
    "Debian":                                "Other",
    "iOS":                                   "Other",
    "Android":                               "Other",
    "Red Hat":                               "Other",
    "Arch":                                  "Other",
    "Fedora":                                "Other",
    "iPadOS":                                "Other",
    "Cygwin":                                "Other",
    "BSD":                                   "Other",
    "ChromeOS":                              "Other",
    "NixOS":                                 "Other",
    "AIX":                                   "Other",
    "Solaris":                               "Other",
    "Pop!_OS":                               "Other",
    "Haiku":                                 "Other",
    "Other (Please Specify):":               "Other",
    "Other (please specify):":               "Other",
    "Unknown":                               "Other",
}

# ── Office- & Collaboration-Tools → kanonische Gruppen ────────────────────
office_stack_mapping = {
    "Jira":                                  "Jira",
    "Jira Work Management":                  "Jira",
    "Confluence":                            "Confluence",
    "Markdown File":                         "Markdown File",
    "Trello":                                "Trello",
    "Notion":                                "Notion",
    "GitHub":                                "GitHub",
    "GitHub Discussions":                    "GitHub",
    "Azure Devops":                          "Azure Devops",
    "Miro":                                  "Miro",
    "GitLab":                                "Other",
    "Wikis":                                 "Other",
    "Asana":                                 "Other",
    "Obsidian":                              "Other",
    "Microsoft Planner":                     "Other",
    "Clickup":                               "Other",
    "ClickUp":                               "Other",
    "Google Workspace":                      "Other",
    "Doxygen":                               "Other",
    "Stack Overflow for Teams":              "Other",
    "Airtable":                              "Other",
    "Linear":                                "Other",
    "Redmine":                               "Other",
    "Monday.com":                            "Other",
    "monday.com":                            "Other",
    "YouTrack":                              "Other",
    "Lucid (includes Lucidchart)":           "Other",
    "Lucid":                                 "Other",
    "Google Colab":                          "Other",
    "Smartsheet":                            "Other",
    "Basecamp":                              "Other",
    "Microsoft Lists":                       "Other",
    "Shortcut":                              "Other",
    "Wrike":                                 "Other",
    "Coda":                                  "Other",
    "Adobe Workfront":                       "Other",
    "Redocly":                               "Other",
    "Nuclino":                               "Other",
    "DingTalk (Teambition)":                 "Other",
    "Dingtalk (Teambition)":                 "Other",
    "Document360":                           "Other",
    "Swit":                                  "Other",
    "Tettra":                                "Other",
    "Workzone":                              "Other",
    "Planview Projectplace or Clarizen":     "Other",
    "Planview Projectplace Or Clarizen":     "Other",
    "Wimi":                                  "Other",
    "Leankor":                               "Other",
    "Cerri":                                 "Other",
    "Unknown":                               "Other",
}

# ── KI-Nutzung (AISelect) → Ja / Nein ─────────────────────────────────────
aiselect_mapping = {
    "Yes":                                   "Yes",
    "Yes, I use AI tools daily":             "Yes",
    "Yes, I use AI tools weekly":            "Yes",
    "Yes, I use AI tools monthly or infrequently": "Yes",
    "No, and I don't plan to":               "No",
    "No, but I plan to soon":                "No",
    "Unknown":                               "Unknown",
}


# ════════════════════════════════════════════════════════════════════════════
# 6. ROLLEN — DevType-Klassifizierung
# ════════════════════════════════════════════════════════════════════════════

# ── SO-Survey-Rollenname → interne Anzeigename (für Advisor-Report) ───────
role_name_mapping = {
#     "Data scientist or machine learning specialist": "Data Scientist / ML specialist",
#     "Data scientist":                               "Data Scientist / ML specialist",
#     "Applied scientist":                            "Applied scientist",
#     "Data engineer":                                "Data Engineer",
#     "Engineer, data":                               "Data Engineer",
#     "AI/ML engineer":                               "AI/ML Engineer",
#     "Database administrator":                       "Database Administrator",
#     "Database administrator or engineer":           "Database Administrator",
#     "Data or business analyst":                     "Data Analyst",
#     "Financial analyst or engineer":                "Financial Analyst",
#     "Scientist":                                    "Scientist",
#     "Developer, AI":                                "Data Science & AI",
#     "Developer, AI apps or physical AI":            "Data Science & AI",

                        "Data scientist or machine learning specialist": "Data Scientist / ML specialist",
                        "Data scientist":                                "Data Scientist / ML specialist",
                        
                        "Data engineer":                                 "Data Engineer",
                        "Engineer, data":                                "Data Engineer",

                        "Database administrator":                        "Database Administrator",
                        "Database administrator or engineer":            "Database Administrator",

                        "AI/ML engineer":                                "Data Science & AI",
                        "Developer, AI":                                 "Data Science & AI",
                        "Developer, AI apps or physical AI":             "Data Science & AI",

                        "Data or business analyst":                      "Data/Financial Analyst",
                        "Financial analyst or engineer":                 "Data/Financial Analyst",

                        "Developer, front-end":                          "Developer Software Engineering",
                        "Developer, full-stack":                         "Developer Software Engineering",
                        "Developer, game or graphics":                   "Developer Software Engineering",
                        "Developer, mobile":                             "Developer Software Engineering",
                        "Developer, desktop or enterprise applications": "Developer Software Engineering",
                        "Developer, back-end":                           "Developer Software Engineering",

                        "Developer Advocate":                            "Developer Community & Specialized",
                        "Blockchain":                                    "Developer Community & Specialized",

                        "Developer Experience":                          "Developer Platform & Infrastructure",
                        "Developer, QA or test":                         "Developer Platform & Infrastructure",
                        "Architect, software or solutions":              "Developer Platform & Infrastructure",


                        "Developer, embedded applications or devices":   "Developer Hardware & Systems",
                        "Hardware Engineer":                             "Developer Hardware & Systems",


                        # Management-Rollen
                        "Engineering manager":                          "Management",
                        "Product manager":                              "Management",
                        "Project manager":                              "Management",
                        "Senior Executive (C-Suite, VP, etc.)":         "Management",
                        "Senior executive (C-suite, VP, etc.)":         "Management",
                        "Senior executive/VP":                          "Management",
                        "Founder, technology or otherwise":             "Management",

                        # DevOps & Infrastruktur
                        "DevOps engineer or professional":              "DevOps & SRE",
                        "DevOps specialist":                            "DevOps & SRE",
                        "System administrator":                         "DevOps & SRE",
                        "Cloud infrastructure engineer":                "DevOps & SRE",
                        "Engineer, site reliability":                   "DevOps & SRE",

                        # Design 
                        "Designer":                                     "Designer",
                        "UX, Research Ops or UI design professional":   "Designer",

                        # Security 
                        "Cybersecurity or InfoSec professional":        "Security",
                        "Security professional":                        "Security",

                        # Research
                        "Academic researcher":                           "Research",
                        "Research & Development role":                   "Research",
                        "Scientist":                                     "Research",
                        "Applied scientist":                             "Research",

                        # Sonstiges
                        "Student":                                      "Student",

                        "Marketing or sales professional":              "Other",
                        "Support engineer or analyst":                  "Other",
                        "Other (please specify):":                      "Other",
                        "Unknown":                                      "Other",
                        "Educator":                                     "Other",
                        "Retired":                                      "Other",
}

# ── SO-Survey-Rollenname → Data-Rollenkategorie (für data_role_mapping) ───
data_role_mapping = {
    "Data scientist or machine learning specialist": "Data Scientist / ML specialist",
    "Data scientist":                               "Data Scientist / ML specialist",
    "Applied scientist":                            "Applied scientist",
    "Data engineer":                                "Data Engineer",
    "Engineer, data":                               "Data Engineer",
    "AI/ML engineer":                               "AI/ML Engineer",
    "Database administrator":                       "Database Administrator",
    "Database administrator or engineer":           "Database Administrator",
    "Data or business analyst":                     "Data Analyst",
    "Financial analyst or engineer":                "Financial Analyst",
    "Scientist":                                    "Scientist",
    "Developer, AI":                                "Data Science & AI",
    "Developer, AI apps or physical AI":            "Data Science & AI",
}

# ── Alle Rollen → Hauptkategorie (für enrich_devtype_features) ────────────
role_category_mapping = {
                        "Data scientist or machine learning specialist": "Data Scientist / ML specialist",
                        "Data scientist":                                "Data Scientist / ML specialist",
                        
                        "Data engineer":                                 "Data Engineer",
                        "Engineer, data":                                "Data Engineer",

                        "Database administrator":                        "Database Administrator",
                        "Database administrator or engineer":            "Database Administrator",

                        "AI/ML engineer":                                "Data Science & AI",
                        "Developer, AI":                                 "Data Science & AI",
                        "Developer, AI apps or physical AI":             "Data Science & AI",

                        "Data or business analyst":                      "Data/Financial Analyst",
                        "Financial analyst or engineer":                 "Data/Financial Analyst",

                        "Developer, front-end":                          "Developer Software Engineering",
                        "Developer, full-stack":                         "Developer Software Engineering",
                        "Developer, game or graphics":                   "Developer Software Engineering",
                        "Developer, mobile":                             "Developer Software Engineering",
                        "Developer, desktop or enterprise applications": "Developer Software Engineering",
                        "Developer, back-end":                           "Developer Software Engineering",

                        "Developer Advocate":                            "Developer Community & Specialized",
                        "Blockchain":                                    "Developer Community & Specialized",

                        "Developer Experience":                          "Developer Platform & Infrastructure",
                        "Developer, QA or test":                         "Developer Platform & Infrastructure",
                        "Architect, software or solutions":              "Developer Platform & Infrastructure",


                        "Developer, embedded applications or devices":   "Developer Hardware & Systems",
                        "Hardware Engineer":                             "Developer Hardware & Systems",


                        # Management-Rollen
                        "Engineering manager":                          "Management",
                        "Product manager":                              "Management",
                        "Project manager":                              "Management",
                        "Senior Executive (C-Suite, VP, etc.)":         "Management",
                        "Senior executive (C-suite, VP, etc.)":         "Management",
                        "Senior executive/VP":                          "Management",
                        "Founder, technology or otherwise":             "Management",

                        # DevOps & Infrastruktur
                        "DevOps engineer or professional":              "DevOps & SRE",
                        "DevOps specialist":                            "DevOps & SRE",
                        "System administrator":                         "DevOps & SRE",
                        "Cloud infrastructure engineer":                "DevOps & SRE",
                        "Engineer, site reliability":                   "DevOps & SRE",

                        # Design 
                        "Designer":                                     "Designer",
                        "UX, Research Ops or UI design professional":   "Designer",

                        # Security 
                        "Cybersecurity or InfoSec professional":        "Security",
                        "Security professional":                        "Security",

                        # Research
                        "Academic researcher":                           "Research",
                        "Research & Development role":                   "Research",
                        "Scientist":                                     "Research",
                        "Applied scientist":                             "Research",

                        # Sonstiges
                        "Student":                                      "Student",

                        "Marketing or sales professional":              "Other",
                        "Support engineer or analyst":                  "Other",
                        "Other (please specify):":                      "Other",
                        "Unknown":                                      "Other",
                        "Educator":                                     "Other",
                        "Retired":                                      "Other",
                        }


# ════════════════════════════════════════════════════════════════════════════
# 7. ADVISOR — Skill-Kategorien & Whitelists für DataCareerAdvisor
# ════════════════════════════════════════════════════════════════════════════

# ── Skill-Whitelists je Data-Rolle ────────────────────────────────────────
data_role_skills = {
    "Data Analyst": {
        # Programmiersprachen
        "Python", "SQL", "R", "VBA",
        # Visualisierung & BI
        "Tableau", "Power BI", "Looker", "Qlik", "Metabase",
        "Matplotlib", "Seaborn", "Plotly",
        "Excel", "Google Sheets",
        # Datenbanken
        "PostgreSQL", "MySQL", "Microsoft SQL Server",
        "BigQuery", "Snowflake", "MongoDB",
        # ML-Grundlagen
        "Pandas", "NumPy", "Scikit-Learn",
        # Tools & Orchestrierung
        "dbt", "Airflow", "Spark",
        # KI-Assistenten
        "OpenAI / ChatGPT", "Google Gemini", "GitHub Copilot",
    },
    "Data Scientist / ML specialist": {
        # Programmiersprachen
        "Python", "SQL", "R", "Scala", "Julia",
        # ML / Deep Learning
        "PyTorch", "TensorFlow", "Scikit-Learn", "Keras", "MLflow", "OpenCV",
        # Data-Libraries
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
        # Infrastruktur & Datenbanken
        "Spark", "Airflow", "dbt",
        "BigQuery", "Snowflake", "PostgreSQL", "MongoDB", "Redis",
        "AWS", "Google Cloud", "Microsoft Azure", "Docker",
        # KI-Tools
        "OpenAI / ChatGPT", "Claude", "Google Gemini", "GitHub Copilot",
    },
    "Data Engineer": {
        # Programmiersprachen
        "Python", "SQL", "Scala", "Java", "Bash/Shell/PowerShell",
        # Orchestrierung & ETL
        "Spark", "Airflow", "dbt", "Kafka",
        # Datenbanken
        "BigQuery", "Snowflake", "PostgreSQL", "MySQL",
        "Microsoft SQL Server", "MongoDB", "Redis",
        "Cassandra", "Elasticsearch", "DynamoDB",
        # Cloud & Infrastruktur
        "AWS", "Google Cloud", "Microsoft Azure",
        "Docker", "Kubernetes", "Terraform", "Ansible",
    },
    "Database Administrator": {
        # Programmiersprachen
        "SQL", "Python", "Bash/Shell/PowerShell",
        # Datenbanken
        "PostgreSQL", "MySQL", "Microsoft SQL Server", "Oracle",
        "MongoDB", "Redis", "Cassandra", "Elasticsearch",
        # Cloud & Infrastruktur
        "AWS", "Google Cloud", "Microsoft Azure", "Docker",
    },
    "AI/ML Engineer": {
        # Programmiersprachen
        "Python", "Scala", "Julia", "Rust",
        # ML / Deep Learning
        "PyTorch", "TensorFlow", "Scikit-Learn", "Keras", "MLflow", "OpenCV",
        # Infrastruktur
        "Spark", "Airflow", "Docker", "Kubernetes",
        "AWS", "Google Cloud", "Microsoft Azure",
        # Datenbanken
        "BigQuery", "Snowflake", "PostgreSQL", "MongoDB",
        # KI-Tools
        "OpenAI / ChatGPT", "Claude", "Google Gemini", "GitHub Copilot",
    },
    "Applied scientist": {
        # Programmiersprachen
        "Python", "R", "SQL", "Scala", "Julia", "Matlab",
        # ML / Deep Learning
        "PyTorch", "TensorFlow", "Scikit-Learn", "Keras", "MLflow",
        # Data-Libraries
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
        # Infrastruktur
        "Spark", "AWS", "Google Cloud", "Microsoft Azure", "Docker",
    },
    "Financial Analyst": {
        # Programmiersprachen
        "Python", "SQL", "R", "VBA",
        # BI & Tabellenkalkulation
        "Excel", "Google Sheets", "Power BI", "Tableau", "Looker",
        # Datenbanken
        "PostgreSQL", "MySQL", "Microsoft SQL Server",
        # Data-Libraries
        "Pandas", "NumPy", "Matplotlib", "Plotly",
        # KI-Tools
        "OpenAI / ChatGPT", "GitHub Copilot",
    },
    "Scientist": {
        # Programmiersprachen
        "Python", "R", "SQL", "Julia", "Matlab",
        # ML / Deep Learning
        "PyTorch", "TensorFlow", "Scikit-Learn", "Keras",
        # Data-Libraries
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
        # Infrastruktur
        "AWS", "Google Cloud", "Docker",
    },
}

# ── Vereinigung aller Skill-Whitelists (Fallback für unbekannte Rollen) ───
all_data_skills = set().union(*data_role_skills.values())

# ── Skill-Kategorisierung für _build_profile_row ─────────────────────────
lang_known = {
    # уже есть
    "Python", "SQL", "R", "Java", "C++", "Go", "Rust", "Scala",
    "TypeScript", "JavaScript", "Bash/Shell/PowerShell", "HTML/CSS",
    "PHP", "C#", "Kotlin", "Swift", "Ruby", "VBA", "Dart", "Matlab",
    "LISP", "COBOL", "Perl", "Julia", "Haskell", "Groovy",
}

db_known = {
    # уже есть + добавить
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Snowflake", "BigQuery",
    "Elasticsearch", "DynamoDB", "SQLite", "Microsoft SQL Server",
    "Oracle", "Cassandra", "CockroachDB", "Neo4J", "Firebase",
}

plat_known = {
    # уже есть + добавить
    "AWS", "Google Cloud", "Microsoft Azure", "Docker", "Kubernetes",
    "Terraform", "Heroku", "DigitalOcean", "Ansible",
    "Linode, now Akamai",
}

web_known = {
    # уже есть + добавить
    "FastAPI", "Flask", "Django", "Streamlit", "React", "Angular",
    "Vue.js", "Node.js", "Spring Framework", "ASP.NET Core",
    "Next.js", "Express",                      
}

tech_known = {
    # Data/ML — уже есть
    "Scikit-Learn", "TensorFlow", "PyTorch", "Pandas", "NumPy",
    "Matplotlib", "Seaborn", "Plotly", "OpenCV", "MLflow", "Keras",
    # BI
    "Tableau", "Power BI", "Looker",
    # Data Engineering — добавить
    "Spark", "Airflow", "dbt", "Kafka",      
}

ai_known = {
    # уже есть
    "OpenAI / ChatGPT", "Claude", "Google Gemini", "GitHub Copilot",
    "DeepSeek", "Meta AI", "Perplexity AI", "Tabnine", "Codeium",
}

# ── Währungen je Land (Referenz für DataCareerAdvisor) ────────────────────
country_currency = {
    "Germany":        "EUR European Euro",
    "France":         "EUR European Euro",
    "Netherlands":    "EUR European Euro",
    "Spain":          "EUR European Euro",
    "Italy":          "EUR European Euro",
    "Poland":         "EUR European Euro",
    "Switzerland":    "CHF Swiss Franc",
    "United Kingdom": "GBP British Pound",
    "United States":  "USD US Dollar",
    "Canada":         "CAD Canadian Dollar",
    "Australia":      "AUD Australian Dollar",
    "India":          "INR Indian Rupee",
    "Brazil":         "BRL Brazilian Real",
    "Japan":          "JPY Japanese Yen",
}
