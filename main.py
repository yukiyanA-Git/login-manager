import sys
import os
import csv
import traceback
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QCursor

from crypto_vault import CryptoVault
from overlay_screen import ScreenSelectionOverlay
from account_manager_ui import AccountManagerWindow
from quick_menu import QuickTrayMenu

def excepthook(exc_type, exc_value, exc_traceback):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"[App Error]\n{err_msg}")

sys.excepthook = excepthook

def ensure_icon_file(target_dir: str) -> str:
    icon_path = os.path.join(target_dir, "app_icon.png")
    if not os.path.exists(icon_path):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor(0, 120, 212))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI Symbol", 24, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🔑")
        painter.end()

        pixmap.save(icon_path, "PNG")
    return icon_path

def generate_sample_csv(target_dir: str):
    csv_path = os.path.join(target_dir, "sample_import_passwords.csv")
    headers = ["会社名", "製品名1", "製品名2", "ID", "パスワード", "セキュリティレベル", "備考", "秘密の質問", "秘密の答え", "カテゴリー", "URL"]
    rows = [
        ["楽天市場", "楽天Ichiba", "", "rakuten_user@example.com", "RakutenPass2026!", "1", "ポイントカード会員", "", "", "ショッピング", "https://www.rakuten.co.jp"],
        ["SBI証券", "SBIネット証券", "", "sbi_account_8899", "SBIStrictSecuredPass#999", "3", "取引暗号コード: 1234", "母親の旧姓", "田中", "金融・資産", "https://www.sbisec.co.jp"],
        ["Sansan", "Eight", "Sansan名刺", "user_sansan@example.com", "SansanPassword#2026", "1", "名刺管理サービスEight", "", "", "ビジネス", "https://8card.net"],
        ["マネーフォワード", "MFクラウド", "マネーフォワードME", "finance_user@example.com", "MoneyForwardStrictPass$99", "3", "暗号化資産口座連携済み", "ペットの名前", "ポチ", "金融・資産", "https://moneyforward.com"]
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return csv_path

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    app_dir = os.path.dirname(os.path.abspath(__file__))
    icon_file = ensure_icon_file(app_dir)
    generate_sample_csv(app_dir)

    vault = CryptoVault()
    overlay = ScreenSelectionOverlay(vault)
    manager_win = AccountManagerWindow(vault, overlay_instance=overlay)

    app_icon = QIcon(icon_file)
    app.setWindowIcon(app_icon)

    tray = QSystemTrayIcon(app_icon, app)
    tray.setToolTip("ログインマネージャー - クリックでクイック操作")

    quick_menu = QuickTrayMenu(manager_win, overlay)
    tray.setContextMenu(quick_menu)

    # Both Left-Click and Right-Click open the Quick Menu cleanly at mouse cursor position!
    def on_tray_activated(reason):
        overlay.hide()
        quick_menu.build_menu()
        quick_menu.popup(QCursor.pos())

    tray.activated.connect(on_tray_activated)
    tray.show()

    tray.showMessage(
        "ログインマネージャー常駐完了",
        "右下の 🔑 アイコンをクリックするとクイック操作メニューが開きます！",
        QSystemTrayIcon.Information,
        4000
    )

    manager_win.show()
    manager_win.raise_()
    manager_win.activateWindow()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
