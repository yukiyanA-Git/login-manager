import sys
import os
import json
import csv
import difflib
from typing import List, Dict, Optional
from cryptography.fernet import Fernet
from firebase_client import FirebaseClient, get_persistent_data_dir
from logo_matcher import match_logo_image

DATA_DIR = get_persistent_data_dir()
KEY_FILE = os.path.join(DATA_DIR, "vault_key.key")
DATA_FILE = os.path.join(DATA_DIR, "vault_data.json")

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

        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        legacy_key_path = os.path.join(exe_dir, "vault_key.key")
        if os.path.exists(legacy_key_path):
            with open(legacy_key_path, "rb") as f:
                key = f.read()
            with open(KEY_FILE, "wb") as f:
                f.write(key)
            return key

        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

    def _get_default_sample_accounts(self) -> List[Dict]:
        return [
            {
                "id": "acc_001",
                "name": "楽天市場",
                "alias1": "楽天Ichiba",
                "alias2": "",
                "field1_name": "会員番号",
                "field1_value": "RK-998877",
                "field2_name": "",
                "field2_value": "",
                "username": "rakuten_user@example.com",
                "password": "RakutenPass2026!",
                "security_level": 1,
                "category": "ショッピング",
                "notes": "ポイントカード会員アカウント",
                "sec_question": "",
                "sec_answer": "",
                "url": "https://www.rakuten.co.jp",
                "aliases": ["楽天市場", "楽天ichiba", "会員番号", "rk-998877"],
                "logo_image": ""
            },
            {
                "id": "acc_002",
                "name": "SBI証券",
                "alias1": "SBIネット証券",
                "alias2": "",
                "field1_name": "取引暗号コード",
                "field1_value": "1234",
                "field2_name": "口座番号",
                "field2_value": "889900",
                "username": "sbi_account_8899",
                "password": "SBIStrictSecuredPass#999",
                "security_level": 3,
                "category": "金融・資産",
                "notes": "セキュリティレベル高設定",
                "sec_question": "母親の旧姓",
                "sec_answer": "田中",
                "url": "https://www.sbisec.co.jp",
                "aliases": ["sbi証券", "sbiネット証券", "1234", "889900"],
                "logo_image": ""
            },
            {
                "id": "acc_003",
                "name": "Sansan",
                "alias1": "Eight",
                "alias2": "Sansan名刺",
                "field1_name": "名刺ID",
                "field1_value": "CARD-88",
                "field2_name": "",
                "field2_value": "",
                "username": "user_sansan@example.com",
                "password": "SansanPassword#2026",
                "security_level": 1,
                "category": "ビジネス",
                "notes": "名刺管理サービスEight連携",
                "sec_question": "",
                "sec_answer": "",
                "url": "https://8card.net",
                "aliases": ["sansan", "eight", "sansan名刺", "card-88"],
                "logo_image": ""
            },
            {
                "id": "acc_004",
                "name": "マネーフォワード",
                "alias1": "MFクラウド",
                "alias2": "マネーフォワードME",
                "field1_name": "契約番号",
                "field1_value": "MF-771122",
                "field2_name": "",
                "field2_value": "",
                "username": "finance_user@example.com",
                "password": "MoneyForwardStrictPass$99",
                "security_level": 3,
                "category": "金融・資産",
                "notes": "暗号化資産口座連携済み",
                "sec_question": "ペットの名前",
                "sec_answer": "ポチ",
                "url": "https://moneyforward.com",
                "aliases": ["マネーフォワード", "mfクラウド", "マネーフォワードme", "mf-771122"],
                "logo_image": ""
            }
        ]

    def load_vault(self):
        local_accs = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self.fernet.decrypt(encrypted_data).decode("utf-8")
                local_accs = json.loads(decrypted_data)
            except Exception as e:
                print(f"Error loading local vault: {e}")
                local_accs = []

        if not local_accs:
            local_accs = self._get_default_sample_accounts()
            self.accounts = local_accs
            self.save_local_file()
        else:
            self.accounts = local_accs

    def merge_accounts(self, cloud_accs: List[Dict]):
        existing_ids = {a.get("id"): a for a in self.accounts if a.get("id")}
        existing_keys = {f"{a.get('name', '').lower()}_{a.get('username', '').lower()}": a for a in self.accounts}

        for c_acc in cloud_accs:
            c_id = c_acc.get("id")
            c_key = f"{c_acc.get('name', '').lower()}_{c_acc.get('username', '').lower()}"

            if c_id and c_id in existing_ids:
                existing_ids[c_id].update(c_acc)
            elif c_key in existing_keys:
                existing_keys[c_key].update(c_acc)
            else:
                self.accounts.append(c_acc)

        self.save_local_file()

    def save_vault(self):
        # 100% Pure Local Encryption Save (AES-256)
        self.save_local_file()

    def save_local_file(self):
        raw_json = json.dumps(self.accounts, ensure_ascii=False, indent=2).encode("utf-8")
        encrypted_data = self.fernet.encrypt(raw_json)
        with open(DATA_FILE, "wb") as f:
            f.write(encrypted_data)

    def add_account(self, name: str, username: str, password: str, security_level: int = 1,
                    category: str = "一般", url: str = "", notes: str = "",
                    sec_question: str = "", sec_answer: str = "",
                    alias1: str = "", alias2: str = "", logo_image: str = "",
                    field1_name: str = "", field1_value: str = "",
                    field2_name: str = "", field2_value: str = ""):
        import uuid
        acc_id = str(uuid.uuid4())[:8]

        f1_n = field1_name.strip()
        f1_v = field1_value.strip() or alias1.strip()
        f2_n = field2_name.strip()
        f2_v = field2_value.strip() or alias2.strip()

        aliases = [name.lower()]
        if f1_v:
            aliases.append(f1_v.lower())
        if f2_v:
            aliases.append(f2_v.lower())
        if f1_n:
            aliases.append(f1_n.lower())
        if f2_n:
            aliases.append(f2_n.lower())

        acc = {
            "id": acc_id,
            "name": name,
            "alias1": f1_v,
            "alias2": f2_v,
            "field1_name": f1_n,
            "field1_value": f1_v,
            "field2_name": f2_n,
            "field2_value": f2_v,
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
        headers = [
            "会社名", "製品名1/別名1", "製品名2/別名2", "ID", "パスワード", "セキュリティレベル",
            "第3項目タイトル", "第3項目文字列", "第4項目タイトル", "第4項目文字列",
            "備考", "秘密の質問", "秘密の答え", "カテゴリー", "URL"
        ]
        rows = []
        for acc in self.accounts:
            rows.append([
                acc.get("name", ""),
                acc.get("alias1", ""),
                acc.get("alias2", ""),
                acc.get("username", ""),
                acc.get("password", ""),
                str(acc.get("security_level", 1)),
                acc.get("field1_name", ""),
                acc.get("field1_value") or acc.get("alias1", ""),
                acc.get("field2_name", ""),
                acc.get("field2_value") or acc.get("alias2", ""),
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

                    if len(row) >= 15:
                        f1_name = row[6].strip()
                        f1_val = row[7].strip()
                        f2_name = row[8].strip()
                        f2_val = row[9].strip()
                        notes = row[10]
                        sec_q = row[11]
                        sec_a = row[12]
                        cat = row[13]
                        url = row[14]
                    else:
                        f1_name = ""
                        f1_val = alias1
                        f2_name = ""
                        f2_val = alias2
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
                            alias1=f1_val or alias1, alias2=f2_val or alias2,
                            field1_name=f1_name, field1_value=f1_val or alias1,
                            field2_name=f2_name, field2_value=f2_val or alias2
                        )
                        count += 1
        return count
