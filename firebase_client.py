import os
import json
import requests
from typing import Dict, List, Optional

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "firebase_config.json")

class FirebaseClient:
    def __init__(self):
        self.enabled = False
        self.project_id = ""
        self.api_key = ""
        self.load_config()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "enabled": False,
                "project_id": "your-firebase-project-id",
                "api_key": "your-firebase-api-key",
                "notes": "Firebaseクラウド同期を有効にする場合は enabled: true と設定し、プロジェクトIDを入力してください。"
            }
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Firebase config creation notice: {e}")
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.enabled = data.get("enabled", False)
                self.project_id = data.get("project_id", "")
                self.api_key = data.get("api_key", "")
        except Exception as e:
            print(f"Error loading Firebase config: {e}")
            self.enabled = False

    def save_config_file(self, enabled: bool, project_id: str, api_key: str = "dummy"):
        self.enabled = enabled
        self.project_id = project_id
        self.api_key = api_key
        data = {
            "enabled": enabled,
            "project_id": project_id,
            "api_key": api_key,
            "notes": "Firebaseクラウド同期設定"
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving Firebase config: {e}")

    def sync_to_cloud(self, accounts: List[Dict]) -> bool:
        if not self.enabled or not self.project_id or self.project_id.startswith("your-"):
            return False

        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/accounts"
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
                    "url": {"stringValue": acc.get("url", "")}
                }
                body = {"fields": fields}
                response = requests.patch(f"{doc_url}?key={self.api_key}", json=body, timeout=5)
            print("[Firebase Sync] Uploaded accounts to cloud successfully.")
            return True
        except Exception as e:
            print(f"[Firebase Sync Notice] Could not sync to cloud: {e}")
            return False

    def fetch_from_cloud(self) -> Optional[List[Dict]]:
        if not self.enabled or not self.project_id or self.project_id.startswith("your-"):
            return None

        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/accounts?key={self.api_key}"
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
                        "aliases": aliases
                    }
                    accounts.append(acc)
                print(f"[Firebase Sync] Downloaded {len(accounts)} accounts from cloud.")
                return accounts
        except Exception as e:
            print(f"[Firebase Sync Notice] Fetch error: {e}")
        return None
