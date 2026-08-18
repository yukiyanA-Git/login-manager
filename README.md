# 🔑 ログインマネージャー (Login Manager)

PCでのログイン作業を爆速化する軽量Windowsデスクトップアプリケーション。

---

## 🚀 無料ダウンロード ＆ インストール手順 (Step 1 & Step 2)

### 1. アプリの入手
右側の **[Releases (最新リリース)](https://github.com/yukiyanA-Git/login-manager/releases)** から **`LoginManager.zip`** をダウンロードします。

### 2. 起動方法
1. ダウンロードした **`LoginManager.zip`** を右クリックし、「すべて展開（解凍）」します。
2. 展開されたフォルダ内にある **`LoginManager.exe`** をダブルクリックするだけで即座に起動します！
   *(※Pythonのインストール作業は不要です)*

---

## ✨ 特徴・機能
- **📋 爆速クリップボード（文字コピー）優先検索**: Web上の会社名や製品名を `Ctrl+C` でコピーしてショートカット（`Alt+Z`）を押すだけで、IDとパスワードのコピーボタンが0.01秒でポップアップします。
- **➕ 画面囲み/コピー文字による会社名自動入力登録**: マウスドラッグで画面を囲んで会社名を自動プレ入力。
- **🏷️ 製品名・別名登録（最大2つ）**: 会社名（Sansan）だけでなく製品名（Eight）での自動照合に対応。
- **🔒 段階的セキュリティ保護**: `標準 (認証なし・すぐ表示)` vs `高セキュリティ (Windows Hello/顔・指紋認証要求)`。
- **☁️ Firebaseクラウド同期 ＆ 📁 CSVインポート**: 複数PC間での自動リアルタイム同期 ＆ CSV一括インポート対応。

---

## 📁 開発・ビルド方法
```bash
# ライブラリのインストール
pip install PySide6 cryptography Pillow requests winrt-Windows.Media.Ocr winrt-Windows.Security.Credentials.UI winrt-Windows.Foundation

# アプリの起動
python main.py

# 配布用 .exe のビルド
python build_exe.py
```

## 📄 ライセンス
MIT License

