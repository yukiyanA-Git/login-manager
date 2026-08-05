from PySide6.QtWidgets import QWidget, QApplication, QMessageBox, QInputDialog
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PIL import ImageGrab

from ocr_engine import perform_ocr_on_image
from auth_hello import authenticate_windows_hello
from popup_window import FloatingPopupWindow

class ScreenSelectionOverlay(QWidget):
    def __init__(self, vault_instance, parent=None):
        super().__init__(parent)
        self.vault = vault_instance
        self.start_pos = None
        self.end_pos = None
        self.is_drawing = False
        self.current_rect = QRect()
        self.popup_ref = None
        self.register_mode_callback = None

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

    def smart_search(self):
        """
        Hyper-fast Clipboard-First Search:
        1. Checks if clipboard contains non-empty text (e.g. copied text 'Amazon' or 'Eight').
        2. If matching account found -> Instantly opens popup window (0ms delay, 100% exact match).
        3. If no clipboard match -> Opens screen selection overlay (長方形の枠) as fallback for image logos!
        """
        clip_text = QApplication.clipboard().text().strip()
        if clip_text and len(clip_text) < 60:
            matched_acc = self.vault.find_account_by_name(clip_text)
            if matched_acc:
                print(f"[Smart Search] Instant Clipboard Match: '{clip_text}' -> '{matched_acc['name']}'")
                sec_level = matched_acc.get("security_level", 1)
                if sec_level == 3:
                    auth_ok = authenticate_windows_hello(matched_acc["name"])
                    if not auth_ok:
                        QMessageBox.warning(None, "アクセス拒否", "厳重保護認証が完了しなかったためログイン情報を表示できません。")
                        return

                # Position popup at top-right of screen
                screen_geom = QApplication.primaryScreen().geometry()
                popup_pos = QPoint(screen_geom.width() - 370, 80)
                self.popup_ref = FloatingPopupWindow(matched_acc, pos=popup_pos)
                self.popup_ref.show()
                return

        # Fallback to Screen Selection Overlay if no clipboard match
        self.show_overlay()

    def show_overlay(self):
        """Standard search mode: frame company name to find and open popup."""
        self.register_mode_callback = None
        self._prepare_and_show("コピーした文字またはマウスドラッグで会社名を囲んで検索してください [Enter/Wクリックで確定]")

    def show_overlay_for_register(self, callback):
        """Register mode: frame company name or use clipboard text to auto-fill registration form!"""
        clip_text = QApplication.clipboard().text().strip()
        if clip_text and len(clip_text) < 60:
            callback(clip_text)
            return

        self.register_mode_callback = callback
        self._prepare_and_show("マウスドラッグで登録する会社名を囲んでください [自動入力します]")

    def _prepare_and_show(self, banner_text: str):
        self.banner_text = banner_text
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        self.start_pos = None
        self.end_pos = None
        self.current_rect = QRect()
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_drawing = True
            self.current_rect = QRect(self.start_pos, self.end_pos)
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_pos = event.pos()
            self.current_rect = QRect(self.start_pos, self.end_pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.end_pos = event.pos()
            self.current_rect = QRect(self.start_pos, self.end_pos).normalized()
            self.update()

    def mouseDoubleClickEvent(self, event):
        if self.current_rect and self.current_rect.width() > 10 and self.current_rect.height() > 10:
            self.process_selection()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.current_rect and self.current_rect.width() > 10:
                self.process_selection()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))

        painter.setPen(Qt.NoPen)
        banner_bg = QColor(220, 38, 38, 230) if self.register_mode_callback else QColor(17, 24, 39, 230)
        painter.setBrush(banner_bg)
        banner_rect = QRect(self.width() // 2 - 300, 24, 600, 44)
        painter.drawRoundedRect(banner_rect, 10, 10)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Meiryo", 11, QFont.Bold))
        text = getattr(self, "banner_text", "マウスドラッグで会社名を囲んでください")
        painter.drawText(banner_rect, Qt.AlignCenter, text)

        if self.current_rect and not self.current_rect.isEmpty():
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.current_rect, QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            pen_color = QColor(239, 68, 68) if self.register_mode_callback else QColor(0, 120, 212)
            pen = QPen(pen_color, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QColor(pen_color.red(), pen_color.green(), pen_color.blue(), 40))
            painter.drawRect(self.current_rect)

            dim_text = f"{self.current_rect.width()} x {self.current_rect.height()} px"
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(pen_color)
            painter.setBrush(QColor(255, 255, 255, 240))
            badge_rect = QRect(self.current_rect.left(), max(0, self.current_rect.top() - 22), 110, 20)
            painter.drawRoundedRect(badge_rect, 4, 4)
            painter.drawText(badge_rect, Qt.AlignCenter, dim_text)

    def process_selection(self):
        rect = self.current_rect
        self.close()

        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0

        x = int(rect.x() * dpr)
        y = int(rect.y() * dpr)
        w = int(rect.width() * dpr)
        h = int(rect.height() * dpr)

        captured_img = ImageGrab.grab(bbox=(x, y, x + w, y + h))

        ocr_text = perform_ocr_on_image(captured_img)
        cleaned_text = ocr_text.replace("\n", " ").replace("\r", "").strip() if ocr_text else ""
        print(f"[OCR Log] Raw: '{ocr_text}' -> Cleaned: '{cleaned_text}' (DPR: {dpr})")

        if self.register_mode_callback:
            if not cleaned_text:
                text, ok = QInputDialog.getText(
                    None, "会社名の手動入力",
                    "囲んだ画像から文字が読めませんでした。\n登録する「会社名」を入力してください:"
                )
                cleaned_text = text.strip() if ok else ""

            self.register_mode_callback(cleaned_text)
            return

        account = self.vault.find_account_by_name(cleaned_text)

        if not account:
            names = [a["name"] for a in self.vault.accounts]
            item, ok = QInputDialog.getItem(
                None, "対象アカウント選択",
                f"読み取りテキスト: '{cleaned_text if cleaned_text else '(未検出)'}'\n表示するアカウントを選択してください:",
                names, 0, False
            )
            if ok and item:
                account = self.vault.find_account_by_name(item)
            else:
                return

        sec_level = account.get("security_level", 1)

        if sec_level == 3:
            auth_ok = authenticate_windows_hello(account["name"])
            if not auth_ok:
                QMessageBox.warning(None, "アクセス拒否", "厳重保護認証が完了しなかったためログイン情報を表示できません。")
                return

        popup_pos = QPoint(rect.x() + rect.width() + 10, rect.y())
        self.popup_ref = FloatingPopupWindow(account, pos=popup_pos)
        self.popup_ref.show()
