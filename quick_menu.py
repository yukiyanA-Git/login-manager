from PySide6.QtWidgets import QMenu, QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QUrl
from PySide6.QtGui import QAction, QFont, QIcon, QColor, QDesktopServices

class QuickTrayMenu(QMenu):
    def __init__(self, manager_win, overlay_instance, parent=None):
        super().__init__(parent)
        self.manager_win = manager_win
        self.overlay = overlay_instance

        self.setStyleSheet("""
            QMenu {
                background-color: #111827;
                border: 2px solid #0078D4;
                border-radius: 10px;
                color: #F9FAFB;
                padding: 6px;
                font-family: 'Segoe UI', 'Meiryo', sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background-color: #0078D4;
                color: #FFFFFF;
                font-weight: bold;
            }
            QMenu::separator {
                height: 1px;
                background-color: #374151;
                margin: 4px 8px;
            }
        """)

        self.aboutToShow.connect(self.build_menu)
        self.build_menu()

    def build_menu(self):
        self.clear()

        title_action = QAction("🔑  ログインマネージャー クイックメニュー", self)
        title_action.setEnabled(False)
        self.addAction(title_action)
        self.addSeparator()

        user_email = self.manager_win.vault.firebase.user_email
        if user_email:
            google_text = f"🔴  Google連動中: {user_email}"
        else:
            google_text = "🔴  Googleアカウントでサインイン"

        action_google = QAction(google_text, self)
        action_google.triggered.connect(self.trigger_google_auth)
        self.addAction(action_google)

        self.addSeparator()

        # Dynamic Bookmark Submenu
        bookmark_menu = QMenu("🔖  登録サイトを開く (ブックマーク)", self)
        bookmark_menu.setStyleSheet("""
            QMenu {
                background-color: #1F2937;
                border: 1px solid #0078D4;
                border-radius: 8px;
                color: #F9FAFB;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 14px;
            }
            QMenu::item:selected {
                background-color: #4F46E5;
                color: #FFFFFF;
            }
        """)

        has_bookmarks = False
        accounts = self.manager_win.vault.accounts
        for acc in accounts:
            name = acc.get("name", "")
            url = acc.get("url", "")
            if name:
                has_bookmarks = True
                display_label = f"🌐  {name}"
                if url:
                    display_label += f" ({url[:25]}...)" if len(url) > 25 else f" ({url})"

                action_site = QAction(display_label, self)
                action_site.triggered.connect(lambda _, a=acc: self.open_bookmark_and_popup(a))
                bookmark_menu.addAction(action_site)

        if not has_bookmarks:
            action_empty = QAction("（登録サイトはありません）", self)
            action_empty.setEnabled(False)
            bookmark_menu.addAction(action_empty)

        self.addMenu(bookmark_menu)

        self.addSeparator()

        action_register = QAction("➕  新規アカウント登録 (コピー文/画面ロゴから)", self)
        action_register.triggered.connect(self.trigger_register)
        self.addAction(action_register)

        action_search = QAction("🔍  ログイン情報検索 (コピー文 Ctrl+C)", self)
        action_search.triggered.connect(self.trigger_search)
        self.addAction(action_search)

        action_ocr = QAction("📐  画面ロゴ/枠で囲んで検索 (画像比較)", self)
        action_ocr.triggered.connect(self.trigger_ocr)
        self.addAction(action_ocr)

        self.addSeparator()

        action_manage = QAction("⚙️  アカウント管理画面を開く", self)
        action_manage.triggered.connect(self.trigger_manage)
        self.addAction(action_manage)

        self.addSeparator()

        action_quit = QAction("❌  アプリ完全終了", self)
        action_quit.triggered.connect(QApplication.quit)
        self.addAction(action_quit)

    def open_bookmark_and_popup(self, acc: dict):
        url = acc.get("url", "").strip()
        if url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            QDesktopServices.openUrl(QUrl(url))

        # Close any active OCR overlays cleanly
        self.overlay.hide()
        # Show popup window staying on top so it doesn't get buried!
        self.overlay.handle_account_found(acc)

    def trigger_google_auth(self):
        self.overlay.hide()
        self.manager_win.open_google_dialog()

    def trigger_register(self):
        clip_text = QApplication.clipboard().text().strip()
        if clip_text and len(clip_text) < 50:
            self.overlay.hide()
            self.manager_win.open_add_dialog(initial_name=clip_text)
            self.manager_win.show()
            self.manager_win.raise_()
            self.manager_win.activateWindow()
        else:
            self.overlay.show_overlay_for_register(
                lambda name, logo_b64="": self.manager_win.open_add_dialog(initial_name=name, logo_b64=logo_b64)
            )

    def trigger_search(self):
        self.overlay.smart_search()

    def trigger_ocr(self):
        self.overlay.show_overlay()

    def trigger_manage(self):
        self.overlay.hide()
        self.manager_win.show()
        self.manager_win.raise_()
        self.manager_win.activateWindow()
