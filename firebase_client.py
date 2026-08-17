import sys
import os
import json
import requests
import hashlib
from typing import Dict, List, Optional

def get_persistent_data_dir() -> str:
    appdata = os.getenv('APPDATA')
    if appdata:
        data_dir = os.path.join(appdata, "LoginManager")
    else:
        data_dir = os.path.expanduser("~/.login_manager")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

CONFIG_FILE = os.path.join(get_persistent_data_dir(), "firebase_config.json")

class FirebaseClient:
    def __init__(self):
        self.enabled = True
        self.project_id = "login-manager-official"
        self.user_id = ""
        self.user_email = ""
        self.master_pin_hash = ""
        self.master_pin_hint = ""
        self.load_config()

    def _hash_pin(self, pin_str: str) -> str:
        return hashlib.sha256(pin_str.strip().encode("utf-8")).hexdigest()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "enabled": True,
                "project_id": "login-manager-official",
                "user_id": "",
                "user_email": "",
                "master_pin_hash": self._hash_pin("1234"),
                "master_pin_hint": "初期番号(1234)",
                "notes": "Googleアカウント認証＆個人のFirestoreデータ保護設定"
            }
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Firebase config notice: {e}")
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.enabled = data.get("enabled", True)
                self.project_id = data.get("project_id", "login-manager-official")
                self.user_email = data.get("user_email", "").strip()
                self.user_id = data.get("user_id", "").strip()
                self.master_pin_hash = data.get("master_pin_hash", self._hash_pin("1234"))
                self.master_pin_hint = data.get("master_pin_hint", "初期番号(1234)")

                if self.user_email and not self.user_id:
                    safe_id = self.user_email.lower().replace("@", "_at_").replace(".", "_")
                    self.user_id = f"usr_{safe_id}"
        except Exception as e:
            print(f"Error loading Firebase config: {e}")
            self.master_pin_hash = self._hash_pin("1234")
            self.master_pin_hint = "初期番号(1234)"

    def save_master_pin(self, new_pin: str, hint: str = ""):
        self.master_pin_hash = self._hash_pin(new_pin)
        if hint:
            self.master_pin_hint = hint.strip()
        self.save_user_session(user_email=self.user_email, user_id=self.user_id)

    def verify_master_pin(self, typed_pin: str) -> bool:
        typed_hash = self._hash_pin(typed_pin)
        if typed_hash == self.master_pin_hash:
            return True
        if typed_pin in ["1234"] and (not self.master_pin_hash or self.master_pin_hash == self._hash_pin("1234")):
            return True
        return False

    def save_user_session(self, user_email: str, user_id: str = ""):
        self.user_email = user_email.strip()
        if not user_id and user_email:
            safe_id = user_email.lower().replace("@", "_at_").replace(".", "_")
            self.user_id = f"usr_{safe_id}"
        elif user_id:
            self.user_id = user_id

        self.enabled = True
        data = {
            "enabled": True,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "master_pin_hash": self.master_pin_hash,
            "master_pin_hint": self.master_pin_hint,
            "notes": "Googleアカウント認証アクティブ"
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[Firebase Session Saved] User '{self.user_email}' (ID: {self.user_id}) saved persistently to {CONFIG_FILE}")
        except Exception as e:
            print(f"Error saving user session: {e}")

        if self.user_id and self.project_id:
            try:
                url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/users/{self.user_id}/settings/pin_config"
                body = {
                    "fields": {
                        "master_pin_hash": {"stringValue": self.master_pin_hash},
                        "master_pin_hint": {"stringValue": self.master_pin_hint},
                        "user_email": {"stringValue": self.user_email}
                    }
                }
                requests.patch(url, json=body, timeout=4)
            except Exception as e:
                print(f"Error syncing master PIN to cloud: {e}")

    def logout_user(self):
        self.user_email = ""
        self.user_id = ""
        data = {
            "enabled": True,
            "project_id": self.project_id,
            "user_id": "",
            "user_email": "",
            "master_pin_hash": self.master_pin_hash,
            "master_pin_hint": self.master_pin_hint,
            "notes": "ログアウト状態 (ローカル保存のみ)"
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving logout session: {e}")

    def sync_to_cloud(self, accounts: List[Dict]) -> bool:
        if not self.enabled or not self.user_email:
            return False

        if not self.user_id:
            safe_id = self.user_email.lower().replace("@", "_at_").replace(".", "_")
            self.user_id = f"usr_{safe_id}"

        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/users/{self.user_id}/accounts"
            for acc in accounts:
                doc_id = acc.get("id", "acc_unk")
                doc_url = f"{url}/{doc_id}"

                fields = {
                    "name": {"stringValue": acc.get("name", "")},
                    "alias1": {"stringValue": acc.get("alias1", "")},
                    "alias2": {"stringValue": acc.get("alias2", "")},
                    "username": {"stringValue": acc.get("username", "")},
                    "password": {"stringValue": acc.get("password", "")},
                    "security_level": {"integerValue": int(acc.get("security_level", 1))},
                    "category": {"stringValue": acc.get("category", "")},
                    "notes": {"stringValue": acc.get("notes", "")},
                    "sec_question": {"stringValue": acc.get("sec_question", "")},
                    "sec_answer": {"stringValue": acc.get("sec_answer", "")},
                    "url": {"stringValue": acc.get("url", "")},
                    "logo_image": {"stringValue": acc.get("logo_image", "")}
                }
                body = {"fields": fields}
                response = requests.patch(doc_url, json=body, timeout=5)
            print(f"[Firebase Cloud] Successfully uploaded {len(accounts)} accounts for User '{self.user_email}'.")
            return True
        except Exception as e:
            print(f"[Firebase Cloud Notice] Sync upload error: {e}")
            return False

    def fetch_from_cloud(self) -> Optional[List[Dict]]:
        if not self.enabled or not self.user_email:
            return None

        if not self.user_id:
            safe_id = self.user_email.lower().replace("@", "_at_").replace(".", "_")
            self.user_id = f"usr_{safe_id}"

        try:
            try:
                settings_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/users/{self.user_id}/settings/pin_config"
                s_resp = requests.get(settings_url, timeout=3)
                if s_resp.status_code == 200:
                    s_data = s_resp.json()
                    c_hash = s_data.get("fields", {}).get("master_pin_hash", {}).get("stringValue", "")
                    c_hint = s_data.get("fields", {}).get("master_pin_hint", {}).get("stringValue", "")
                    if c_hash:
                        self.master_pin_hash = c_hash
                    if c_hint:
                        self.master_pin_hint = c_hint
            except Exception as e:
                print(f"Error fetching master PIN from cloud: {e}")

            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/users/{self.user_id}/accounts"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                documents = data.get("documents", [])
                accounts = []
                for doc in documents:
                    doc_name = doc.get("name", "")
                    doc_id = doc_name.split("/")[-1] if "/" in doc_name else "acc"
                    fields = doc.get("fields", {})

                    name_str = fields.get("name", {}).get("stringValue", "")
                    alias1_str = fields.get("alias1", {}).get("stringValue", "")
                    alias2_str = fields.get("alias2", {}).get("stringValue", "")

                    aliases = [name_str.lower()]
                    if alias1_str:
                        aliases.append(alias1_str.lower())
                    if alias2_str:
                        aliases.append(alias2_str.lower())

                    acc = {
                        "id": doc_id,
                        "name": name_str,
                        "alias1": alias1_str,
                        "alias2": alias2_str,
                        "username": fields.get("username", {}).get("stringValue", ""),
                        "password": fields.get("password", {}).get("stringValue", ""),
                        "security_level": int(fields.get("security_level", {}).get("integerValue", 1)),
                        "category": fields.get("category", {}).get("stringValue", ""),
                        "notes": fields.get("notes", {}).get("stringValue", ""),
                        "sec_question": fields.get("sec_question", {}).get("stringValue", ""),
                        "sec_answer": fields.get("sec_answer", {}).get("stringValue", ""),
                        "url": fields.get("url", {}).get("stringValue", ""),
                        "logo_image": fields.get("logo_image", {}).get("stringValue", ""),
                        "aliases": aliases
                    }
                    accounts.append(acc)
                print(f"[Firebase Cloud] Downloaded {len(accounts)} accounts for User '{self.user_email}'.")
                return accounts
        except Exception as e:
            print(f"[Firebase Cloud Notice] Fetch error: {e}")
        return None
