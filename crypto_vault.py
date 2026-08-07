import os
import json
import csv
import difflib
from typing import List, Dict, Optional
from cryptography.fernet import Fernet
from firebase_client import FirebaseClient
from logo_matcher import match_logo_image

KEY_FILE = os.path.join(os.path.dirname(__file__), "vault_key.key")
DATA_FILE = os.path.join(os.path.dirname(__file__), "vault_data.json")

class CryptoVault:
    def __init__(self):
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)
        self.firebase = FirebaseClient()
        self.accounts: List[Dict] = []
        self.load_vault()

    def _get_or_create_key(self) -> bytes:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

    def load_vault(self):
        cloud_accs = self.firebase.fetch_from_cloud()
        if cloud_accs is not None and len(cloud_accs) > 0:
            self.accounts = cloud_accs
            self.save_local_file()
            return

        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self.fernet.decrypt(encrypted_data).decode("utf-8")
                self.accounts = json.loads(decrypted_data)
            except Exception as e:
                print(f"Error loading vault: {e}")
                self.accounts = []
        else:
            self.accounts = []

    def save_vault(self):
        self.save_local_file()
        if self.firebase.enabled:
            self.firebase.sync_to_cloud(self.accounts)

    def save_local_file(self):
        raw_json = json.dumps(self.accounts, ensure_ascii=False, indent=2).encode("utf-8")
        encrypted_data = self.fernet.encrypt(raw_json)
        with open(DATA_FILE, "wb") as f:
            f.write(encrypted_data)

    def add_account(self, name: str, username: str, password: str, security_level: int = 1,
                    category: str = "一般", url: str = "", notes: str = "",
                    sec_question: str = "", sec_answer: str = "",
                    alias1: str = "", alias2: str = "", logo_image: str = ""):
        import uuid
        acc_id = str(uuid.uuid4())[:8]

        aliases = [name.lower()]
        if alias1:
            aliases.append(alias1.lower())
        if alias2:
            aliases.append(alias2.lower())

        acc = {
            "id": acc_id,
            "name": name,
            "alias1": alias1,
            "alias2": alias2,
            "username": username,
            "password": password,
            "security_level": security_level,
            "category": category,
            "url": url,
            "notes": notes,
            "sec_question": sec_question,
            "sec_answer": sec_answer,
            "aliases": aliases,
            "logo_image": logo_image
        }
        self.accounts.append(acc)
        self.save_vault()
        return acc

    def delete_account(self, acc_id: str):
        self.accounts = [a for a in self.accounts if a.get("id") != acc_id]
        self.save_vault()

    def find_account_by_name(self, query: str) -> Optional[Dict]:
        if not query:
            return None
        q = query.strip().lower()

        for acc in self.accounts:
            aliases = acc.get("aliases", [acc.get("name", "").lower()])
            for a in aliases:
                if q == a or q in a or a in q:
                    return acc

        all_terms = []
        term_map = {}
        for acc in self.accounts:
            name = acc.get("name", "").lower()
            all_terms.append(name)
            term_map[name] = acc
            for a in [acc.get("alias1", "").lower(), acc.get("alias2", "").lower()]:
                if a:
                    all_terms.append(a)
                    term_map[a] = acc

        matches = difflib.get_close_matches(q, all_terms, n=1, cutoff=0.35)
        if matches:
            return term_map[matches[0]]
        return None

    def find_account_by_window_title(self, window_title: str) -> Optional[Dict]:
        if not window_title:
            return None

        clean_title = window_title
        for suffix in [" - Google Chrome", " - Microsoft Edge", " - Mozilla Firefox", " - Brave", " - Opera"]:
            if clean_title.endswith(suffix):
                clean_title = clean_title[:-len(suffix)]

        clean_title_lower = clean_title.lower()

        for acc in self.accounts:
            name = acc.get("name", "").lower()
            alias1 = acc.get("alias1", "").lower()
            alias2 = acc.get("alias2", "").lower()

            if name and (name in clean_title_lower or clean_title_lower in name):
                return acc
            if alias1 and (alias1 in clean_title_lower or clean_title_lower in alias1):
                return acc
            if alias2 and (alias2 in clean_title_lower or clean_title_lower in alias2):
                return acc

        return self.find_account_by_name(clean_title)

    def find_account_by_logo(self, target_img) -> Optional[Dict]:
        return match_logo_image(target_img, self.accounts, threshold=0.75)

    def export_accounts_to_csv(self, file_path: str) -> int:
        """Exports all registered accounts to CSV file with UTF-8 BOM encoding."""
        headers = ["会社名", "製品名1", "製品名2", "ID", "パスワード", "セキュリティレベル", "備考", "秘密の質問", "秘密の答え", "カテゴリー", "URL"]
        rows = []
        for acc in self.accounts:
            rows.append([
                acc.get("name", ""),
                acc.get("alias1", ""),
                acc.get("alias2", ""),
                acc.get("username", ""),
                acc.get("password", ""),
                str(acc.get("security_level", 1)),
                acc.get("notes", ""),
                acc.get("sec_question", ""),
                acc.get("sec_answer", ""),
                acc.get("category", "一般"),
                acc.get("url", "")
            ])

        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return len(rows)

    def import_csv(self, file_path: str) -> int:
        count = 0
        if not os.path.exists(file_path):
            return 0

        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                if len(row) >= 5:
                    name = row[0].strip()
                    alias1 = row[1].strip() if len(row) > 1 else ""
                    alias2 = row[2].strip() if len(row) > 2 else ""
                    username = row[3].strip() if len(row) > 3 else ""
                    password = row[4].strip() if len(row) > 4 else ""
                    sec_level = int(row[5]) if len(row) > 5 and row[5].isdigit() else 1
                    notes = row[6] if len(row) > 6 else ""
                    sec_q = row[7] if len(row) > 7 else ""
                    sec_a = row[8] if len(row) > 8 else ""
                    cat = row[9] if len(row) > 9 else "一般"
                    url = row[10] if len(row) > 10 else ""

                    if name and username and password:
                        self.add_account(
                            name=name, username=username, password=password,
                            security_level=sec_level, category=cat, url=url,
                            notes=notes, sec_question=sec_q, sec_answer=sec_a,
                            alias1=alias1, alias2=alias2
                        )
                        count += 1
        return count
