"""
Curated Ground-Truth Datasets for FinLens AI Evaluation & Benchmarking.
Contains labeled test sets for:
1. Merchant Normalization (raw POS/statement strings -> canonical merchant name)
2. Transaction Categorization (merchant + description + amount -> Category & Transaction Type)
3. AI Agent Tool Selection & Grounding (natural language queries in EN & ZH -> expected tool call)
"""

# ============================================================
# 1. Merchant Normalization Ground Truth Dataset (30+ test cases)
# ============================================================
MERCHANT_BENCHMARK_DATA = [
    # Fast food & Coffee
    ("TST* TIM HORTONS #1024 VANCOUVER BC", "Tim Hortons"),
    ("TIM HORTONS 4921 TORONTO ON", "Tim Hortons"),
    ("STARBUCKS STORE 04829 SEATTLE WA", "Starbucks"),
    ("SQ *STARBUCKS COFFEE MONTREAL QC", "Starbucks"),
    ("MCDONALDS #2183 CALGARY AB", "McDonald's"),
    ("MCDONALD'S RESTAURANT OTTAWA ON", "McDonald's"),
    ("SUBWAY #12903 BURNABY BC", "Subway"),
    # Delivery & Rideshare
    ("UBER *EATS PENDING", "Uber Eats"),
    ("UBER *TRIP VANCOUVER BC", "Uber"),
    ("LYFT *RIDE 09-12 SAN FRANCISCO CA", "Lyft"),
    ("DOORDASH*BURGERKING WWW.DOORDASH.COM", "DoorDash"),
    ("SKIPTHEDISHES WINNIPEG MB", "SkipTheDishes"),
    # Groceries & Retail
    ("LOBLAWS STORE 1029 TORONTO ON", "Loblaws"),
    ("SAFEWAY FUEL #4928 SURREY BC", "Safeway"),
    ("WHOLE FOODS MKT 10293 VANCOUVER BC", "Whole Foods"),
    ("COSTCO WHOLESALE #258 BURNABY BC", "Costco"),
    ("WALMART STORE #3104 MISSISSAUGA ON", "Walmart"),
    ("METRO INC #583 MONTREAL QC", "Metro"),
    ("SOBEYS 0294 EDMONTON AB", "Sobeys"),
    # Tech & Subscriptions
    ("AMZN Mktp CA*9812487 SEATTLE WA", "Amazon"),
    ("AMAZON.CA*294829 SEATTLE WA", "Amazon"),
    ("APPLE.COM/BILL 866-712-7753 CA", "Apple"),
    ("NETFLIX.COM LOS GATOS CA", "Netflix"),
    ("SPOTIFY PENDING STOCKHOLM SE", "Spotify"),
    ("GOOGLE *SERVICES G.CO/HELPPAY# CA", "Google"),
    ("OPENAI *CHATGPT SUBSCRIPTION", "OpenAI"),
    ("GITHUB *SPONSOR/PRO SAN FRANCISCO CA", "GitHub"),
    ("MICROSOFT*STORE MSFT.COM/BILL WA", "Microsoft"),
    # Utilities & Telecom
    ("BC HYDRO PAYMENT VANCOUVER BC", "BC Hydro"),
    ("TORONTO HYDRO ELEC BILL", "Toronto Hydro"),
    ("ENBRIDGE GAS DISTRIBUTION", "Enbridge Gas"),
    ("TELUS MOBILITY AUTO-PAY", "Telus"),
    ("ROGERS WIRELESS DIRECT DEBIT", "Rogers"),
    ("BELL MOBILITY BILL PAYMENT", "Bell"),
    # Gas Stations
    ("SHELL OIL 57442291 VANCOUVER BC", "Shell"),
    ("CHEVRON 0029384 RICHMOND BC", "Chevron"),
    ("ESSO GAS BAR 0492 TORONTO ON", "Esso"),
    ("PETRO-CANADA #10928 CALGARY AB", "Petro-Canada"),
    # Travel
    ("AIR CANADA 014294829 MONTREAL QC", "Air Canada"),
    ("WESTJET 83829482 CALGARY AB", "WestJet"),
    ("AIRBNB *HM9428SF SAN FRANCISCO CA", "Airbnb"),
]


# ============================================================
# 2. Transaction Categorization Ground Truth Dataset (35+ test cases)
# ============================================================
CATEGORIZATION_BENCHMARK_DATA = [
    # (Merchant, Raw Description, Amount, Expected Category, Expected Type)
    ("Tim Hortons", "TST* TIM HORTONS #1024", "-4.85", "Food", "expense"),
    ("Starbucks", "STARBUCKS STORE 04829", "-6.45", "Food", "expense"),
    ("McDonald's", "MCDONALDS #2183", "-14.20", "Food", "expense"),
    ("Uber Eats", "UBER *EATS PENDING", "-34.50", "Food", "expense"),
    ("Whole Foods", "WHOLE FOODS MKT 10293", "-112.40", "Food", "expense"),
    ("Loblaws", "LOBLAWS STORE 1029", "-86.75", "Food", "expense"),
    ("Uber", "UBER *TRIP VANCOUVER BC", "-24.50", "Transportation", "expense"),
    ("Shell", "SHELL OIL 57442291", "-65.00", "Transportation", "expense"),
    ("Chevron", "CHEVRON 0029384", "-72.10", "Transportation", "expense"),
    ("TransLink", "TRANSIT METRO PASS", "-140.00", "Transportation", "expense"),
    ("Impark", "PARKING LOT 294", "-15.00", "Transportation", "expense"),
    ("Amazon", "AMZN Mktp CA*9812487", "-89.99", "Shopping", "expense"),
    ("Costco", "COSTCO WHOLESALE #258", "-245.80", "Shopping", "expense"),
    ("Best Buy", "BEST BUY BURNABY BC", "-289.00", "Shopping", "expense"),
    ("IKEA", "IKEA COQUITLAM BC", "-180.50", "Shopping", "expense"),
    ("OpenAI", "OPENAI *CHATGPT SUBSCRIPTION", "-27.00", "Shopping", "expense"),
    ("GitHub", "GITHUB *PRO ACCOUNT", "-10.00", "Shopping", "expense"),
    ("Netflix", "NETFLIX.COM LOS GATOS", "-19.99", "Entertainment", "expense"),
    ("Spotify", "SPOTIFY PENDING", "-11.99", "Entertainment", "expense"),
    ("Steam", "STEAM PURCHASE GAMES", "-59.99", "Entertainment", "expense"),
    ("Cineplex", "CINEMA MOVIE TICKETS", "-32.00", "Entertainment", "expense"),
    ("BC Hydro", "BC HYDRO ELECTRIC UTILITY", "-85.10", "Utilities", "expense"),
    ("Enbridge Gas", "ENBRIDGE GAS PAYMENT", "-64.30", "Utilities", "expense"),
    ("Telus", "TELUS MOBILITY AUTO-PAY", "-95.00", "Utilities", "expense"),
    ("Rogers", "ROGERS INTERNET MONTHLY", "-89.00", "Utilities", "expense"),
    ("Property Mgmt", "RENT PAYMENT PROPERTY MGMT", "-1450.00", "Housing", "expense"),
    ("Mortgage Corp", "MORTGAGE BIWEEKLY PAYMENT", "-1200.00", "Housing", "expense"),
    ("Shoppers Drug Mart", "SHOPPERS DRUG MART #291", "-28.40", "Healthcare", "expense"),
    ("Dental Clinic", "DENTAL HYGIENE CLINIC", "-185.00", "Healthcare", "expense"),
    ("Air Canada", "AIR CANADA FLIGHT BOOKING", "-540.00", "Travel", "expense"),
    ("Airbnb", "AIRBNB *HM9428SF RESERVATION", "-320.00", "Travel", "expense"),
    ("RBC Royal Bank", "SERVICE CHARGE MONTHLY FEE", "-16.95", "Financial", "expense"),
    # Incomes & Transfers
    ("Payroll / Salary", "ACME CORP PAYROLL DIRECT DEP", "3200.00", "Income", "income"),
    ("Employer Inc", "SALARY PAYMENT OCTOBER", "2850.00", "Income", "income"),
    ("Investment Dividend", "DIVIDEND DISTRIBUTION ETF", "84.50", "Income", "income"),
    ("Interac e-Transfer", "INTERAC E-TRANSFER FROM ALICE", "-50.00", "Transfer", "transfer"),
    ("Credit Card", "PAYMENT - THANK YOU / PAIEMENT", "-200.00", "Transfer", "transfer"),
]


# ============================================================
# 3. AI Agent Tool Selection Ground Truth Dataset (30+ test cases)
# ============================================================
AGENT_BENCHMARK_DATA = [
    # 1. Recurring & Subscriptions (EN & ZH)
    ("What recurring subscriptions do I have?", "detect_recurring_transactions"),
    ("Show me my monthly bills and recurring charges", "detect_recurring_transactions"),
    ("Do I have any active subscriptions?", "detect_recurring_transactions"),
    ("我每个月有哪些固定订阅？", "detect_recurring_transactions"),
    ("帮我找出所有周期性扣款账单", "detect_recurring_transactions"),
    ("查看按月自动扣款项目", "detect_recurring_transactions"),
    # 2. Anomalies & Unusual Transactions (EN & ZH)
    ("Were there any unusual transactions this month?", "detect_unusual_transactions"),
    ("Check for unexpected spikes or duplicate charges", "detect_unusual_transactions"),
    ("Flag any anomalies in my spending", "detect_unusual_transactions"),
    ("最近有什么异常消费吗？", "detect_unusual_transactions"),
    ("检查是否有重复扣款或可疑交易", "detect_unusual_transactions"),
    ("帮我排查不寻常的突增开销", "detect_unusual_transactions"),
    # 3. Top / Largest Purchases (EN & ZH)
    ("What was my largest purchase this month?", "get_top_transactions"),
    ("Show me my top 5 biggest expenses", "get_top_transactions"),
    ("What are my highest income deposits?", "get_top_transactions"),
    ("我最大的几笔支出是什么？", "get_top_transactions"),
    ("查看最贵的大额消费", "get_top_transactions"),
    ("列出金额最高的收入进账", "get_top_transactions"),
    # 4. Category Spending (EN & ZH)
    ("How much did I spend on Food and restaurants?", "get_spending_by_category"),
    ("What is my total spending on Shopping?", "get_spending_by_category"),
    ("Break down my expenditures by category", "get_spending_by_category"),
    ("餐饮外卖一共花了多少钱？", "get_spending_by_category"),
    ("本月在购物上支出多少？", "get_spending_by_category"),
    ("按分类统计我的各项开销", "get_spending_by_category"),
    ("交通出行花费了多少？", "get_spending_by_category"),
    # 5. Period Comparison (EN & ZH)
    ("Compare my spending this month versus last month", "compare_periods"),
    ("Did my expenses increase compared to August?", "compare_periods"),
    ("对比一下九月份和八月份的支出差异", "compare_periods"),
    ("消费环比上月是有所增长还是减少？", "compare_periods"),
    # 6. Overall Monthly Summary (EN & ZH)
    ("Give me a summary of my financial cash flow", "get_monthly_summary"),
    ("How am I doing overall this month?", "get_monthly_summary"),
    ("What is my net cash flow and balance?", "get_monthly_summary"),
    ("总结一下本月财务状况与现金流总览", "get_monthly_summary"),
    ("我的总收入与总支出结余是多少？", "get_monthly_summary"),
    # 7. Fallback Keyword Search (EN & ZH)
    ("Find transactions at Starbucks", "search_transactions"),
    ("Search for Apple purchases", "search_transactions"),
    ("搜索壳牌加油站的记录", "search_transactions"),
]
