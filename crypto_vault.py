import os
import json
import csv
import base64
import difflib
from typing import List, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from firebase_client import FirebaseClient

VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault_data.json")
MASTER_SALT = b"AntigravityPasswordManagerSalt2026"

class CryptoVault:
    def __init__(self, master_password: str = "default_master_key"):
        self.master_password = master_password
        self.fernet = self._generate_fernet(master_password)
        self.firebase = FirebaseClient()
        self.accounts: List[Dict] = []
        self.load_vault()

    def _generate_fernet(self, password: str) -> Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=MASTER_SALT,
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def load_vault(self):
        cloud_accounts = self.firebase.fetch_from_cloud()
        if cloud_accounts:
            self.accounts = cloud_accounts
            self.save_local_file()
            return

        if not os.path.exists(VAULT_FILE):
            self._create_demo_accounts()
            self.save_vault()
            return

        try:
            with open(VAULT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.accounts = data.get("accounts", [])
        except Exception as e:
            print(f"Error loading vault: {e}")
            self._create_demo_accounts()

    def save_vault(self):
        self.save_local_file()
        self.firebase.sync_to_cloud(self.accounts)

    def save_local_file(self):
        data = {"accounts": self.accounts}
        with open(VAULT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _create_demo_accounts(self):
        self.accounts = [
            {
                "id": "acc_001",
                "name": "Amazon",
                "alias1": "アマゾン",
                "alias2": "Amazon Prime",
                "aliases": ["amazon", "アマゾン", "amazon.co.jp", "amazon prime"],
                "username": "user_amazon@example.com",
                "password": "AmazonSecurePassword123!",
                "security_level": 1,
                "category": "ショッピング",
                "url": "https://www.amazon.co.jp",
                "notes": "プライム会員アカウント",
                "sec_question": "",
                "sec_answer": ""
            },
            {
                "id": "acc_002",
                "name": "Sansan",
                "alias1": "Eight",
                "alias2": "Sansan名刺",
                "aliases": ["sansan", "eight", "エイト"],
                "username": "user_sansan@example.com",
                "password": "SansanPassword#2026",
                "security_level": 1,
                "category": "ビジネス",
                "url": "https://8card.net",
                "notes": "名刺管理サービスEight",
                "sec_question": "",
                "sec_answer": ""
            },
            {
                "id": "acc_003",
                "name": "マネーフォワード",
                "alias1": "MFクラウド",
                "alias2": "マネーフォワードME",
                "aliases": ["マネーフォワード", "moneyforward", "mfクラウド", "mf"],
                "username": "finance_user@example.com",
                "password": "MoneyForwardStrictPass$99",
                "security_level": 3,
                "category": "金融・資産",
                "url": "https://moneyforward.com",
                "notes": "暗号化資産口座連携済み",
                "sec_question": "第一ペットの名前",
                "sec_answer": "ポチ"
            }
        ]

    def find_account_by_name(self, search_text: str) -> Optional[Dict]:
        """
        Clipboard / OCR Text Search matching:
        1. Exact / Substring match against Name, Alias1, Alias2, or Aliases list.
        2. Fuzzy Similarity ratio match.
        """
        if not search_text:
            return None
        text_lower = search_text.strip().lower()

        # Step 1: Substring / Exact match
        for acc in self.accounts:
            all_names = [acc["name"].lower(), acc.get("alias1", "").lower(), acc.get("alias2", "").lower()] + [a.lower() for a in acc.get("aliases", [])]
            for target in all_names:
                if target and (text_lower in target or target in text_lower):
                    return acc

        # Step 2: Fuzzy Similarity match
        best_match = None
        best_ratio = 0.0

        for acc in self.accounts:
            all_names = [acc["name"].lower(), acc.get("alias1", "").lower(), acc.get("alias2", "").lower()] + [a.lower() for a in acc.get("aliases", [])]
            for target in all_names:
                if not target:
                    continue
                ratio = difflib.SequenceMatcher(None, text_lower, target).ratio()
                if ratio > best_ratio and ratio >= 0.45:
                    best_ratio = ratio
                    best_match = acc

        if best_match:
            print(f"[Smart Match] Matched '{search_text}' -> '{best_match['name']}' (Ratio: {best_ratio:.2f})")
            return best_match

        return None

    def add_account(self, name: str, username: str, password: str, security_level: int = 1,
                    category: str = "一般", url: str = "", notes: str = "",
                    sec_question: str = "", sec_answer: str = "",
                    alias1: str = "", alias2: str = ""):
        aliases = [name.lower(), name.replace(" ", "").lower()]
        if alias1:
            aliases.append(alias1.lower())
        if alias2:
            aliases.append(alias2.lower())

        acc_id = f"acc_{len(self.accounts) + 1:03d}"
        new_acc = {
            "id": acc_id,
            "name": name,
            "alias1": alias1,
            "alias2": alias2,
            "aliases": aliases,
            "username": username,
            "password": password,
            "security_level": security_level,
            "category": category,
            "url": url,
            "notes": notes,
            "sec_question": sec_question,
            "sec_answer": sec_answer
        }
        self.accounts.append(new_acc)
        self.save_vault()
        return new_acc

    def delete_account(self, acc_id: str):
        self.accounts = [a for a in self.accounts if a["id"] != acc_id]
        self.save_vault()

    def import_csv(self, file_path: str) -> int:
        count = 0
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("会社名") or row.get("Name") or row.get("title") or "Unknown"
                alias1 = row.get("製品名1") or row.get("製品名") or row.get("Alias1") or ""
                alias2 = row.get("製品名2") or row.get("Alias2") or ""
                username = row.get("ID") or row.get("Username") or row.get("username") or ""
                password = row.get("パスワード") or row.get("Password") or row.get("password") or ""
                sec_str = str(row.get("セキュリティレベル") or row.get("SecurityLevel") or "1")
                sec_level = 3 if "3" in sec_str or "高" in sec_str else 1
                cat = row.get("カテゴリー") or row.get("Category") or "CSVインポート"
                url = row.get("URL") or ""
                notes = row.get("備考") or row.get("Notes") or ""
                sec_q = row.get("秘密の質問") or row.get("SecurityQuestion") or ""
                sec_a = row.get("秘密の答え") or row.get("SecurityAnswer") or ""

                if name and (username or password):
                    self.add_account(name, username, password, sec_level, cat, url, notes, sec_q, sec_a, alias1, alias2)
                    count += 1
        return count
