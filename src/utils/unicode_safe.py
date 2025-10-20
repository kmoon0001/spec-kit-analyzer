"""Unicode-safe print utilities to prevent encoding issues on Windows.

This module provides safe alternatives to print() that handle Unicode characters
gracefully on Windows systems with different code page settings.
"""

import os
import sys
from typing import Any


def safe_print(
    *args: Any, sep: str = " ", end: str = "\n", file: Any | None = None
) -> None:
    """Print with Unicode-safe encoding handling.

    Args:
        *args: Items to print
        sep: Separator between items
        end: End character
        file: Output file (defaults to sys.stdout)
    """
    if file is None:
        file = sys.stdout

    # Convert all arguments to strings, handling Unicode safely
    safe_args = []
    for arg in args:
        if isinstance(arg, str):
            # Replace common Unicode characters with ASCII equivalents
            safe_str = _replace_unicode_chars(str(arg))
            safe_args.append(safe_str)
        else:
            safe_args.append(str(arg))

    # Join and print
    output = sep.join(safe_args) + end

    try:
        print(output, end="", file=file)
    except UnicodeEncodeError:
        # Fallback: encode as ASCII with error handling
        safe_output = output.encode("ascii", errors="replace").decode("ascii")
        print(safe_output, end="", file=file)


def _replace_unicode_chars(text: str) -> str:
    """Replace common Unicode characters with ASCII equivalents.

    Args:
        text: Input text that may contain Unicode characters

    Returns:
        Text with Unicode characters replaced by ASCII equivalents
    """
    replacements = {
        # Common emojis and symbols
        "✅": "[OK]",
        "❌": "[FAIL]",
        "⏰": "[TIMEOUT]",
        "🔍": "[SEARCH]",
        "🛠️": "[TOOLS]",
        "📊": "[CHART]",
        "🎯": "[TARGET]",
        "🚀": "[LAUNCH]",
        "📈": "[TREND]",
        "✨": "[SPARKLE]",
        "🎉": "[CELEBRATE]",
        "🔧": "[WRENCH]",
        "📋": "[LIST]",
        "💡": "[IDEA]",
        "⭐": "[STAR]",
        "🌟": "[STAR2]",
        "🔥": "[FIRE]",
        "💯": "[100]",
        "🚨": "[ALERT]",
        "🔒": "[LOCK]",
        "🔑": "[KEY]",
        "📁": "[FOLDER]",
        "📝": "[NOTE]",
        "📄": "[DOCUMENT]",
        "📌": "[PIN]",
        "📍": "[LOCATION]",
        "📎": "[CLIP]",
        "📏": "[RULER]",
        "📐": "[TRIANGLE]",
        "📑": "[BOOKMARK]",
        "📒": "[NOTEBOOK]",
        "📓": "[NOTEBOOK2]",
        "📔": "[NOTEBOOK3]",
        "📕": "[BOOK]",
        "📖": "[OPEN_BOOK]",
        "📗": "[GREEN_BOOK]",
        "📘": "[BLUE_BOOK]",
        "📙": "[ORANGE_BOOK]",
        "📚": "[BOOKS]",
        "📛": "[BADGE]",
        "📜": "[SCROLL]",
        "📞": "[PHONE]",
        "📟": "[PAGER]",
        "📠": "[FAX]",
        "📡": "[SATELLITE]",
        "📢": "[SPEAKER]",
        "📣": "[MEGAPHONE]",
        "📤": "[OUTBOX]",
        "📥": "[INBOX]",
        "📦": "[PACKAGE]",
        "📧": "[EMAIL]",
        "📨": "[INCOMING_ENVELOPE]",
        "📩": "[ENVELOPE_ARROW]",
        "📪": "[MAILBOX_CLOSED]",
        "📫": "[MAILBOX_OPEN]",
        "📬": "[MAILBOX_WITH_MAIL]",
        "📭": "[MAILBOX_WITH_NO_MAIL]",
        "📮": "[POSTBOX]",
        "📯": "[POSTAL_HORN]",
        "📰": "[NEWSPAPER]",
        "📱": "[MOBILE]",
        "📲": "[MOBILE_ARROW]",
        "📳": "[VIBRATION]",
        "📴": "[MOBILE_OFF]",
        "📶": "[SIGNAL]",
        "📷": "[CAMERA]",
        "📸": "[CAMERA_FLASH]",
        "📹": "[VIDEO_CAMERA]",
        "📺": "[TV]",
        "📻": "[RADIO]",
        "📼": "[VHS]",
        "📽️": "[FILM_PROJECTOR]",
        "📾": "[FILM_FRAMES]",
        "📿": "[PRAYER_BEADS]",
        "🔀": "[SHUFFLE]",
        "🔁": "[REPEAT]",
        "🔂": "[REPEAT_ONE]",
        "🔃": "[REFRESH]",
        "🔄": "[ARROW_REFRESH]",
        "🔅": "[LOW_BRIGHTNESS]",
        "🔆": "[HIGH_BRIGHTNESS]",
        "🔇": "[MUTE]",
        "🔈": "[SOUND]",
        "🔉": "[SOUND_UP]",
        "🔊": "[LOUD_SOUND]",
        "🔋": "[BATTERY]",
        "🔌": "[PLUG]",
        "🔎": "[MAG_RIGHT]",
        "🔏": "[LOCK_WITH_PEN]",
        "🔐": "[LOCK_WITH_KEY]",
        "🔓": "[UNLOCK]",
        "🔔": "[BELL]",
        "🔕": "[NO_BELL]",
        "🔖": "[BOOKMARK]",
        "🔗": "[LINK]",
        "🔘": "[RADIO_BUTTON]",
        "🔙": "[BACK]",
        "🔚": "[END]",
        "🔛": "[ON]",
        "🔜": "[SOON]",
        "🔝": "[TOP]",
        "🔞": "[UNDERAGE]",
        "🔟": "[KEYCAP_TEN]",
        "🔠": "[CAPITAL_ABCD]",
        "🔡": "[ABCD]",
        "🔢": "[1234]",
        "🔣": "[SYMBOLS]",
        "🔤": "[ABC]",
    }

    result = text
    for unicode_char, ascii_replacement in replacements.items():
        result = result.replace(unicode_char, ascii_replacement)

    return result


def setup_unicode_safe_environment() -> None:
    """Setup environment for Unicode-safe operations on Windows."""
    if sys.platform == "win32":
        # Set environment variables for better Unicode support
        os.environ["PYTHONIOENCODING"] = "utf-8"

        # Try to set console code page to UTF-8 if possible
        try:
            import subprocess

            subprocess.run(["chcp", "65001"], shell=True, capture_output=True)
        except Exception:
            # Ignore if chcp command fails
            pass


def test_unicode_safety() -> None:
    """Test that Unicode characters are handled safely."""
    test_strings = [
        "✅ Analysis completed successfully",
        "❌ Analysis failed with error",
        "⏰ Analysis timed out",
        "🔍 Searching for issues...",
        "📊 Generating report",
        "🎯 Target achieved",
        "🚀 Launching application",
        "📈 Performance improved",
        "✨ New features added",
        "🎉 Congratulations!",
    ]

    print("Testing Unicode safety:")
    for test_str in test_strings:
        safe_print(f"Original: {test_str}")
        safe_print(f"Safe: {_replace_unicode_chars(test_str)}")
        print()


if __name__ == "__main__":
    setup_unicode_safe_environment()
    test_unicode_safety()
