TEST_CASES = [

    # ============================================================
    # 1. SQL INJECTION + INPUT VALIDATION + TYPE HINTS
    # ============================================================

    {
        "id": "case_01_user_query",
        "diff": '''
+ def get_user(user_id):
+     query = "SELECT * FROM users WHERE id = " + user_id
+     result = db.execute(query)
+     return result
''',
        "expected": [
            {
                "category": "security",
                "issue": "sql_injection"
            },
            {
                "category": "security",
                "issue": "no_input_validation"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },

    # ============================================================
    # 2. HARDCODED SECRET + BAD NAMING + TYPE HINTS
    # ============================================================

    {
        "id": "case_02_api_secret",
        "diff": '''
+ API_KEY = "sk-live-abc123456789"
+ def f(x):
+     response = requests.get(
+         "https://api.example.com",
+         headers={"Authorization": API_KEY}
+     )
+     return response
''',
        "expected": [
            {
                "category": "security",
                "issue": "hardcoded_secret"
            },
            {
                "category": "style",
                "issue": "bad_naming"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },

    # ============================================================
    # 3. EVAL + INPUT VALIDATION + BAD NAMING
    # ============================================================

    {
        "id": "case_03_eval",
        "diff": '''
+ def f(x):
+     result = eval(x)
+     return result
''',
        "expected": [
            {
                "category": "security",
                "issue": "unsafe_eval"
            },
            {
                "category": "security",
                "issue": "no_input_validation"
            },
            {
                "category": "style",
                "issue": "bad_naming"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },

    # ============================================================
    # 4. COMMAND INJECTION + INPUT VALIDATION + TYPE HINTS
    # ============================================================

    {
        "id": "case_04_delete_file",
        "diff": '''
+ import os
+ def f(filename):
+     os.system("rm " + filename)
''',
        "expected": [
            {
                "category": "security",
                "issue": "command_injection"
            },
            {
                "category": "security",
                "issue": "no_input_validation"
            },
            {
                "category": "style",
                "issue": "bad_naming"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },

    # ============================================================
    # 5. NONE DEREFERENCE + ERROR HANDLING + TYPE HINTS
    # ============================================================

    {
        "id": "case_05_database_lookup",
        "diff": '''
+ def get_price(product_id):
+     data = db.find(product_id)
+     price = data["price"]
+     return price
''',
        "expected": [
            {
                "category": "logic",
                "issue": "none_dereference"
            },
            {
                "category": "logic",
                "issue": "no_error_handling"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },

    # ============================================================
    # 6. OFF BY ONE + TYPE HINTS + BAD NAMING
    # ============================================================

    {
        "id": "case_06_last_item",
        "diff": '''
+ def f(x):
+     z = x[len(x)]
+     return z
''',
        "expected": [
            {
                "category": "logic",
                "issue": "off_by_one"
            },
            {
                "category": "style",
                "issue": "bad_naming"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },

    # ============================================================
    # 7. HTTP ERROR HANDLING + INPUT VALIDATION + TYPE HINTS
    # ============================================================

    {
        "id": "case_07_fetch_data",
        "diff": '''
+ def fetch_data(url):
+     response = requests.get(url)
+     return response.json()
''',
        "expected": [
            {
                "category": "logic",
                "issue": "no_error_handling"
            },
            {
                "category": "security",
                "issue": "no_input_validation"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },

    # ============================================================
    # 8. MULTIPLE SECURITY ISSUES
    # ============================================================

    {
        "id": "case_08_user_file",
        "diff": '''
+ def load_user_file(user_id, filename):
+     query = "SELECT path FROM files WHERE user_id = " + user_id
+     result = db.execute(query)
+     path = "/var/data/" + filename
+     with open(path) as f:
+         return f.read()
''',
        "expected": [
            {
                "category": "security",
                "issue": "sql_injection"
            },
            {
                "category": "security",
                "issue": "no_input_validation"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },

    # ============================================================
    # 9. CLEAN CASE
    # Expected = NOTHING
    # ============================================================

    {
        "id": "case_09_clean",
        "diff": '''
+ def calculate_total(price: float, tax: float) -> float:
+     if price < 0:
+         raise ValueError("price cannot be negative")
+     if tax < 0:
+         raise ValueError("tax cannot be negative")
+     return price * (1 + tax)
''',
        "expected": [],
    },

    # ============================================================
    # 10. LARGE MIXED CASE
    # ============================================================

    {
        "id": "case_10_mixed",
        "diff": '''
+ def f(x, y):
+     query = "SELECT * FROM users WHERE id = " + x
+     result = db.execute(query)
+     value = eval(y)
+     response = requests.get(y)
+     data = response.json()
+     return data["price"]
''',
        "expected": [
            {
                "category": "security",
                "issue": "sql_injection"
            },
            {
                "category": "security",
                "issue": "unsafe_eval"
            },
            {
                "category": "security",
                "issue": "no_input_validation"
            },
            {
                "category": "logic",
                "issue": "none_dereference"
            },
            {
                "category": "logic",
                "issue": "no_error_handling"
            },
            {
                "category": "style",
                "issue": "bad_naming"
            },
            {
                "category": "style",
                "issue": "missing_type_hints"
            },
        ],
    },
]