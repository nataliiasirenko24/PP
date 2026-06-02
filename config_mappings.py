# ── Схема колонок по годам ─────────────────────────────────────────────────
# Перенесено из ноутбука: canonical → оригинальное имя в конкретном году
# None = колонка отсутствует в данном году

schema = {yr: dict(
    salary     = 'ConvertedCompYearly' if yr >= 2021 else 'ConvertedComp',
    currency   = 'Currency' if yr >= 2021 else 'CurrencyDesc',

    # Демография и базовый профиль
    country    = 'Country',
    work_exp   = 'WorkExp' if yr >= 2022 else None,
    years_code = 'YearsCode',
    remote     = 'RemoteWork' if yr >= 2022 else None,

    # Профессиональный трек
    branch     = 'MainBranch',
    devtype    = 'DevType',
    education  = 'EdLevel',
    employment = 'Employment',
    industry   = 'Industry' if yr >= 2022 else None,
    org_size   = 'OrgSize',
    icorpm     = 'ICorPM' if yr >= 2022 else None,

    # Хард-стек (мульти-выбор)
    language_have = 'LanguageHaveWorkedWith' if yr >= 2021 else 'LanguageWorkedWith',
    language_entry = 'LanguagesHaveEntry' if yr >= 2021 else None,

    database_have = 'DatabaseHaveWorkedWith' if yr >= 2021 else 'DatabaseWorkedWith', 
    database_entry = 'DatabaseHaveEntry' if yr >= 2021 else None, 

    platform_have = 'PlatformHaveWorkedWith' if yr >= 2021 else 'PlatformWorkedWith',
    platform_entry = 'PlatformHaveEntry' if yr == 2025 else None,

    webframe_have = 'WebframeHaveWorkedWith' if yr >= 2021 else 'WebframeWorkedWith',
    webframe_entry = 'WebframeHaveEntry' if yr == 2025 else None,

    tech_have       = ('SOTagsHaveWorkedWith' if yr >= 2025 else
                       'MiscTechHaveWorkedWith' if yr >= 2021 else
                       'MiscTechWorkedWith' if yr == 2020 else None),
    tech_entry       = ('SOTagsHaveWorkedWith' if yr == 2025 else None),

    ai_have = ('AIModelsHaveWorkedWith' if yr >= 2025 else
                  'AISearchDevHaveWorkedWith' if yr == 2024 else
                  'AISearchHaveWorkedWith' if yr == 2023 else None),
    ai_entry = ('AIModelsWantEntry' if yr == 2025 else None),
    
    ai_select  = 'AISelect' if yr >= 2023 else None,
    ai_agents  = 'AIAgentExternal' if yr >= 2025 else None,
) for yr in range(2020, 2026)}


# data_role_mapping = [
#     ("Data Scientist / ML", [
#         "Data scientist or machine learning specialist",
#         "AI/ML engineer", "Applied scientist", "Data scientist",
#     ]),
#     ("Data Engineer", [
#         "Engineer, data", "Data engineer",
#         "Cloud infrastructure engineer",
#     ]),
#     ("Data / Business Analyst", [
#         "Data or business analyst",
#         "Financial analyst or engineer",
#     ]),
#     ("Database Admin", [
#         "Database administrator",
#         "Database administrator or engineer",
#     ]),
#     ("Research / Scientist", [
#         "Academic researcher", "Scientist",
#         "Research & Development role",
#     ]),
# ]

data_role_mapping = {
    'Data scientist or machine learning specialist': 'Data Scientist / ML specialist',
    'Data scientist': 'Data Scientist / ML specialist',
    'Applied scientist': 'Applied scientist',
    'Data engineer': 'Data Engineer',
    'Engineer, data': 'Data Engineer',
    'AI/ML engineer': 'AI/ML Engineer',
    'Database administrator': 'Database Administrator',
    'Database administrator or engineer': 'Database Administrator',
    'Data or business analyst': 'Data Analyst',
    'Financial analyst or engineer': 'Financial Analyst', 
    'Scientist': 'Scientist'}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# country_mapping
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

country_mapping = {
    'United States of America': 'United States',
    'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
    'Russian Federation': 'Russia',
    'Iran, Islamic Republic of...': 'Iran',
    'Republic of Korea': 'South Korea',
    'North Korea': 'South Korea',
    'Venezuela, Bolivarian Republic of...': 'Venezuela',
    'The former Yugoslav Republic of Macedonia': 'Republic of North Macedonia',
    'Republic of North Macedonia': 'North Macedonia',
    'Republic of Moldova': 'Moldova',
    'Syrian Arab Republic': 'Syria',
    'Viet Nam': 'Vietnam',
    'United Republic of Tanzania': 'Tanzanian shilling',
    'Congo, Republic of the...': 'Republic of the Congo',
    'Democratic Republic of the Congo': 'Democratic Republic of the Congo',
    'Libyan Arab Jamahiriya': 'Libya'
}

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# remote_mapping
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

remote_mapping = {
    # Удаленка
    'Fully remote': 'Remote',
    'Remote': 'Remote',
    
    # Гибрид
    'Hybrid (some remote, some in-person)': 'Hybrid',
    'Hybrid (some remote, leans heavy to in-person)': 'Hybrid',
    'Hybrid (some in-person, leans heavy to flexibility)': 'Hybrid',
    'Your choice (very flexible, you can come in when you want or just as needed)': 'Hybrid',
    
    # Офис
    'In-person': 'On-site',
    'Full in-person': 'On-site',

    # Unknown
    'Unknown': 'Unknown'
}


branch_mapping = {
    # Профессиональные разработчики
    'I am a developer by profession': 'Professional',
    
    # Те, кто пишет код как часть другой работы или учебы
    'I am not primarily a developer, but I write code sometimes as part of my work': 'Coding at Work/Studies',
    'I am not primarily a developer, but I write code sometimes as part of my work/studies': 'Coding at Work/Studies',
    'I am a student who is learning to code': 'Coding at Work/Studies',
    
    # Other
    'I work with developers or my work supports developers but am not a developer by profession': 'Other',
    'I used to be a developer by profession, but no longer am': 'Other',
    'I am learning to code': 'Other',
    'I code primarily as a hobby': 'Other',
    'Unknown': 'Other'
}

education_mapping = {
    'Other doctoral degree (Ph.D., Ed.D., etc.)': 'PhD',
    'Professional degree (JD, MD, Ph.D, Ed.D, etc.)': 'PhD',
    
    'Master’s degree (M.A., M.S., M.Eng., MBA, etc.)': 'Master',
    'Professional degree (JD, MD, etc.)': 'Master',
    
    'Bachelor’s degree (B.A., B.S., B.Eng., etc.)': 'Bachelor',
    
    'Some college/university study without earning a degree': 'College / Undergrad',
    'Associate degree (A.A., A.S., etc.)': 'College / Undergrad',
    
    # Ранг 1: Школа (Средняя или Начальная)
    'Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)': 'School',
    'Primary/elementary school': 'School',
    
    # Ранг 0: Без образования и пропуски
    'I never completed any formal education': 'Other',
    'Something else': 'Other',
    'Other (please specify):': 'Other',
    'Unknown': 'Other'
}

education_rank_mapping = {
    'PhD': 5,
    'Master': 4,
    'Bachelor': 3,
    'College / Undergrad': 2,
    'School': 1,
    'Other': 0
}

industry_mapping = {
    # --- Блок TECH ---
    "Information Services, IT, Software Development, or other Technology": "IT, Telecom & Tech",
    "Software Development": "IT, Telecom & Tech",
    "Internet, Telecomm or Information Services": "IT, Telecom & Tech",
    "Computer Systems Design and Services": "IT, Telecom & Tech",
    # --- Блок ФИНАНСЫ ---
    "Financial Services": "Banking, Finance & Insurance",
    "Banking/Financial Services": "Banking, Finance & Insurance",
    "Fintech": "Banking, Finance & Insurance",
    "Insurance": "Banking, Finance & Insurance",
    # --- МЕДИЦИНА И ОБРАЗОВАНИЕ ---
    "Healthcare": "Healthcare & Medicine",
    "Higher Education": "Education",
    # --- РЕАЛЬНЫЙ СЕКТОР, РИТЕЙЛ И ГОСУДАРСТВО ---
    "Retail and Consumer Services": "Retail & Consumer Services",
    "Government": "Government & Public Sector",
    "Manufacturing, Transportation, or Supply Chain": "Manufacturing, Logistics & Supply Chain",
    "Manufacturing": "Manufacturing, Logistics & Supply Chain",
    "Transportation, or Supply Chain": "Manufacturing, Logistics & Supply Chain",
    "Energy": "Energy & Utilities",
    "Oil & Gas": "Energy & Utilities",
    "Media & Advertising Services": "Media & Advertising",
    "Advertising Services": "Media & Advertising",
    "Wholesale": "Wholesale & Trade",
    "Legal Services": "Legal Services",
    # --- ПРОПУСКИ И ДРУГОЕ (РАЗДЕЛЯЕМ ИХ!) ---
    "Other": "Other",
    "Other:": "Other",
    "Unknown": "Unknown", 
}

# 1. Порядковый ранк размера компании (для XGBoost / CatBoost)
org_size_mapping = {
    '10,000 or more employees': '10k+',
    '5,000 to 9,999 employees': 'Large 2 (5-9k)',
    '1,000 to 4,999 employees': 'Large 1 (1-5k)',
    '500 to 999 employees': 'Medium 2 (500-999)',
    '100 to 499 employees': 'Medium 1 (100-499)',
    '20 to 99 employees': 'Small (20-99)',
    '10 to 19 employees': 'Micro (2-19)',
    '2 to 9 employees': 'Micro (2-19)',
    'Less than 20 employees': 'Micro (2-19)',
    'Just me - I am a freelancer, sole proprietor, etc.': 'Feelancer (1)',
    'I don’t know': 'Other',
    'Unknown': 'Other'
}

# 2. Текстовые группы для One-Hot Encoding (для Линейной регрессии)
org_size_rank_mapping = {
    '10k+': 9,
    'Large 2 (5-9k)': 8,
    'Large 1 (1-5k)': 7,
    'Medium 2 (500-999)': 6,
    'Medium 1 (100-499)': 5,
    'Small (20-99)': 3,
    'Micro (2-19)': 2,
    'Feelancer (1)': 1,
    'Other': 0
}

icorpm_mapping = {
    'Individual contributor': 'IC',
    'Independent contributor': 'IC',
    'People manager': 'Manager',
    'Unknown': 'Unknown'
}

platform_mapping = {
    'amazon web services (aws)': 'AWS',
    'aws': 'AWS',
    'google cloud platform': 'Google Cloud',
    'google cloud': 'Google Cloud',
    'microsoft azure': 'Microsoft Azure',
    'azure': 'Microsoft Azure'
}

ai_select_mapping = {
    'Yes': 'Yes',
    'Yes, I use AI tools daily': 'Yes',
    'Yes, I use AI tools weekly': 'Yes',
    'Yes, I use AI tools monthly or infrequently': 'Yes',
    "No, and I don't plan to": 'No',
    'No, but I plan to soon': 'No',
    'Unknown': 'Unknown'
}


language_mapping  = {
    'Bash/Shell':                'Bash/Shell/PowerShell',
    'PowerShell':                'Bash/Shell/PowerShell',
    'Bash/Shell (all shells)':   'Bash/Shell/PowerShell',
    'MATLAB':                    'Matlab',
    'LISP':                      'Lisp',
    'COBOL':                     'Cobol',
    'Objective C': 'Objective-C',
    'clojure': 'Clojure',
    'Clojure, ClojureScript': 'Clojure',
    'haskell': 'Haskell',
    'nix': 'Nix',
    'Visual Basic (.Net)': 'VBA',
    'Unknown':'Other'
}

# Маппинг для колонки 'database' 
database_mapping= {
    'sqlite': 'SQLite',
    'Dynamodb': 'DynamoDB',
    'Couch DB': 'CouchDB',
    'Couchbase': 'CouchDB',
    'Firebase Realtime Database': 'Firebase',
    'Cloud Firestore': 'Firebase',
    'FirebirdSQL': 'Firebird',
    'firebird': 'Firebird',
    'Firebird SQL': 'Firebird',
    'Neo4j': 'Neo4J',
    'Azure SQL': 'SQL Server',
    'Microsoft SQL Server': 'SQL Server',
    'Opensearch': 'OpenSearch',
    'RavenDb': 'RavenDB',
    'neon': 'Neon', 
    'SAP HANA': 'HANA',
    'Cockroachdb': 'CockroachDB',
  
}


platform_mapping = {
    'Amazon Web Services (AWS)': 'AWS',
    'Google Cloud Platform': 'Google Cloud',
    'Digital Ocean': 'DigitalOcean',
    'Linode, now Akamai': 'Linode', 
    'Oracle Cloud Infrastructure (OCI)': 'Oracle Cloud',
    'Oracle Cloud Infrastructure': 'Oracle Cloud',
    'IBM Cloud or Watson': 'IBM Cloud', 
    'IBM Cloud Or Watson': 'IBM Cloud', 
    'fly.io': 'Fly.io',
    'Podman': 'Docker',
    'conda': 'Conda',
    'nix': 'Nix',
    'cmake': 'CMake',
    'uv': 'UV',
    'Uv': 'UV',
    'helm': 'Helm'
}


webframe_mapping = {
    "React.js": "React",
    "ASP.NET CORE": "ASP.NET Core",
    "Angular.js": "Angular",
    "AngularJS": "Angular",
    "Spring Boot": "Spring Framework" 
}
tech_map = {
    r'.NET.*': '.NET',
    r'Scikit-learn.*': 'Scikit-Learn',
    r'Torch.*': 'PyTorch',
    r'Teraform': 'Terraform',
    # и т.д.
}

tech_mapping = {
    # Объединение семейства .NET
    '.NET Framework': '.NET',
    '.NET Core / .NET 5': '.NET',
    '.NET Core': '.NET',
    '.NET (5+)': '.NET',
    '.NET Framework (1.0 - 4.8)': '.NET',
    '.NET MAUI': '.NET',
    '.NET 8 or higher': '.NET',
    'Torch/PyTorch': 'Torch',
    'Scikit-learn': 'Scikit-Learn',
    'Opencv': 'OpenCV',
    'Spring Framework': 'Spring'
}

ai_mapping = {
    # OpenAI
    "openAI GPT (chatbot models)": "OpenAI / ChatGPT",
    "openAI Reasoning models": "OpenAI / ChatGPT",
    "openAI Image generating models": "OpenAI / ChatGPT",
    "OpenAI Codex": "OpenAI / ChatGPT",
    "ChatGPT": "OpenAI / ChatGPT",
    
    # Google
    "Google Bard AI": "Google Gemini",
    "Gemini (Flash general purpose models)": "Google Gemini",
    "Gemini (Pro Reasoning models)": "Google Gemini",
    
    # Anthropic
    "Anthropic: Claude Sonnet": "Claude",
    
    # DeepSeek
    "DeepSeek (R- Reasoning models)": "DeepSeek",
    "DeepSeek (V- General purpose models)": "DeepSeek",
    
    # Perplexity
    "Perplexity Sonar models": "Perplexity AI",
    
    # Meta
    "Meta Llama (all models)": "Meta AI"
}


region_mapping = {
    # ── США / Канада ──────────────────────────────────────────────
    "United States":                    "North America",
    "United States of America":         "North America",  # дубль
    "Canada":                           "North America",

    # ── UK ────────────────────────────────────────────────────────
    "United Kingdom":                                    "UK",
    "United Kingdom of Great Britain and Northern Ireland": "UK",  # дубль
    "Ireland":                          "UK",
    "Isle of Man":                      "UK",

    # ── DACH ──────────────────────────────────────────────────────
    "Germany":                          "DACH",
    "Switzerland":                      "DACH",
    "Austria":                          "DACH",
    "Liechtenstein":                    "DACH",

    # ── Nordics ───────────────────────────────────────────────────
    "Sweden":                           "Nordics",
    "Norway":                           "Nordics",
    "Denmark":                          "Nordics",
    "Finland":                          "Nordics",
    "Iceland":                          "Nordics",
    "Estonia":                          "Nordics",
    "Latvia":                           "Nordics",
    "Lithuania":                        "Nordics",

    # ── W_Europe ──────────────────────────────────────────────────
    "France":                           "W_Europe",
    "Netherlands":                      "W_Europe",
    "Belgium":                          "W_Europe",
    "Spain":                            "W_Europe",
    "Italy":                            "W_Europe",
    "Portugal":                         "W_Europe",
    "Luxembourg":                       "W_Europe",
    "Monaco":                           "W_Europe",
    "Andorra":                          "W_Europe",
    "San Marino":                       "W_Europe",
    "Malta":                            "W_Europe",

    # ── E_Europe ──────────────────────────────────────────────────
    "Poland":                           "E_Europe",
    "Czech Republic":                   "E_Europe",
    "Slovakia":                         "E_Europe",
    "Hungary":                          "E_Europe",
    "Romania":                          "E_Europe",
    "Bulgaria":                         "E_Europe",
    "Slovenia":                         "E_Europe",
    "Croatia":                          "E_Europe",
    "Serbia":                           "E_Europe",
    "Bosnia and Herzegovina":           "E_Europe",
    "Montenegro":                       "E_Europe",
    "Kosovo":                           "E_Europe",
    "Albania":                          "E_Europe",
    "Greece":                           "E_Europe",
    "Cyprus":                           "E_Europe",
    "Ukraine":                          "E_Europe",
    "Belarus":                          "E_Europe",
    "Republic of Moldova":              "E_Europe",
    "Moldova":                          "E_Europe",
    "Republic of North Macedonia":      "E_Europe",
    "The former Yugoslav Republic of Macedonia": "E_Europe",

    # ── CIS ───────────────────────────────────────────────────────
    "Russian Federation":               "CIS",
    "Kazakhstan":                       "CIS",
    "Azerbaijan":                       "CIS",
    "Armenia":                          "CIS",
    "Georgia":                          "CIS",
    "Uzbekistan":                       "CIS",
    "Kyrgyzstan":                       "CIS",
    "Tajikistan":                       "CIS",
    "Turkmenistan":                     "CIS",

    # ── Middle East ───────────────────────────────────────────────
    "Israel":                           "Middle East",
    "Turkey":                           "Middle East",
    "United Arab Emirates":             "Middle East",
    "Saudi Arabia":                     "Middle East",
    "Kuwait":                           "Middle East",
    "Qatar":                            "Middle East",
    "Bahrain":                          "Middle East",
    "Oman":                             "Middle East",
    "Jordan":                           "Middle East",
    "Lebanon":                          "Middle East",
    "Iraq":                             "Middle East",
    "Iran":                             "Middle East",
    "Iran, Islamic Republic of...":     "Middle East",
    "Palestine":                        "Middle East",
    "Syrian Arab Republic":             "Middle East",
    "Yemen":                            "Middle East",

    # ── India ─────────────────────────────────────────────────────
    "India":                            "India",

    # ── East Asia ─────────────────────────────────────────────────
    "China":                            "East Asia",
    "Japan":                            "East Asia",
    "Republic of Korea":                "East Asia",
    "South Korea":                      "East Asia",
    "Hong Kong (S.A.R.)":               "East Asia",
    "Taiwan":                           "East Asia",
    "Mongolia":                         "East Asia",
    "North Korea":                                  "East Asia",
    "Democratic People's Republic of Korea":        "East Asia",

    # ── SE Asia ───────────────────────────────────────────────────
    "Singapore":                        "SE Asia",
    "Malaysia":                         "SE Asia",
    "Indonesia":                        "SE Asia",
    "Philippines":                      "SE Asia",
    "Viet Nam":                         "SE Asia",
    "Thailand":                         "SE Asia",
    "Myanmar":                          "SE Asia",
    "Cambodia":                         "SE Asia",
    "Sri Lanka":                        "SE Asia",
    "Bangladesh":                       "SE Asia",
    "Nepal":                            "SE Asia",
    "Pakistan":                         "SE Asia",
    "Afghanistan":                      "SE Asia",
    "Maldives":                         "SE Asia",
    "Bhutan":                           "SE Asia",
    "Lao People's Democratic Republic": "SE Asia",
    "Brunei Darussalam":                "SE Asia",
    "Timor-Leste":                      "SE Asia",

    # ── Latin America ─────────────────────────────────────────────
    "Brazil":                           "Latin America",
    "Mexico":                           "Latin America",
    "Argentina":                        "Latin America",
    "Colombia":                         "Latin America",
    "Chile":                            "Latin America",
    "Peru":                             "Latin America",
    "Venezuela, Bolivarian Republic of...": "Latin America",
    "Ecuador":                          "Latin America",
    "Uruguay":                          "Latin America",
    "Bolivia":                          "Latin America",
    "Paraguay":                         "Latin America",
    "Panama":                           "Latin America",
    "Costa Rica":                       "Latin America",
    "Guatemala":                        "Latin America",
    "Honduras":                         "Latin America",
    "El Salvador":                      "Latin America",
    "Nicaragua":                        "Latin America",
    "Dominican Republic":               "Latin America",
    "Cuba":                             "Latin America",
    "Haiti":                            "Latin America",
    "Jamaica":                          "Latin America",
    "Trinidad and Tobago":              "Latin America",
    "Bahamas":                          "Latin America",
    "Barbados":                         "Latin America",
    "Guyana":                           "Latin America",
    "Suriname":                         "Latin America",
    "Grenada":                          "Latin America",
    "Saint Vincent and the Grenadines": "Latin America",
    "Saint Lucia":                      "Latin America",
    "Saint Kitts and Nevis":            "Latin America",
    "Dominica":                         "Latin America",
    "Antigua and Barbuda":              "Latin America",
    "Belize":                           "Latin America",

    # ── Africa ────────────────────────────────────────────────────
    "Nigeria":                          "Africa",
    "South Africa":                     "Africa",
    "Kenya":                            "Africa",
    "Ghana":                            "Africa",
    "Egypt":                            "Africa",
    "Morocco":                          "Africa",
    "Tunisia":                          "Africa",
    "Algeria":                          "Africa",
    "Ethiopia":                         "Africa",
    "Tanzania":                         "Africa",
    "United Republic of Tanzania":      "Africa",
    "Uganda":                           "Africa",
    "Cameroon":                         "Africa",
    "Senegal":                          "Africa",
    "Côte d'Ivoire":                    "Africa",
    "Democratic Republic of the Congo": "Africa",
    "Congo, Republic of the...":        "Africa",
    "Rwanda":                           "Africa",
    "Zambia":                           "Africa",
    "Zimbabwe":                         "Africa",
    "Mozambique":                       "Africa",
    "Madagascar":                       "Africa",
    "Sudan":                            "Africa",
    "Somalia":                          "Africa",
    "Namibia":                          "Africa",
    "Botswana":                         "Africa",
    "Swaziland":                        "Africa",
    "Angola":                           "Africa",
    "Libyan Arab Jamahiriya":           "Africa",
    "Mauritius":                        "Africa",
    "Togo":                             "Africa",
    "Benin":                            "Africa",
    "Malawi":                           "Africa",
    "Guinea":                           "Africa",
    "Guinea-Bissau":                    "Africa",
    "Gambia":                           "Africa",
    "Niger":                            "Africa",
    "Mali":                             "Africa",
    "Burkina Faso":                     "Africa",
    "Mauritania":                       "Africa",
    "Djibouti":                         "Africa",
    "Cape Verde":                       "Africa",
    "Lesotho":                          "Africa",
    "Gabon":                            "Africa",

    # ── Oceania ───────────────────────────────────────────────────
    "Australia":                        "Oceania",
    "New Zealand":                      "Oceania",
    "Fiji":                             "Oceania",
    "Papua New Guinea":                 "Oceania",
    "Samoa":                            "Oceania",
    "Palau":                            "Oceania",

    # ── Прочее ────────────────────────────────────────────────────
    "Nomadic":                          "Other",
}
