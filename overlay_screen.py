import os
from PySide6.QtWidgets import (
    QWidget, QRubberBand, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QRect, QPoint, QTimer
from PySide6.QtGui import QPainter, QColor, QCursor, QFont
from PIL import ImageGrab

from ocr_engine import WinRTOcrEngine
from popup_window import FloatingPopupWindow
from auth_hello import WindowsHelloAuthenticator
from win_title_helper import get_active_window_title
from logo_matcher import pil_to_base64

class ScreenSelectionOverlay(QWidget):
    def __init__(self, vault_instance, parent=None):
        super().__init__(parent)
        self.vault = vault_instance
        self.ocr = WinRTOcrEngine()
        self.authenticator = WindowsHelloAuthenticator()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)

        self.rubber_band = None
        self.origin = QPoint()
        self.is_register_mode = False
        self.register_callback = None
        self.popup_win = None

    def smart_search(self):
        # Step 1: Clipboard Text Check
        clip_text = QApplication.clipboard().text().strip()
        if clip_text and len(clip_text) < 100:
            matched_acc = self.vault.find_account_by_name(clip_text)
            if matched_acc:
                print(f"[Smart Search] Clipboard matched: '{clip_text}' -> {matched_acc.get('name')}")
                self.handle_account_found(matched_acc)
                return

        # Step 2: Active Window Title Check
        win_title = get_active_window_title()
        if win_title:
            matched_acc = self.vault.find_account_by_window_title(win_title)
            if matched_acc:
                print(f"[Smart Search] Window title matched: '{win_title}' -> {matched_acc.get('name')}")
                self.handle_account_found(matched_acc)
                return

        # Step 3: Friendly prompt without forced OCR popup
        hint_str = f"「{clip_text}」" if clip_text else f"ウィンドウ「{win_title[:30]}」" if win_title else "テキスト"
        reply = QMessageBox.question(
            None,
            "ログイン検索 - 見つかりませんでした",
            f"コピーした文字または画面タイトル【{hint_str}】に該当する登録情報が見つかりませんでした。\n\n"
            f"画面上のロゴやアイコン枠をドラッグして、画像/OCR読み込み検索を行いますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.show_overlay()

    def show_overlay(self):
        self.is_register_mode = False
        self.register_callback = None
        self._set_fullscreen_geometry()
        self.show()
        self.raise_()
        self.activateWindow()

    def show_overlay_for_register(self, callback):
        self.is_register_mode = True
        self.register_callback = callback
        self._set_fullscreen_geometry()
        self.show()
        self.raise_()
        self.activateWindow()

    def _set_fullscreen_geometry(self):
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        text = "➕ 画面上の会社名ロゴ/アイコンをドラッグして自動入力登録" if self.is_register_mode else "🔍 画面上の文字/ロゴマークをドラッグして囲む (ESCキーでキャンセル)"
        painter.drawText(20, 40, text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            if not self.rubber_band:
                self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
            self.rubber_band.setGeometry(QRect(self.origin, self.origin))
            self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if self.rubber_band and self.origin:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rubber_band:
            selection_rect = self.rubber_band.geometry()
            self.rubber_band.hide()
            self.hide()

            if selection_rect.width() > 10 and selection_rect.height() > 10:
                QTimer.singleShot(100, lambda: self.process_selection(selection_rect))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.rubber_band:
                self.rubber_band.hide()
            self.hide()

    def process_selection(self, rect: QRect):
        cursor_pos = QCursor.pos()

        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio()

        x = int(rect.x() * dpr)
        y = int(rect.y() * dpr)
        w = int(rect.width() * dpr)
        h = int(rect.height() * dpr)

        # Capture cropped PIL Image
        try:
            bbox = (x, y, x + w, y + h)
            captured_img = ImageGrab.grab(bbox=bbox)
            captured_b64 = pil_to_base64(captured_img)
        except Exception as e:
            print(f"Error capturing image region: {e}")
            captured_img = None
            captured_b64 = ""

        detected_text = self.ocr.recognize_region(x, y, w, h)
        print(f"[OCR Text Detected]: '{detected_text}'")

        if self.is_register_mode:
            if self.register_callback:
                self.register_callback(detected_text, captured_b64)
            return

        # 1. Try text OCR match first
        if detected_text:
            matched_acc = self.vault.find_account_by_name(detected_text)
            if matched_acc:
                print(f"[Search Result] Text OCR match: '{detected_text}' -> {matched_acc.get('name')}")
                self.handle_account_found(matched_acc, cursor_pos)
                return

        # 2. Try Visual Logo Image Similarity match
        if captured_img:
            logo_matched_acc = self.vault.find_account_by_logo(captured_img)
            if logo_matched_acc:
                print(f"[Search Result] Visual Logo Image match: -> {logo_matched_acc.get('name')}")
                self.handle_account_found(logo_matched_acc, cursor_pos)
                return

        QMessageBox.information(
            None, "未登録",
            f"認識された文字/ロゴ: 「{detected_text if detected_text else '画像ロゴ'}」\n\n該当するアカウント情報は未登録です。「アカウント管理」画面から新規追加を行ってください。"
        )

    def handle_account_found(self, acc_data: dict, pos: QPoint = None):
        if not pos:
            pos = QCursor.pos()

        sec_level = acc_data.get("security_level", 1)
        if sec_level == 3:
            service_name = acc_data.get("name", "アカウント")
            is_authed = self.authenticator.authenticate(
                reason=f"「{service_name}」のパスワード閲覧セキュリティ保護"
            )
            if not is_authed:
                QMessageBox.warning(None, "認証失敗", "本人確認認証に失敗しました。パスワードを表示できません。")
                return

        if self.popup_win:
            self.popup_win.close()

        self.popup_win = FloatingPopupWindow(acc_data, pos=pos)
        self.popup_win.show()
