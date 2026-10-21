import secrets
import string

# 安全で一般的に広く利用可能な記号セット（SQL/HTMLエスケープ問題や特殊記号拒否のある '"`<>\/,;:| 等は完全除外）
SAFE_SYMBOLS = "!@#$%*-_=+?."

# 見間違い・打ち間違いが多発する紛らわしい文字セット (数字の1, 小文字l, 大文字I, 数字0, 大文字O)
AMBIGUOUS_CHARS = "1lI0O"

def generate_password(
    length: int = 12,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = False,
    exclude_ambiguous: bool = False,
    symbols: str = SAFE_SYMBOLS
) -> str:
    """
    Pythonの secrets モジュール（OSの暗号学的乱数生成器）を使用した
    完全ランダム・法則性ゼロの強固なパスワード生成関数。
    各指定文字種から最低1文字以上を確実に含めた上でシャッフルします。
    """
    length = max(4, min(length, 64))

    upper_pool = string.ascii_uppercase
    lower_pool = string.ascii_lowercase
    digit_pool = string.digits
    symbol_pool = symbols

    if exclude_ambiguous:
        upper_pool = "".join(c for c in upper_pool if c not in AMBIGUOUS_CHARS)
        lower_pool = "".join(c for c in lower_pool if c not in AMBIGUOUS_CHARS)
        digit_pool = "".join(c for c in digit_pool if c not in AMBIGUOUS_CHARS)
        symbol_pool = "".join(c for c in symbol_pool if c not in AMBIGUOUS_CHARS)

    categories = []
    if use_upper and upper_pool:
        categories.append(upper_pool)
    if use_lower and lower_pool:
        categories.append(lower_pool)
    if use_digits and digit_pool:
        categories.append(digit_pool)
    if use_symbols and symbol_pool:
        categories.append(symbol_pool)

    # 何も選択されていない場合は安全なデフォルト（英小文字＋数字）
    if not categories:
        categories = [lower_pool or string.ascii_lowercase, digit_pool or string.digits]

    all_pool = "".join(categories)

    # 各文字種から最低1文字ずつを確保
    password_chars = []
    for cat in categories:
        if len(password_chars) < length:
            password_chars.append(secrets.choice(cat))

    # 残りの文字数をプール全体から暗号学的乱数で補完
    while len(password_chars) < length:
        password_chars.append(secrets.choice(all_pool))

    # 順序の偏りを完全排除するためシャッフル
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)

def evaluate_strength(password: str) -> tuple[int, str, str]:
    """
    パスワードの強度を評価して (スコア 0-100, 判定ラベル, カラーコード) を返します。
    """
    if not password:
        return 0, "未生成", "#9CA3AF"

    length = len(password)
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_digits = any(c in string.digits for c in password)
    has_symbols = any(c in SAFE_SYMBOLS for c in password)

    score = 0
    # 長さによるスコア
    if length >= 4:
        score += min(length * 3, 40)

    # 種類の豊富さ
    types_count = sum([has_lower, has_upper, has_digits, has_symbols])
    score += types_count * 15

    score = min(score, 100)

    if score < 35:
        return score, "注意 (PIN・簡易)", "#F59E0B"
    elif score < 60:
        return score, "普通 (日常用)", "#3B82F6"
    elif score < 85:
        return score, "強固 (推奨)", "#10B981"
    else:
        return score, "極めて強固 (最高安全)", "#059669"
