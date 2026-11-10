#!/usr/bin/env python3
"""⚡Kizen-Notes — Local notes app (PySide6)."""

from __future__ import annotations

import os
import sqlite3
import sys
import shutil
import uuid
import re
import json
import html as html_lib
import zipfile
import tempfile
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import (
    QFont, QPalette, QKeySequence, QShortcut, QPixmap, QImage, QColor,
    QTextCharFormat, QTextCursor, QTextDocument, QIcon
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QLabel, QPushButton, QLineEdit, QTextEdit,
    QScrollArea, QDialog, QMessageBox, QSizePolicy, QMenu, QButtonGroup,
    QFileDialog, QWidgetAction, QGraphicsDropShadowEffect
)

try:
    from __version__ import __version__, __repo__
except ImportError:
    __version__ = "1.0.0"          # ✅ FIX: 1.0.0a1 → 1.0.0
    __repo__ = "uaydemir633-dotcom/Kizen-Notes"


# ============================================================
# LICENSE
# ============================================================
LICENSE_TEXT = """MIT License

Copyright (c) 2026 Kizen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


# ============================================================
# THEME & CONFIG
# ============================================================
PALETTE = {
    "bg_app":       ("#FFFFFF", "#202124"),
    "bg_header":    ("#FFFFFF", "#202124"),
    "bg_sidebar":   ("#FFFFFF", "#202124"),
    "bg_input":     ("#F1F3F4", "#525355"),
    "bg_hover":     ("#F1F3F4", "#3C4043"),
    "bg_card":      ("#FFFFFF", "#2D2E30"),
    "text_hi":      ("#202124", "#E8EAED"),
    "text_mid":     ("#5F6368", "#9AA0A6"),
    "text_lo":      ("#80868B", "#80868B"),
    "accent":       "#FDD663",
    "accent_dark":  "#F9AB00",
    "accent_bg":    ("#FEF7E0", "#41331C"),
    "accent_text":  ("#202124", "#E8EAED"),
    "danger":       ("#D93025", "#F28B82"),
    "success":      ("#188038", "#81C995"),
    "border":       ("#E0E0E0", "#5F6368"),
    "card_border":  ("#DADCE0", "#5F6368"),
    "avatar_bg":    "#1E8E3E",
}

NOTE_COLORS = {
    "default": ("#FFFFFF", "#2D2E30"),
    "red":     ("#F28B82", "#5C2B29"),
    "orange":  ("#FBBC04", "#614A19"),
    "yellow":  ("#FFF475", "#635D19"),
    "green":   ("#CCFF90", "#345920"),
    "blue":    ("#CBF0F8", "#2D555E"),
    "purple":  ("#D7AEFB", "#42275E"),
}

_light_mode = False
_theme_mode = "system"       # FIX #6
_body_font_size = 13         # FIX #10


def pal(key: str):
    v = PALETTE[key]
    if isinstance(v, (tuple, list)):
        return v[0] if _light_mode else v[1]
    return v


def note_color(name: str) -> str:
    c = NOTE_COLORS.get(name, NOTE_COLORS["default"])
    return c[0] if _light_mode else c[1]


def set_mode(mode: str):
    # FIX #6: temayı config'e yaz
    global _light_mode, _theme_mode
    _theme_mode = mode
    try:
        cfg = _load_config()
        cfg["theme"] = mode
        _save_config(cfg)
    except Exception:
        pass
    if mode == "light":
        _light_mode = True
    elif mode == "dark":
        _light_mode = False
    else:
        try:
            hints = QApplication.styleHints()
            _light_mode = (hints.colorScheme() == Qt.ColorScheme.Light)
        except Exception:
            app = QApplication.instance()
            if app:
                _light_mode = app.palette().color(QPalette.Window).lightness() > 128


_FONT_CACHE: dict = {}
def _font(size: int = 12, bold: bool = False, family: str | None = None, italic: bool = False) -> QFont:
    key = (size, bool(bold), family, bool(italic))
    if key in _FONT_CACHE: return _FONT_CACHE[key]
    f = QFont()
    if family: f.setFamily(family)
    f.setPointSize(size); f.setBold(bold); f.setItalic(italic)
    _FONT_CACHE[key] = f
    return f


def _add_shadow(widget, blur=20, y=4, alpha=60):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)
    return effect


def _highlight_text(text: str, query: str) -> str:
    escaped = html_lib.escape(text)
    if not query or not query.strip():
        return escaped
    try:
        pattern = re.compile(re.escape(query.strip()), re.IGNORECASE)
        return pattern.sub(
            lambda m: f'<span style="background:#FFEB3B; color:#000; border-radius:2px; padding:0 1px;">{m.group()}</span>',
            escaped,
        )
    except re.error:
        return escaped


def _human_date(dt_str: str) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt_str
    now = datetime.now()
    diff = now - dt
    secs = int(diff.total_seconds())
    # FIX #11: gelecek tarihi doğru göster
    if secs < 0:
        return dt.strftime("%b %d, %H:%M")
    if secs < 45:
        return "Just now"
    if secs < 3600:
        return f"{secs // 60} min ago"
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    days = (now.date() - dt.date()).days
    if days == 1:
        return f"Yesterday {dt.strftime('%H:%M')}"
    if days < 7:
        wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return wd[dt.weekday()]
    months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if dt.year == now.year:
        return f"{months_en[dt.month-1]} {dt.day}"
    return f"{months_en[dt.month-1]} {dt.day}, {dt.year}"


# ---- Tiny JSON config ----
_KIZEN_DIR = os.path.expanduser("~/.kizen")
ASSETS_DIR = os.path.join(_KIZEN_DIR, "assets")
DB_PATH = os.path.join(_KIZEN_DIR, "notes.db")
CONFIG_PATH = os.path.join(_KIZEN_DIR, "config.json")
IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")


def _load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_config(cfg: dict):
    try:
        os.makedirs(_KIZEN_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def _apply_font_size(size: int):
    global _body_font_size
    _body_font_size = size
    cfg = _load_config()
    cfg["font_size"] = size
    _save_config(cfg)


def build_qss() -> str:
    bg_app = pal("bg_app"); bg_header = pal("bg_header"); bg_sidebar = pal("bg_sidebar")
    bg_input = pal("bg_input"); bg_hover = pal("bg_hover"); bg_card = pal("bg_card")
    text_hi = pal("text_hi"); text_mid = pal("text_mid"); text_lo = pal("text_lo")
    accent = pal("accent"); accent_dark = pal("accent_dark"); border = pal("border")
    accent_bg = pal("accent_bg"); accent_text = pal("accent_text"); card_border = pal("card_border")

    return f"""
    QMainWindow {{ background-color: {bg_app}; }}
    QWidget {{ color: {text_hi}; }}
    QLabel {{ background: transparent; }}

    /* ---------- Header ---------- */
    QFrame#HeaderBar {{ background-color: {bg_header}; }}
    QPushButton#HeaderIcon {{
        background: transparent; border: none; border-radius: 20px;
        font-size: 18px; color: {text_mid}; text-align: center; padding: 0;
    }}
    QPushButton#HeaderIcon:hover {{ background-color: {bg_hover}; color: {text_hi}; }}
    QLabel#AppLogo {{ font-size: 18px; font-weight: 600; color: {text_hi}; }}

    /* ---------- Sidebar ---------- */
    QFrame#Sidebar {{ background-color: {bg_sidebar}; }}
    QFrame#Sidebar QPushButton {{
        background: transparent; border: none; text-align: left;
        padding: 0 24px 0 20px; border-radius: 0 25px 25px 0;
        color: {text_hi}; font-size: 13px; height: 48px;
    }}
    QFrame#Sidebar QPushButton[collapsed="true"] {{
        padding: 0 8px 0 4px;
        text-align: center;
    }}
    QFrame#Sidebar QPushButton:hover {{ background-color: {bg_hover}; }}
    QFrame#Sidebar QPushButton:checked {{
        background-color: {accent_bg};
        color: {accent_text};
        font-weight: 500;
    }}

    /* ---------- Note cards ---------- */
    QFrame#NoteCard {{
        background-color: {bg_card};
        border-radius: 8px;
        border: 1px solid {card_border};
    }}
    QFrame#NoteCard:hover {{ border-color: {text_lo}; }}

    /* ---------- Search bar ---------- */
    QFrame#SearchBar {{
        background-color: {bg_input};
        border-radius: 8px;
        border: 1px solid transparent;
    }}
    QFrame#SearchBar[focused="true"] {{
        background-color: {bg_card};
        border: 1px solid transparent;
    }}

    /* ---------- Take-a-note bar ---------- */
    QFrame#InlineNote {{
        background-color: {bg_card};
        border-radius: 8px;
        border: 1px solid {card_border};
    }}
    QFrame#InlineNote:hover {{ border-color: {text_lo}; }}

    /* ---------- Buttons ---------- */
    QPushButton {{
        background-color: transparent; color: {text_hi};
        border: none; padding: 6px 12px; border-radius: 18px; text-align: left;
    }}
    QPushButton:hover {{ background-color: {bg_hover}; }}

    QPushButton#Fab {{
        background-color: {accent}; color: #000000; border-radius: 28px;
        font-weight: bold; font-size: 26px; text-align: center;
    }}
    QPushButton#Fab:hover {{ background-color: {accent_dark}; }}

    /* ---------- Inputs ---------- */
    QLineEdit, QTextEdit {{
        background-color: transparent; color: {text_hi}; border: none;
        border-radius: 8px; padding: 8px 12px;
        selection-background-color: {accent};
        selection-color: #000;
    }}
    QLineEdit#TransparentInput, QTextEdit#TransparentInput {{
        background: transparent; border: none; padding: 2px; font-size: 14px;
    }}

    /* ---------- Scroll ---------- */
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {border}; min-height: 24px; border-radius: 4px; }}
    QScrollBar::handle:vertical:hover {{ background: {text_lo}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

    /* ---------- Menu ---------- */
    QMenu {{
        background-color: {bg_card}; color: {text_hi};
        border: 1px solid {border}; border-radius: 4px; padding: 6px 0;
    }}
    QMenu::item {{ padding: 8px 24px 8px 16px; border-radius: 0; font-size: 13px; }}
    QMenu::item:selected {{ background-color: {bg_hover}; }}
    QMenu::separator {{ height: 1px; background: {border}; margin: 4px 0; }}

    /* ---------- Labels ---------- */
    QLabel#SectionHeader {{ color: {text_mid}; padding: 8px 24px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; }}
    QLabel#NoteTitle {{ color: {text_hi}; font-weight: 500; }}
    QLabel#NotePreview {{ color: {text_mid}; }}
    QLabel#Toast {{
        background-color: {bg_card}; border: 1px solid {border};
        border-radius: 8px; padding: 10px 20px;
    }}

    QToolTip {{
        background-color: {bg_card}; color: {text_hi};
        border: 1px solid {border}; border-radius: 4px; padding: 4px 8px;
    }}
    """


def _apply_theme(app: QApplication):
    app.setStyleSheet(build_qss())


# ============================================================
# HELPERS
# ============================================================
def _fit_window_size(w: int, h: int, mw: int = 40, mh: int = 90) -> tuple[int, int]:
    screen = QApplication.primaryScreen().availableGeometry()
    return max(200, min(w, screen.width() - mw)), max(150, min(h, screen.height() - mh))


def _center_dialog(dialog: QDialog, parent: QWidget | None, w: int, h: int):
    w, h = _fit_window_size(w, h)
    dialog.resize(w, h)
    if parent:
        try:
            pg = parent.geometry()
            dialog.move(pg.center().x() - w // 2, pg.center().y() - h // 2)
        except Exception:
            pass


class ClickableFrame(QFrame):
    clicked = Signal()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class Toast(QLabel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(_font(13))
        _add_shadow(self, blur=24, y=4, alpha=80)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, duration: int = 2000):
        self.setText(text)
        self.adjustSize()
        p = self.parentWidget()
        if p:
            self.move(max(0, (p.width() - self.width()) // 2), int(p.height() * 0.04))
        super().show(); self.raise_(); self._timer.start(duration)


# ============================================================
# DATABASE
# ============================================================
class NotesDB:
    def __init__(self):
        os.makedirs(_KIZEN_DIR, exist_ok=True)
        os.makedirs(ASSETS_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._init_schema()

    def _init_schema(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                plain_body TEXT NOT NULL DEFAULT '',
                color TEXT NOT NULL DEFAULT 'default',
                pinned INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                image_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS note_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                title TEXT,
                body TEXT,
                color TEXT,
                image_path TEXT,
                saved_at TEXT NOT NULL,
                FOREIGN KEY(note_id) REFERENCES notes(id)
            )
        """)
        self.cursor.execute("PRAGMA table_info(notes)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if "plain_body" not in columns:
            self.cursor.execute("ALTER TABLE notes ADD COLUMN plain_body TEXT NOT NULL DEFAULT ''")
        self.conn.commit()

    def _html_to_plain(self, html_text: str) -> str:
        if not html_text: return ""
        doc = QTextDocument()
        doc.setHtml(html_text)
        return doc.toPlainText()

    def add(self, title: str, body: str, color: str, pinned: bool, image_path: str) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plain = self._html_to_plain(body)
        self.cursor.execute(
            "INSERT INTO notes (title, body, plain_body, color, pinned, status, image_path, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)",
            (title, body, plain, color, 1 if pinned else 0, image_path, now, now),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update(self, note_id: int, title: str, body: str, color: str, pinned: bool,
               image_path: str, skip_history: bool = False):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plain = self._html_to_plain(body)
        if not skip_history:
            row = self.get(note_id)
            if row:
                self.cursor.execute(
                    "INSERT INTO note_history (note_id, title, body, color, image_path, saved_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (note_id, row["title"], row["body"], row["color"], row["image_path"], row["updated_at"])
                )
        self.cursor.execute(
            "UPDATE notes SET title=?, body=?, plain_body=?, color=?, pinned=?, image_path=?, updated_at=? WHERE id=?",
            (title, body, plain, color, 1 if pinned else 0, image_path, now, note_id),
        )
        self.conn.commit()

    def restore_version(self, note_id: int, title: str, body: str, color: str, image_path: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plain = self._html_to_plain(body)
        self.cursor.execute(
            "UPDATE notes SET title=?, body=?, plain_body=?, color=?, image_path=?, updated_at=? WHERE id=?",
            (title, body, plain, color, image_path or "", now, note_id),
        )
        self.conn.commit()

    def toggle_pin(self, note_id: int):
        self.cursor.execute("UPDATE notes SET pinned = 1 - pinned, updated_at=? WHERE id=?",
                            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note_id))
        self.conn.commit()

    def set_status(self, note_id: int, status: str):
        self.cursor.execute("UPDATE notes SET status=?, updated_at=? WHERE id=?",
                            (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note_id))
        self.conn.commit()

    def delete_permanently(self, note_id: int):
        row = self.get(note_id)
        if row and row["image_path"] and os.path.exists(row["image_path"]):
            try: os.remove(row["image_path"])
            except Exception: pass
        self.cursor.execute("DELETE FROM note_history WHERE note_id=?", (note_id,))
        self.cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
        self.conn.commit()

    def delete_tag_from_all(self, tag: str):
        # FIX #3: plain_body ve body (HTML) birlikte güncelle
        pat = rf"#{re.escape(tag)}\b\s?"
        self.cursor.execute("SELECT id, plain_body, body FROM notes")
        rows = self.cursor.fetchall()
        for row in rows:
            plain = row["plain_body"] or ""
            if f"#{tag}" not in plain:
                continue
            new_plain = re.sub(pat, "", plain)
            new_html = re.sub(pat, "", row["body"] or "")
            self.cursor.execute(
                "UPDATE notes SET plain_body=?, body=? WHERE id=?",
                (new_plain, new_html, row["id"]),
            )
        self.conn.commit()

    def get(self, note_id: int):
        self.cursor.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        return self.cursor.fetchone()

    def get_history(self, note_id: int):
        self.cursor.execute("SELECT * FROM note_history WHERE note_id=? ORDER BY saved_at DESC", (note_id,))
        return self.cursor.fetchall()

    def count_by_status(self) -> dict:
        self.cursor.execute("SELECT status, COUNT(*) as c FROM notes GROUP BY status")
        return {row["status"]: row["c"] for row in self.cursor.fetchall()}

    def count_pinned_active(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM notes WHERE status='active' AND pinned=1")
        return self.cursor.fetchone()[0]

    def list_all(self, filter_mode: str = "all", search: str = ""):
        q = "SELECT * FROM notes WHERE 1=1"
        params = []

        if filter_mode == "all": q += " AND status='active'"
        elif filter_mode == "pinned": q += " AND status='active' AND pinned=1"
        elif filter_mode == "archive": q += " AND status='archived'"
        elif filter_mode == "trash": q += " AND status='trash'"
        elif filter_mode.startswith("color:"):
            q += " AND status='active' AND color=?"
            params.append(filter_mode.split(":", 1)[1])
        elif filter_mode.startswith("tag:"):
            tag = filter_mode.split(":", 1)[1]
            q += " AND status='active' AND plain_body LIKE ?"
            params.append(f"%#{tag}%")

        if search.strip():
            q += " AND (LOWER(title) LIKE ? OR LOWER(plain_body) LIKE ?)"
            s = f"%{search.lower().strip()}%"
            params.extend([s, s])

        if filter_mode == "trash": q += " ORDER BY updated_at DESC"
        else: q += " ORDER BY pinned DESC, updated_at DESC"

        self.cursor.execute(q, params)
        return self.cursor.fetchall()

    def get_all_tags(self):
        self.cursor.execute("SELECT plain_body FROM notes WHERE status='active'")
        tags = set()
        for row in self.cursor.fetchall():
            if not row["plain_body"]: continue
            found = re.findall(r"#([a-zA-Z0-9_]+)", row["plain_body"])
            for f in found:
                tags.add(f)
        return sorted(list(tags))

    def note_to_markdown(self, note_id: int) -> str:
        row = self.get(note_id)
        if not row: return ""
        doc = QTextDocument()
        doc.setHtml(row["body"])
        parts = [f"# {row['title'] or 'Untitled'}", ""]
        if row["image_path"] and os.path.exists(row["image_path"]):
            parts.append(f"![image](assets/{os.path.basename(row['image_path'])})")
            parts.append("")
        parts.append(doc.toPlainText())
        parts.append("")
        parts.append(f"---\n*Last updated: {row['updated_at']}*")
        return "\n".join(parts)

    def export_all_markdown(self, dir_path: str) -> int:
        os.makedirs(dir_path, exist_ok=True)
        self.cursor.execute("SELECT * FROM notes WHERE status='active'")
        rows = self.cursor.fetchall()
        for row in rows:
            doc = QTextDocument()
            doc.setHtml(row["body"])
            safe = re.sub(r"[^\w\s\-]", "", row["title"] or f"note_{row['id']}")[:60].strip()
            if not safe: safe = f"note_{row['id']}"
            parts = [f"# {row['title'] or 'Untitled'}", ""]
            if row["image_path"]:
                parts.append(f"![image](../assets/{os.path.basename(row['image_path'])})")
                parts.append("")
            parts.append(doc.toPlainText())
            fname = f"{safe}.md"
            fpath = os.path.join(dir_path, fname)
            counter = 1
            while os.path.exists(fpath):
                fname = f"{safe}_{counter}.md"
                fpath = os.path.join(dir_path, fname)
                counter += 1
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("\n".join(parts))
        return len(rows)

    def export_backup_zip(self, zip_path: str):
        # FIX #12: VACUUM INTO ile tutarlı snapshot
        tmp_db = os.path.join(tempfile.gettempdir(), f"kizen_{uuid.uuid4().hex}.db")
        try:
            try:
                safe = tmp_db.replace("'", "''")
                self.cursor.execute(f"VACUUM INTO '{safe}'")
            except Exception:
                self.conn.commit()
                shutil.copy2(DB_PATH, tmp_db)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(tmp_db, "notes.db")
                if os.path.exists(ASSETS_DIR):
                    for fname in os.listdir(ASSETS_DIR):
                        fp = os.path.join(ASSETS_DIR, fname)
                        if os.path.isfile(fp):
                            z.write(fp, f"assets/{fname}")
        finally:
            if os.path.exists(tmp_db):
                try: os.remove(tmp_db)
                except Exception: pass

    def close(self):
        try: self.conn.close()
        except Exception: pass


# ============================================================
# NOTE CARD
# ============================================================
class NoteCard(QFrame):
    clicked = Signal(int)
    menu_requested = Signal(int, object)
    copy_requested = Signal(int)

    def __init__(self, row, parent: QWidget | None = None, search: str = ""):
        super().__init__(parent)
        self.setObjectName("NoteCard")
        self.note_id = row["id"]
        self._color_name = row["color"]
        self._pinned = bool(row["pinned"])
        self._raw_title = row["title"] or ""
        self._plain_body = row["plain_body"] or ""

        self.setMinimumHeight(110)
        self.setMaximumWidth(240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(8)

        # Image
        if row["image_path"] and os.path.exists(row["image_path"]):
            pixmap = QPixmap(row["image_path"])
            if not pixmap.isNull():
                img_lbl = QLabel()
                scaled_pixmap = pixmap.scaled(240, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_lbl.setPixmap(scaled_pixmap)
                img_lbl.setStyleSheet("border-radius: 4px;")
                img_lbl.setAlignment(Qt.AlignCenter)
                v.addWidget(img_lbl)

        # Title + hover actions
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(4)

        raw_title = self._raw_title or ("Untitled" if self._plain_body else "")
        if raw_title:
            title_lbl = QLabel()
            title_lbl.setObjectName("NoteTitle")
            title_lbl.setFont(_font(14, bold=True))
            title_lbl.setWordWrap(True)
            if search.strip():
                title_lbl.setTextFormat(Qt.RichText)
                title_lbl.setText(_highlight_text(raw_title, search))
            else:
                title_lbl.setText(raw_title)
            hdr.addWidget(title_lbl, 1)
        else:
            hdr.addStretch(1)

        if self._pinned:
            pin_lbl = QLabel("📌")
            pin_lbl.setFont(_font(11))
            hdr.addWidget(pin_lbl)

        # Hover action buttons
        self._hover_btns = []

        self.copy_btn = QPushButton("📋")
        self.copy_btn.setFixedSize(24, 24)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setToolTip("Copy text")
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 12px;
                font-size: 11px; text-align: center; padding: 0; }}
            QPushButton:hover {{ background: {pal('bg_hover')}; }}
        """)
        self.copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.note_id))
        self.copy_btn.hide()
        hdr.addWidget(self.copy_btn)
        self._hover_btns.append(self.copy_btn)

        self.more_btn = QPushButton("⋮")
        self.more_btn.setFixedSize(24, 24)
        self.more_btn.setCursor(Qt.PointingHandCursor)
        self.more_btn.setToolTip("More options")
        self.more_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 12px;
                font-size: 14px; font-weight: bold; text-align: center; padding: 0;
                color: {pal('text_mid')}; }}
            QPushButton:hover {{ background: {pal('bg_hover')}; color: {pal('text_hi')}; }}
        """)
        self.more_btn.clicked.connect(self._emit_menu)
        self.more_btn.hide()
        hdr.addWidget(self.more_btn)
        self._hover_btns.append(self.more_btn)

        v.addLayout(hdr)

        # Body text
        plain_body = self._plain_body.replace("[ ]", "☐").replace("[x]", "☑").replace("[X]", "☑")
        if len(plain_body) > 200:
            plain_body = plain_body[:200].rstrip() + "…"

        if plain_body.strip():
            body_lbl = QLabel()
            body_lbl.setObjectName("NotePreview")
            body_lbl.setFont(_font(12))
            body_lbl.setWordWrap(True)
            body_lbl.setTextInteractionFlags(Qt.NoTextInteraction)
            if search.strip():
                body_lbl.setTextFormat(Qt.RichText)
                body_lbl.setText(_highlight_text(plain_body, search))
            else:
                body_lbl.setText(plain_body)
            v.addWidget(body_lbl, 1)

        v.addStretch(1)

        # Label chips (tags found in body)
        tags = re.findall(r"#([a-zA-Z0-9_]+)", self._plain_body)
        if tags:
            tag_row = QHBoxLayout()
            tag_row.setContentsMargins(0, 0, 0, 0)
            tag_row.setSpacing(4)
            for t in tags[:3]:
                chip = QLabel(t)
                chip.setFont(_font(10))
                chip.setStyleSheet(f"""
                    background-color: {pal('bg_hover')}; color: {pal('text_mid')};
                    border-radius: 10px; padding: 2px 10px; font-size: 11px;
                """)
                tag_row.addWidget(chip)
            tag_row.addStretch(1)
            v.addLayout(tag_row)

        # Date
        date_lbl = QLabel(_human_date(row["updated_at"]))
        date_lbl.setFont(_font(10))
        date_lbl.setStyleSheet(f"color: {pal('text_lo')};")
        date_lbl.setToolTip(row["updated_at"])
        v.addWidget(date_lbl)

        self._apply_color()

    def _emit_menu(self):
        pos = self.more_btn.mapToGlobal(self.more_btn.rect().bottomRight())
        self.menu_requested.emit(self.note_id, pos)

    def enterEvent(self, event):
        for b in self._hover_btns:
            b.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        for b in self._hover_btns:
            b.hide()
        super().leaveEvent(event)

    def _apply_color(self):
        bg = note_color(self._color_name)
        border_col = pal("card_border")
        self.setStyleSheet(f"""
            QFrame#NoteCard {{
                background-color: {bg};
                border-radius: 8px;
                border: 1px solid {border_col};
            }}
            QFrame#NoteCard:hover {{ border-color: {pal('text_lo')}; }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.note_id)
        elif event.button() == Qt.RightButton:
            self.menu_requested.emit(self.note_id, event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        event.accept()


# ============================================================
# HISTORY DIALOG
# ============================================================
class HistoryDialog(QDialog):
    def __init__(self, parent, db: NotesDB, note_id: int):
        super().__init__(parent)
        self.setWindowTitle("Version history")
        self.setModal(True)
        _center_dialog(self, parent, 400, 500)
        self.db = db
        self.note_id = note_id

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Version history")
        title.setFont(_font(18, bold=True))
        v.addWidget(title)
        hint = QLabel("Restore any previous version of this note. Unsaved changes will be lost.")
        hint.setStyleSheet(f"color: {pal('text_lo')}; font-size: 12px;")
        hint.setWordWrap(True)
        v.addWidget(hint)
        v.addSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(10)

        history = db.get_history(note_id)
        if not history:
            cl.addWidget(QLabel("No previous versions yet."))
        else:
            for i, row in enumerate(history):
                row_frame = QFrame()
                row_frame.setStyleSheet(f"background: {pal('bg_card')}; border-radius: 8px;")
                rl = QHBoxLayout(row_frame)
                rl.setContentsMargins(14, 12, 14, 12)
                info = QVBoxLayout()
                time_lbl = QLabel(row["saved_at"]); time_lbl.setFont(_font(12, bold=True))
                info.addWidget(time_lbl)
                sub_lbl = QLabel("Version")
                sub_lbl.setStyleSheet(f"color: {pal('text_lo')}; font-size: 11px;")
                info.addWidget(sub_lbl)
                rl.addLayout(info); rl.addStretch(1)
                restore_btn = QPushButton("Restore")
                restore_btn.setFixedSize(74, 30)
                restore_btn.clicked.connect(lambda _c=False, r=row: self._restore(r))
                rl.addWidget(restore_btn)
                cl.addWidget(row_frame)
        cl.addStretch(1)
        scroll.setWidget(content)
        v.addWidget(scroll, 1)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(38)
        close_btn.clicked.connect(self.reject)
        v.addWidget(close_btn)

    def _restore(self, row):
        # FIX D: onay iste — editor'deki unsaved değişiklikler kaybolacak
        reply = QMessageBox.question(
            self, "Restore version",
            "Restore this version?\n\nUnsaved changes in the editor will be lost.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.db.restore_version(self.note_id, row["title"] or "", row["body"] or "",
                                row["color"] or "default", row["image_path"] or "")
        QMessageBox.information(self, "Success", "Version restored.")
        self.accept()


# ============================================================
# COLOR PICKER WIDGET
# ============================================================
class ColorPickerWidget(QWidget):
    color_selected = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(8)
        row, col = 0, 0
        for name in NOTE_COLORS:
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(name.capitalize())
            bg = note_color(name)
            border_col = pal("border") if name == "default" else bg
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {bg}; border-radius: 16px; border: 1px solid {border_col}; }}
                QPushButton:hover {{ border: 2px solid {pal('text_lo')}; }}
            """)
            btn.clicked.connect(lambda _c=False, n=name: self._select(n))
            layout.addWidget(btn, row, col)
            col += 1
            if col > 3: col = 0; row += 1

    def _select(self, name):
        self.color_selected.emit(name)
        self.window().close()


# ============================================================
# EDIT DIALOG
# ============================================================
class NoteEditDialog(QDialog):
    def __init__(self, parent, db: NotesDB, note_id: int | None = None):
        super().__init__(parent)
        self.db = db
        self.note_id = note_id
        self._color = "default"
        self._pinned = False
        self._image_path = ""
        self._original_image_path = ""       # FIX #13
        self._result_action = "saved"        # FIX B

        self.setModal(True)
        self.setAcceptDrops(True)
        _center_dialog(self, parent, 600, 540)
        self.setMinimumSize(450, 440)

        self._update_bg()

        self.sc_esc = QShortcut(QKeySequence("Escape"), self, self._save)
        self.sc_save = QShortcut(QKeySequence("Ctrl+S"), self, self._save)

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)

        self.image_preview = QLabel()
        self.image_preview.setFixedHeight(160)
        self.image_preview.hide()
        self.image_preview.setStyleSheet("border-radius: 4px;")
        v.addWidget(self.image_preview)

        top_row = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Title")
        self.title_edit.setStyleSheet(f"font-size: 20px; font-weight: bold; border: none; background: transparent; color: {pal('text_hi')}; padding: 0;")
        top_row.addWidget(self.title_edit, 1)

        self.pin_btn = QPushButton("📌")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setFixedSize(36, 36)
        self.pin_btn.setToolTip("Pin note")
        self.pin_btn.setStyleSheet(f"""
            QPushButton {{ border: none; font-size: 16px; background: transparent; border-radius: 18px; }}
            QPushButton:hover {{ background: {pal('bg_hover')}; }}
            QPushButton:checked {{ background: {pal('accent_bg')}; }}
        """)
        top_row.addWidget(self.pin_btn)
        # FIX #1: pin state'i _pinned'e bağla
        self.pin_btn.toggled.connect(lambda checked: setattr(self, "_pinned", checked))

        self.close_btn = QPushButton("✖")
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setToolTip("Save and close")   # FIX 4
        self.close_btn.setStyleSheet(f"""
            QPushButton {{ border: none; font-size: 15px; background: transparent;
                border-radius: 18px; color: {pal('text_mid')}; }}
            QPushButton:hover {{ background: {pal('bg_hover')}; }}
        """)
        self.close_btn.clicked.connect(self._save)
        top_row.addWidget(self.close_btn)
        v.addLayout(top_row)

        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText("Take a note...")
        self.body_edit.setStyleSheet(f"font-size: {_body_font_size}pt; border: none; background: transparent; color: {pal('text_hi')}; padding: 0;")
        self.body_edit.cursorPositionChanged.connect(self._on_cursor_moved)
        v.addWidget(self.body_edit, 1)

        self.date_lbl = QLabel("")
        self.date_lbl.setStyleSheet(f"color: {pal('text_lo')}; font-size: 11px;")
        v.addWidget(self.date_lbl, alignment=Qt.AlignLeft)

        self.tip_bar = QLabel(" 💡 Use '#' for labels, Ctrl+V to paste images.")
        self.tip_bar.setStyleSheet(f"background-color: {pal('accent_bg')}; color: {pal('accent_text')}; border-radius: 4px; padding: 6px; font-size: 11px;")
        self.tip_bar.setAlignment(Qt.AlignCenter)
        v.addWidget(self.tip_bar)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        def make_tool_btn(text, checkable=False):
            b = QPushButton(text)
            b.setFixedSize(32, 32)
            b.setCheckable(checkable)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; border-radius: 16px;
                    font-size: 13px; color: {pal('text_hi')}; text-align: center; padding: 0; }}
                QPushButton:hover {{ background: {pal('bg_hover')}; }}
                QPushButton:checked {{ background: {pal('accent_bg')}; color: {pal('accent_text')}; }}
            """)
            return b

        self.btn_bold = make_tool_btn("B", True)
        self.btn_bold.setStyleSheet(self.btn_bold.styleSheet() + "font-weight: bold;")
        self.btn_bold.clicked.connect(self._toggle_bold)
        toolbar.addWidget(self.btn_bold)

        self.btn_italic = make_tool_btn("I", True)
        self.btn_italic.setStyleSheet(self.btn_italic.styleSheet() + "font-style: italic; font-family: serif;")
        self.btn_italic.clicked.connect(self._toggle_italic)
        toolbar.addWidget(self.btn_italic)

        self.btn_under = make_tool_btn("U", True)
        self.btn_under.setStyleSheet(self.btn_under.styleSheet() + "text-decoration: underline;")
        self.btn_under.clicked.connect(self._toggle_underline)
        toolbar.addWidget(self.btn_under)

        self.btn_strike = make_tool_btn("S", True)
        self.btn_strike.setStyleSheet(self.btn_strike.styleSheet() + "text-decoration: line-through;")
        self.btn_strike.clicked.connect(self._toggle_strike)
        toolbar.addWidget(self.btn_strike)

        toolbar.addSpacing(8)

        self.color_btn = make_tool_btn("🎨"); self.color_btn.setToolTip("Color")
        self.color_btn.clicked.connect(self._show_color_menu); toolbar.addWidget(self.color_btn)

        self.img_btn = make_tool_btn("🖼️"); self.img_btn.setToolTip("Add image")
        self.img_btn.clicked.connect(self._select_image); toolbar.addWidget(self.img_btn)

        self.chk_btn = make_tool_btn("☑"); self.chk_btn.setToolTip("Add checkbox")
        self.chk_btn.clicked.connect(self._insert_checkbox); toolbar.addWidget(self.chk_btn)

        self.more_btn = make_tool_btn("⋮"); self.more_btn.setToolTip("More")
        self.more_btn.clicked.connect(self._show_more_menu); toolbar.addWidget(self.more_btn)

        toolbar.addStretch(1)
        v.addLayout(toolbar)

        if note_id is not None:
            row = db.get(note_id)
            if row:
                self.title_edit.setText(row["title"])
                self.body_edit.setHtml(row["body"])
                self._color = row["color"]
                self._pinned = bool(row["pinned"])
                self._image_path = row["image_path"] or ""
                self._original_image_path = self._image_path  # FIX #13
                self.pin_btn.setChecked(self._pinned)
                self._update_bg()
                if self._image_path and os.path.exists(self._image_path):
                    self._update_image_preview()
                self.date_lbl.setText(f"Last edited: {_human_date(row['updated_at'])}")

        self.title_edit.setFocus()
        QTimer.singleShot(3500, self.tip_bar.hide)

    # FIX L: iptal edilirken kaydedilmemiş görseli temizle
    def reject(self):
        if self._image_path and self._image_path != self._original_image_path:
            if os.path.exists(self._image_path):
                try: os.remove(self._image_path)
                except Exception: pass
        super().reject()

    # FIX #9: dialog gösterildikten sonra preview'i yenile
    def showEvent(self, event):
        super().showEvent(event)
        if self._image_path and os.path.exists(self._image_path):
            QTimer.singleShot(0, self._update_image_preview)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                path = url.toLocalFile()
                if path and path.lower().endswith(IMG_EXTS):
                    self._set_image_from_file(path)
                    event.acceptProposedAction()
                    return
        elif mime.hasImage():
            img = QImage(mime.imageData())
            if not img.isNull():
                dest = os.path.join(ASSETS_DIR, f"{uuid.uuid4().hex}.png")
                img.save(dest)
                self._set_image_path(dest)
                event.acceptProposedAction()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            mime = QApplication.clipboard().mimeData()
            if mime.hasImage():
                img = QImage(mime.imageData())
                if not img.isNull():
                    dest = os.path.join(ASSETS_DIR, f"{uuid.uuid4().hex}.png")
                    img.save(dest)
                    self._set_image_path(dest)
                    event.accept(); return
        super().keyPressEvent(event)

    def _set_image_path(self, new_path: str):
        """FIX I: yeni görsel atanırken önceki unsaved görseli temizle."""
        if self._image_path and self._image_path != self._original_image_path:
            if os.path.exists(self._image_path):
                try: os.remove(self._image_path)
                except Exception: pass
        self._image_path = new_path
        self._update_image_preview()

    def _set_image_from_file(self, src_path: str):
        ext = os.path.splitext(src_path)[1].lower() or ".png"
        dest = os.path.join(ASSETS_DIR, f"{uuid.uuid4().hex}{ext}")
        try:
            shutil.copy2(src_path, dest)
            self._set_image_path(dest)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add image: {e}")

    def _update_bg(self):
        bg = note_color(self._color)
        self.setStyleSheet(f"QDialog {{ background-color: {bg}; border-radius: 8px; }}")
        if hasattr(self, 'title_edit'):
            self.title_edit.setStyleSheet(f"font-size: 20px; font-weight: bold; border: none; background: transparent; color: {pal('text_hi')}; padding: 0;")
            self.body_edit.setStyleSheet(f"font-size: {_body_font_size}pt; border: none; background: transparent; color: {pal('text_hi')}; padding: 0;")

    def _on_cursor_moved(self):
        fmt = self.body_edit.currentCharFormat()
        self.btn_bold.setChecked(fmt.fontWeight() == QFont.Bold)
        self.btn_italic.setChecked(fmt.fontItalic())
        self.btn_under.setChecked(fmt.fontUnderline())
        self.btn_strike.setChecked(fmt.fontStrikeOut())

    def _merge_format(self, fmt):
        cursor = self.body_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.body_edit.mergeCurrentCharFormat(fmt)

    def _toggle_bold(self):
        f = QTextCharFormat(); f.setFontWeight(QFont.Bold if self.btn_bold.isChecked() else QFont.Normal); self._merge_format(f)
    def _toggle_italic(self):
        f = QTextCharFormat(); f.setFontItalic(self.btn_italic.isChecked()); self._merge_format(f)
    def _toggle_underline(self):
        f = QTextCharFormat(); f.setFontUnderline(self.btn_under.isChecked()); self._merge_format(f)
    def _toggle_strike(self):
        f = QTextCharFormat(); f.setFontStrikeOut(self.btn_strike.isChecked()); self._merge_format(f)

    def _show_color_menu(self):
        menu = QMenu(self)
        picker = ColorPickerWidget()
        picker.color_selected.connect(self._select_color)
        action = QWidgetAction(menu)
        action.setDefaultWidget(picker)
        menu.addAction(action)
        menu.exec(self.color_btn.mapToGlobal(self.color_btn.rect().topLeft()))

    def _select_color(self, name: str):
        self._color = name
        self._update_bg()

    def _show_more_menu(self):
        menu = QMenu(self)
        menu.addAction("Make a copy", self._duplicate_note)
        if self.note_id:
            menu.addAction("Version history", self._show_history)
        menu.addSeparator()
        menu.addAction("📄 Download as Markdown", self._export_markdown)
        menu.addSeparator()
        # FIX #2: kalıcı silme değil, çöpe taşı
        menu.addAction("🗑️ Move to Trash", self._delete_note)
        menu.exec(self.more_btn.mapToGlobal(self.more_btn.rect().topLeft()))

    def _export_markdown(self):
        if self.note_id is None:
            QMessageBox.information(self, "Info", "Save the note first."); return
        safe = re.sub(r"[^\w\s\-]", "", self.title_edit.text() or "note")[:60].strip() or "note"
        path, _ = QFileDialog.getSaveFileName(self, "Save as Markdown",
                                              os.path.join(os.path.expanduser("~"), f"{safe}.md"),
                                              "Markdown (*.md);;Text (*.txt)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.db.note_to_markdown(self.note_id))
            QMessageBox.information(self, "Success", f"Saved:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {e}")

    def _show_history(self):
        if self.note_id:
            dlg = HistoryDialog(self, self.db, self.note_id)
            if dlg.exec(): self.accept()

    def _duplicate_note(self):
        # FIX #4: görseli kopyala, paylaşma
        title = self.title_edit.text().strip()
        body = self.body_edit.toHtml()
        doc = QTextDocument(); doc.setHtml(body)
        if not title and not doc.toPlainText().strip() and not self._image_path:
            QMessageBox.information(self, "Info", "Cannot copy empty note.")
            return
        dup_image = ""
        if self._image_path and os.path.exists(self._image_path):
            ext = os.path.splitext(self._image_path)[1].lower() or ".png"
            dup_image = os.path.join(ASSETS_DIR, f"{uuid.uuid4().hex}{ext}")
            try:
                shutil.copy2(self._image_path, dup_image)
            except Exception:
                dup_image = ""
        self.db.add(title, body, self._color, self._pinned, dup_image)
        # FIX F: orijinal notta kaydedilmemiş yeni görseli temizle
        if self._image_path and self._image_path != self._original_image_path:
            if os.path.exists(self._image_path):
                try: os.remove(self._image_path)
                except Exception: pass
        self._result_action = "duplicated"
        self.accept()

    def _delete_note(self):
        # FIX #2: onaylı, çöpe taşıyan silme
        if not self.note_id:
            self.reject()
            return
        reply = QMessageBox.question(
            self, "Move to Trash",
            "Move this note to Trash?\n\nYou can restore it from Trash later.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.set_status(self.note_id, "trash")
            # FIX C: henüz kaydedilmemiş yeni görseli temizle
            if self._image_path and self._image_path != self._original_image_path:
                if os.path.exists(self._image_path):
                    try: os.remove(self._image_path)
                    except Exception: pass
            self._result_action = "trashed"
            self.accept()

    def _select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.webp)")
        if path: self._set_image_from_file(path)

    def _update_image_preview(self):
        # FIX #9: genişlik 0 ise makul fallback
        if not (self._image_path and os.path.exists(self._image_path)):
            return
        pixmap = QPixmap(self._image_path)
        if pixmap.isNull():
            return
        w = self.image_preview.width()
        h = self.image_preview.height()
        if w <= 0 or h <= 0:
            w, h = 400, 160
        self.image_preview.setPixmap(
            pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.image_preview.show()

    def _insert_checkbox(self):
        cursor = self.body_edit.textCursor()
        cursor.insertText("[ ] ")
        self.body_edit.setTextCursor(cursor)

    def _save(self):
        title = self.title_edit.text().strip()
        body_html = self.body_edit.toHtml()
        doc = QTextDocument(); doc.setHtml(body_html)
        body_text = doc.toPlainText().strip()
        if not title and not body_text and not self._image_path:
            self.reject(); return

        # FIX J + O: değişiklik yoksa history de update de atla
        skip_unchanged = False
        if self.note_id is not None:
            cur = self.db.get(self.note_id)
            if cur:
                cur_plain = (cur["plain_body"] or "").strip()
                if (title == (cur["title"] or "")
                    and body_text == cur_plain
                    and self._color == (cur["color"] or "default")
                    and int(self._pinned) == int(cur["pinned"] or 0)
                    and self._image_path == (cur["image_path"] or "")):
                    skip_unchanged = True

        if skip_unchanged:
            self._result_action = "saved"
            self.accept()
            return

        if self.note_id is None:
            self.db.add(title, body_html, self._color, self._pinned, self._image_path)
        else:
            self.db.update(self.note_id, title, body_html, self._color, self._pinned, self._image_path)
        # FIX #13: değiştirilen eski görseli temizle
        if self._original_image_path and self._original_image_path != self._image_path:
            if os.path.exists(self._original_image_path):
                try: os.remove(self._original_image_path)
                except Exception: pass
        self._result_action = "saved"
        self.accept()


# ============================================================
# SETTINGS DIALOG
# ============================================================
class SettingsDialog(QDialog):
    def __init__(self, parent, current_mode: str):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        _center_dialog(self, parent, 380, 420)
        self.mode = current_mode
        self.font_size = _body_font_size

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)

        title = QLabel("⚙️ Settings")
        title.setFont(_font(18, bold=True))
        v.addWidget(title)

        v.addWidget(QLabel("Theme:"))
        self.theme_group = QButtonGroup(self)
        theme_row = QHBoxLayout()
        for name, val in [("System", "system"), ("Dark", "dark"), ("Light", "light")]:
            btn = QPushButton(name)
            btn.setCheckable(True); btn.setFixedHeight(36)
            btn.setStyleSheet(
                f"QPushButton {{ background: {pal('bg_hover')}; border-radius: 18px; padding: 4px 16px; text-align: center; }}"
                f"QPushButton:checked {{ background: {pal('accent_bg')}; color: {pal('accent_text')}; font-weight: bold; }}"
            )
            self.theme_group.addButton(btn); theme_row.addWidget(btn)
            btn.clicked.connect(lambda _c=False, m=val: self._set_theme(m))
            if self.mode == val: btn.setChecked(True)
        v.addLayout(theme_row)

        v.addWidget(QLabel("Font Size:"))
        self.size_group = QButtonGroup(self)
        size_row = QHBoxLayout()
        for label, sz in [("Small", 11), ("Normal", 13), ("Large", 15)]:
            btn = QPushButton(label)
            btn.setCheckable(True); btn.setFixedHeight(36)
            btn.setStyleSheet(
                f"QPushButton {{ background: {pal('bg_hover')}; border-radius: 18px; padding: 4px 16px; text-align: center; }}"
                f"QPushButton:checked {{ background: {pal('accent_bg')}; color: {pal('accent_text')}; font-weight: bold; }}"
            )
            self.size_group.addButton(btn); size_row.addWidget(btn)
            btn.clicked.connect(lambda _c=False, s=sz: self._set_size(s))
            if self.font_size == sz: btn.setChecked(True)
        v.addLayout(size_row)

        v.addStretch(1)

        bottom_row = QHBoxLayout()
        ver = QLabel(f"v{__version__}")
        ver.setFont(_font(11)); ver.setStyleSheet(f"color: {pal('text_lo')};")
        bottom_row.addWidget(ver)
        bottom_row.addStretch(1)
        close_btn = QPushButton("Save")
        close_btn.setFixedHeight(36)
        close_btn.setStyleSheet(f"background: {pal('accent')}; color: #000; border-radius: 18px; padding: 0 22px; text-align: center; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        bottom_row.addWidget(close_btn)
        v.addLayout(bottom_row)

    def _set_theme(self, mode: str): self.mode = mode
    def _set_size(self, size: int): self.font_size = size


# ============================================================
# TAG MANAGER DIALOG
# ============================================================
class TagManagerDialog(QDialog):
    tags_changed = Signal()

    def __init__(self, parent, db: NotesDB):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Edit labels")
        self.setModal(True)
        _center_dialog(self, parent, 360, 450)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20); v.setSpacing(12)

        title = QLabel("Edit labels")
        title.setFont(_font(16, bold=True))
        v.addWidget(title)

        # Create new label
        new_tag_row = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("Create new label")
        self.new_tag_edit.setStyleSheet(f"background: transparent; border: none; font-size: 14px;")
        self.new_tag_edit.returnPressed.connect(self._add_new_tag)
        new_tag_row.addWidget(self.new_tag_edit)

        add_btn = QPushButton("✓")
        add_btn.setFixedSize(30, 30)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; font-size: 16px; font-weight: bold; color: {pal('text_mid')}; }} QPushButton:hover {{ background: {pal('bg_hover')}; border-radius: 15px; }}")
        add_btn.clicked.connect(self._add_new_tag)
        new_tag_row.addWidget(add_btn)
        v.addLayout(new_tag_row)

        # Divider
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background-color: {pal('border')};")
        v.addWidget(line)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.content = QWidget()
        self.cl = QVBoxLayout(self.content)
        self.cl.setContentsMargins(0, 0, 0, 0); self.cl.setSpacing(6)
        self._load_tags()

        scroll.setWidget(self.content)
        v.addWidget(scroll, 1)

        close_btn = QPushButton("Done")
        close_btn.setFixedHeight(38)
        close_btn.setStyleSheet(f"background: transparent; color: {pal('accent_text')}; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        v.addWidget(close_btn)

    def _load_tags(self):
        while self.cl.count():
            item = self.cl.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

        tags = self.db.get_all_tags()
        cfg = _load_config()
        custom_tags = cfg.get("custom_tags", [])
        all_tags = sorted(list(set(tags + custom_tags)))

        if not all_tags:
            self.cl.addWidget(QLabel("No labels yet."))
        else:
            for tag in all_tags:
                row = QFrame()
                row.setStyleSheet(f"background: {pal('bg_hover')}; border-radius: 6px;")
                rl = QHBoxLayout(row); rl.setContentsMargins(12, 8, 8, 8)
                icon = QLabel("🏷️"); icon.setFont(_font(12))
                rl.addWidget(icon)
                name_lbl = QLabel(tag); name_lbl.setFont(_font(13))
                rl.addWidget(name_lbl, 1)

                del_btn = QPushButton("🗑️")
                del_btn.setFixedSize(28, 28)
                del_btn.setStyleSheet(f"QPushButton {{ border: none; border-radius: 14px; font-size: 12px; }} QPushButton:hover {{ background: {pal('bg_card')}; }}")
                del_btn.clicked.connect(lambda _c=False, t=tag: self._delete_tag(t))
                rl.addWidget(del_btn)

                self.cl.addWidget(row)
        self.cl.addStretch(1)

    def _add_new_tag(self):
        new_tag = self.new_tag_edit.text().strip().replace(" ", "_")
        if not new_tag: return

        cfg = _load_config()
        custom_tags = cfg.get("custom_tags", [])
        if new_tag not in custom_tags:
            custom_tags.append(new_tag)
            cfg["custom_tags"] = custom_tags
            _save_config(cfg)

        self.new_tag_edit.clear()
        self._load_tags()
        self.tags_changed.emit()

    def _delete_tag(self, tag: str):
        reply = QMessageBox.question(self, "Delete Label",
                                     f"Remove label '{tag}' from all notes?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_tag_from_all(tag)
            cfg = _load_config()
            custom_tags = cfg.get("custom_tags", [])
            if tag in custom_tags:
                custom_tags.remove(tag)
                cfg["custom_tags"] = custom_tags
                _save_config(cfg)
            self._load_tags()
            self.tags_changed.emit()


# ============================================================
# MAIN WINDOW
# ============================================================
class ProjectKizenNotes(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"⚡Kizen-Notes v{__version__}")
        w, h = _fit_window_size(1280, 780)
        self.resize(w, h)
        self.setMinimumSize(*_fit_window_size(900, 560))

        self.db = NotesDB()
        self._filter = "all"
        self._search = ""
        self._note_widgets: list[NoteCard] = []
        self._sidebar_expanded = True
        self._view_mode = "grid"          # FIX #5
        self._last_cols = 0               # FIX 2
        self._last_rows = 0               # FIX 2
        self._counts = {"all": 0, "pinned": 0, "archive": 0, "trash": 0}

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._perform_search)

        self._build_ui()
        self._bind_shortcuts()

        self._toast = Toast(self)
        self._reload_all()                # FIX P
        self._toast.show_message(f"✓ ⚡Kizen-Notes v{__version__}")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # Header (full width)
        root.addWidget(self._build_header())

        # Body: sidebar + main
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        self.main_area = self._build_main_area()
        body.addWidget(self.main_area, 1)
        root.addLayout(body, 1)

    def _reload_all(self):
        """FIX P: önce _refresh_tags (filtre değişebilir), sonra reload_notes."""
        self._refresh_tags()
        self.reload_notes()

    # ------------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------------
    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(64)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 8, 16, 8)
        hl.setSpacing(8)

        # Hamburger
        self.header_hamburger = QPushButton("☰")
        self.header_hamburger.setObjectName("HeaderIcon")
        self.header_hamburger.setFixedSize(40, 40)
        self.header_hamburger.setCursor(Qt.PointingHandCursor)
        self.header_hamburger.clicked.connect(self._toggle_sidebar)
        hl.addWidget(self.header_hamburger)

        # Logo
        logo_wrap = QHBoxLayout()
        logo_wrap.setContentsMargins(0, 0, 0, 0); logo_wrap.setSpacing(6)
        bolt = QLabel("⚡")
        bolt.setFont(_font(20))
        logo_wrap.addWidget(bolt)
        keep_lbl = QLabel("Kizen-Notes")
        keep_lbl.setObjectName("AppLogo")
        logo_wrap.addWidget(keep_lbl)
        hl.addLayout(logo_wrap)
        hl.addSpacing(20)

        # Centered search bar
        search_wrap = QWidget()
        sw = QHBoxLayout(search_wrap)
        sw.setContentsMargins(0, 0, 0, 0); sw.setSpacing(0)
        sw.addStretch(1)

        self.search_frame = QFrame()
        self.search_frame.setObjectName("SearchBar")
        self.search_frame.setFixedHeight(46)
        self.search_frame.setMaximumWidth(720)
        self.search_frame.setMinimumWidth(280)
        sf = QHBoxLayout(self.search_frame)
        sf.setContentsMargins(14, 0, 8, 0); sf.setSpacing(8)

        search_icon = QLabel("🔍"); search_icon.setFont(_font(13))
        sf.addWidget(search_icon)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("TransparentInput")
        self.search_edit.setPlaceholderText("Search")
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.search_edit.installEventFilter(self)
        sf.addWidget(self.search_edit, 1)

        self.search_clear = QPushButton("✕")
        self.search_clear.setFixedSize(26, 26)
        self.search_clear.setCursor(Qt.PointingHandCursor)
        self.search_clear.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {pal('text_mid')};
                border-radius: 13px; font-size: 12px; padding: 0; text-align: center; }}
            QPushButton:hover {{ background: {pal('bg_hover')}; }}
        """)
        self.search_clear.clicked.connect(self._clear_search)
        self.search_clear.hide()
        sf.addWidget(self.search_clear)

        sw.addWidget(self.search_frame, 4)
        sw.addStretch(1)
        hl.addWidget(search_wrap, 1)

        # Right action icons
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setObjectName("HeaderIcon")
        self.refresh_btn.setFixedSize(40, 40)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setToolTip("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_all)
        hl.addWidget(self.refresh_btn)

        # FIX #5: state-driven view toggle
        self.view_btn = QPushButton("▦")
        self.view_btn.setObjectName("HeaderIcon")
        self.view_btn.setFixedSize(40, 40)
        self.view_btn.setCursor(Qt.PointingHandCursor)
        self.view_btn.setToolTip("Grid view")
        self.view_btn.clicked.connect(self._toggle_view_mode)
        hl.addWidget(self.view_btn)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("HeaderIcon")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._show_settings_menu)
        hl.addWidget(self.settings_btn)

        return header

    # ------------------------------------------------------------------
    # SIDEBAR
    # ------------------------------------------------------------------
    def _build_sidebar(self) -> QFrame:
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(256)

        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(0, 8, 0, 12); sl.setSpacing(0)

        # Filters
        self._filter_buttons = {}
        self._add_sidebar_btn(sl, "all", "⚡", "Notes")
        # FIX UX 1: "Reminders" → "Pinned" (içerikle uyumlu)
        self._add_sidebar_btn(sl, "pinned", "📌", "Pinned")
        self._add_sidebar_btn(sl, "archive", "📥", "Archive")
        self._add_sidebar_btn(sl, "trash", "🗑️", "Trash")

        # Tags section
        sl.addSpacing(8)
        self.tags_header = QLabel("LABELS")
        self.tags_header.setObjectName("SectionHeader")
        sl.addWidget(self.tags_header)

        self.tags_layout = QVBoxLayout()
        self.tags_layout.setContentsMargins(0, 0, 0, 0); self.tags_layout.setSpacing(0)
        sl.addLayout(self.tags_layout)

        # "Edit labels"
        self.edit_labels_btn = QPushButton("✏️   Edit labels")
        self.edit_labels_btn.setCursor(Qt.PointingHandCursor)
        self.edit_labels_btn.setFixedHeight(48)
        self.edit_labels_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; text-align: left;
                padding: 0 24px 0 20px; color: {pal('text_mid')};
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {pal('bg_hover')}; }}
        """)
        self.edit_labels_btn.clicked.connect(self._open_tag_manager)
        sl.addWidget(self.edit_labels_btn)

        sl.addStretch(1)

        # Footer: open source licenses
        self._footer_btn = QPushButton("Open-source licenses")
        self._footer_btn.setCursor(Qt.PointingHandCursor)
        self._footer_btn.setFixedHeight(36)
        self._footer_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; text-align: left;
                padding: 0 24px; color: {pal('text_mid')}; font-size: 11px;
            }}
            QPushButton:hover {{ color: {pal('text_hi')}; text-decoration: underline; }}
        """)
        self._footer_btn.clicked.connect(self._show_license)
        sl.addWidget(self._footer_btn)

        return self.sidebar

    def _add_sidebar_btn(self, layout, filter_id: str, icon: str, label: str):
        btn = QPushButton(f"{icon}   {label}")
        btn.setFixedHeight(48)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(True)
        btn.setProperty("full_text", f"{icon}   {label}")
        btn.setProperty("icon_text", icon)
        btn.setProperty("collapsed", False)   # FIX 1: property-driven
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; text-align: left;
                padding: 0 24px 0 20px; border-radius: 0 25px 25px 0;
                color: {pal('text_hi')}; font-size: 13px;
            }}
            QPushButton[collapsed="true"] {{
                padding: 0 8px 0 4px;
            }}
            QPushButton:hover {{ background-color: {pal('bg_hover')}; }}
            QPushButton:checked {{
                background-color: {pal('accent_bg')};
                color: {pal('accent_text')};
                font-weight: 500;
            }}
        """)
        btn.clicked.connect(lambda _c=False, f=filter_id: self._set_filter(f))
        self._filter_buttons[filter_id] = btn
        layout.addWidget(btn)
        if filter_id == "all": btn.setChecked(True)
        return btn

    def _refresh_tags(self):
        for key in list(self._filter_buttons.keys()):
            if key.startswith("tag:"):
                btn = self._filter_buttons.pop(key)
                try: btn.setParent(None); btn.deleteLater()
                except Exception: pass

        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

        db_tags = self.db.get_all_tags()
        cfg = _load_config()
        custom_tags = cfg.get("custom_tags", [])
        all_tags = sorted(list(set(db_tags + custom_tags)))

        for tag in all_tags:
            btn = QPushButton(f"🏷️   {tag}")
            btn.setFixedHeight(44)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none; text-align: left;
                    padding: 0 24px 0 20px; border-radius: 0 22px 22px 0;
                    color: {pal('text_hi')}; font-size: 13px;
                }}
                QPushButton:hover {{ background-color: {pal('bg_hover')}; }}
                QPushButton:checked {{
                    background-color: {pal('accent_bg')};
                    color: {pal('accent_text')};
                    font-weight: 500;
                }}
            """)
            fid = f"tag:{tag}"
            btn.clicked.connect(lambda _c=False, f=fid: self._set_filter(f))
            if self._filter == fid: btn.setChecked(True)
            btn.setVisible(self._sidebar_expanded)
            self._filter_buttons[fid] = btn
            self.tags_layout.addWidget(btn)

        # FIX K: aktif tag silindiyse filtreyi "all"a döndür
        if self._filter.startswith("tag:"):
            active_tag = self._filter.split(":", 1)[1]
            if active_tag not in all_tags:
                self._filter = "all"
                for fid, btn in self._filter_buttons.items():
                    btn.setChecked(fid == "all")

    def _refresh_counts(self):
        by_status = self.db.count_by_status()
        self._counts = {
            "all": by_status.get("active", 0),
            "pinned": self.db.count_pinned_active(),
            "archive": by_status.get("archived", 0),
            "trash": by_status.get("trash", 0),
        }

    def _restyle_sidebar(self):
        """FIX G: tema değişince sidebar + main area widget QSS'lerini yenile."""
        for fid, btn in self._filter_buttons.items():
            if fid.startswith("tag:"):
                continue
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none; text-align: left;
                    padding: 0 24px 0 20px; border-radius: 0 25px 25px 0;
                    color: {pal('text_hi')}; font-size: 13px;
                }}
                QPushButton[collapsed="true"] {{ padding: 0 8px 0 4px; }}
                QPushButton:hover {{ background-color: {pal('bg_hover')}; }}
                QPushButton:checked {{
                    background-color: {pal('accent_bg')};
                    color: {pal('accent_text')};
                    font-weight: 500;
                }}
            """)
        if hasattr(self, "edit_labels_btn"):
            self.edit_labels_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none; text-align: left;
                    padding: 0 24px 0 20px; color: {pal('text_mid')};
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: {pal('bg_hover')}; }}
            """)
        if hasattr(self, "_footer_btn"):
            self._footer_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none; text-align: left;
                    padding: 0 24px; color: {pal('text_mid')}; font-size: 11px;
                }}
                QPushButton:hover {{ color: {pal('text_hi')}; text-decoration: underline; }}
            """)
        if hasattr(self, "search_clear"):
            self.search_clear.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; color: {pal('text_mid')};
                    border-radius: 13px; font-size: 12px; padding: 0; text-align: center; }}
                QPushButton:hover {{ background: {pal('bg_hover')}; }}
            """)
        if hasattr(self, "_take_note_lbl"):
            self._take_note_lbl.setStyleSheet(f"color: {pal('text_mid')};")
        if hasattr(self, "trash_warning"):
            self.trash_warning.setStyleSheet(f"color: {pal('text_mid')}; padding: 8px;")

    def _toggle_sidebar(self):
        self._sidebar_expanded = not self._sidebar_expanded
        if self._sidebar_expanded:
            self.sidebar.setFixedWidth(256)
            self.tags_header.show()
            self.edit_labels_btn.show()
            self._footer_btn.show()      # FIX H
        else:
            self.sidebar.setFixedWidth(72)
            self.tags_header.hide()
            self.edit_labels_btn.hide()
            self._footer_btn.hide()      # FIX H

        for fid, btn in self._filter_buttons.items():
            if fid.startswith("tag:"):
                btn.setVisible(self._sidebar_expanded)
            else:
                btn.setProperty("collapsed", not self._sidebar_expanded)
                btn.setText(btn.property("full_text") if self._sidebar_expanded
                            else btn.property("icon_text"))
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    # ------------------------------------------------------------------
    # MAIN CONTENT AREA
    # ------------------------------------------------------------------
    def _build_main_area(self) -> QWidget:
        area = QWidget()
        v = QVBoxLayout(area)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        take_wrap = QWidget()
        tw = QHBoxLayout(take_wrap)
        tw.setContentsMargins(24, 16, 24, 16)
        tw.addStretch(1)

        self.inline_note_frame = ClickableFrame()
        self.inline_note_frame.setObjectName("InlineNote")
        self.inline_note_frame.setFixedHeight(46)
        self.inline_note_frame.setFixedWidth(600)
        self.inline_note_frame.setCursor(Qt.PointingHandCursor)
        self.inline_note_frame.clicked.connect(self._new_note)
        _add_shadow(self.inline_note_frame, blur=12, y=2, alpha=30)

        il = QHBoxLayout(self.inline_note_frame)
        il.setContentsMargins(16, 0, 16, 0); il.setSpacing(10)

        # FIX G: self._take_note_lbl olarak sakla
        self._take_note_lbl = QLabel("Take a note...")
        self._take_note_lbl.setFont(_font(14, bold=False))
        self._take_note_lbl.setStyleSheet(f"color: {pal('text_mid')};")
        il.addWidget(self._take_note_lbl)
        il.addStretch(1)

        tw.addWidget(self.inline_note_frame, 4)
        tw.addStretch(1)
        v.addWidget(take_wrap)

        # Trash warning
        self.trash_warning = QLabel("Notes in Trash are deleted after 7 days.")
        self.trash_warning.setFont(_font(12, italic=True))
        self.trash_warning.setAlignment(Qt.AlignCenter)
        self.trash_warning.setStyleSheet(f"color: {pal('text_mid')}; padding: 8px;")
        self.trash_warning.hide()
        v.addWidget(self.trash_warning)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(16, 8, 16, 100)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.scroll.setWidget(self.grid_container)
        v.addWidget(self.scroll, 1)

        self.grid_container.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid_container.customContextMenuRequested.connect(self._grid_context_menu)

        self.fab = QPushButton("＋", area)
        self.fab.setObjectName("Fab")
        self.fab.setFixedSize(56, 56)
        self.fab.setCursor(Qt.PointingHandCursor)
        self.fab.clicked.connect(self._new_note)
        self.fab.setToolTip("New note (Ctrl+N)")
        _add_shadow(self.fab, blur=28, y=6, alpha=90)
        return area

    def _show_settings_menu(self):
        menu = QMenu(self)
        menu.addAction("Settings", self._open_settings)
        if _light_mode:
            menu.addAction("Turn on dark theme", lambda: self._quick_theme("dark"))
        else:
            menu.addAction("Turn on light theme", lambda: self._quick_theme("light"))
        menu.addSeparator()
        menu.addAction("Send feedback", lambda: self._toast.show_message("Thank you!"))
        menu.addAction("Help", self._show_help)
        menu.addAction("App downloads", lambda: self._toast.show_message("App is up to date"))
        menu.addAction("Keyboard shortcuts", self._show_shortcuts)
        menu.exec(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomRight()))

    def _quick_theme(self, mode: str):
        set_mode(mode)
        _apply_theme(QApplication.instance())
        self._restyle_sidebar()
        self._reload_all()    # FIX P

    def _show_help(self):
        QMessageBox.information(self, "Help",
            "⚡Kizen-Notes\n\n"
            "• Ctrl+N: New note\n"
            "• Ctrl+F: Search\n"
            "• Ctrl+Shift+E: Backup\n"
            "• Right-click: Card menu")

    def _show_shortcuts(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Keyboard shortcuts")
        _center_dialog(dlg, self, 480, 420)
        lv = QVBoxLayout(dlg)
        lv.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Keyboard shortcuts"); title.setFont(_font(16, bold=True))
        lv.addWidget(title)
        rows = [
            ("New note", "Ctrl + N"),
            ("Search", "Ctrl + F"),
            ("Backup", "Ctrl + Shift + E"),
            ("Save (editor)", "Ctrl + S"),
            ("Close (editor)", "Esc"),
        ]
        for desc, key in rows:
            row = QHBoxLayout()
            d = QLabel(desc); d.setFont(_font(13))
            k = QLabel(key); k.setFont(_font(12, bold=True))
            row.addWidget(d); row.addStretch(1); row.addWidget(k)
            lv.addLayout(row)
        lv.addStretch(1)
        close = QPushButton("Close"); close.setFixedHeight(36)
        close.clicked.connect(dlg.accept)
        lv.addWidget(close)
        dlg.exec()

    def _show_license(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Open-source licenses")
        dlg.setModal(True)
        _center_dialog(dlg, self, 550, 480)
        dlg.setStyleSheet(f"QDialog {{ background-color: {pal('bg_card')}; border-radius: 10px; }}")

        lv = QVBoxLayout(dlg)
        lv.setContentsMargins(24, 24, 24, 24)
        lv.setSpacing(12)

        title = QLabel("MIT License")
        title.setFont(_font(18, bold=True))
        title.setStyleSheet(f"color: {pal('text_hi')};")
        lv.addWidget(title)

        hint = QLabel("This project is open-source under the MIT license. You can freely use, modify, and share it.")
        hint.setStyleSheet(f"color: {pal('text_mid')}; font-size: 12px;")
        hint.setWordWrap(True)
        lv.addWidget(hint)

        text = QTextEdit()
        text.setPlainText(LICENSE_TEXT)
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 10))
        text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {pal('bg_input')};
                color: {pal('text_hi')};
                border-radius: 8px;
                padding: 12px;
                border: 1px solid {pal('border')};
            }}
        """)
        lv.addWidget(text)

        btn_row = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setFixedHeight(36)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {pal('bg_hover')}; color: {pal('text_hi')};
                border-radius: 18px; padding: 0 16px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {pal('border')}; }}
        """)
        copy_btn.clicked.connect(lambda: self._copy_license_text(copy_btn))
        btn_row.addWidget(copy_btn)

        btn_row.addStretch(1)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {pal('accent')}; color: #000;
                border-radius: 18px; padding: 0 24px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {pal('accent_dark')}; }}
        """)
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)

        lv.addLayout(btn_row)
        dlg.exec()

    def _copy_license_text(self, btn):
        QApplication.clipboard().setText(LICENSE_TEXT)
        original = "📋 Copy"
        try:
            btn.setText("✓ Copied!")
        except RuntimeError:
            return
        def _reset():
            try:
                btn.setText(original)
            except RuntimeError:
                pass
        QTimer.singleShot(1500, _reset)

    def _refresh_all(self):
        self._reload_all()    # FIX P
        self._toast.show_message("✓ Refreshed")

    def _toggle_view_mode(self):
        if self._view_mode == "grid":
            self._view_mode = "list"
            self.view_btn.setText("☰")
            self.view_btn.setToolTip("List view")
        else:
            self._view_mode = "grid"
            self.view_btn.setText("▦")
            self.view_btn.setToolTip("Grid view")
        self._reflow_grid()

    def eventFilter(self, obj, event):
        if obj is self.search_edit:
            if event.type() == event.Type.FocusIn:
                self.search_frame.setProperty("focused", "true")
                self.search_frame.style().unpolish(self.search_frame)
                self.search_frame.style().polish(self.search_frame)
            elif event.type() == event.Type.FocusOut:
                self.search_frame.setProperty("focused", "false")
                self.search_frame.style().unpolish(self.search_frame)
                self.search_frame.style().polish(self.search_frame)
        return super().eventFilter(obj, event)

    def _clear_search(self):
        self.search_edit.clear()
        self.search_edit.setFocus()

    def _grid_context_menu(self, pos):
        menu = QMenu(self)
        if self._filter != "trash":
            menu.addAction("＋ New note", self._new_note)
            menu.addSeparator()
        menu.addAction("🗂️ Backup all notes as ZIP", self._backup_zip)
        menu.addAction("📄 Export all notes to Markdown folder", self._export_all_md)
        menu.exec(self.grid_container.mapToGlobal(pos))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "fab"):
            try:
                fab_x = self.main_area.width() - self.fab.width() - 32
                fab_y = self.main_area.height() - self.fab.height() - 32
                self.fab.move(fab_x, fab_y)
                self.fab.raise_()
            except Exception:
                pass
        QTimer.singleShot(0, self._reflow_grid)

    def _set_filter(self, filter_id: str):
        self._filter = filter_id
        for fid, btn in self._filter_buttons.items():
            btn.setChecked(fid == filter_id)

        is_trash = (filter_id == "trash")
        self.inline_note_frame.setVisible(not is_trash)
        self.fab.setVisible(not is_trash)
        self.trash_warning.setVisible(is_trash)

        self.reload_notes()

    def _on_search_changed(self, text: str):
        self._search = text
        self.search_clear.setVisible(bool(text))
        self.search_timer.start()

    def _perform_search(self):
        self.reload_notes()

    def _make_empty_state(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setAlignment(Qt.AlignCenter)
        vl.setSpacing(16)
        vl.setContentsMargins(0, 60, 0, 60)

        if self._search:
            icon_text = "🔍"
            msg = "No matching notes"
        elif self._filter == "trash":
            icon_text = "🗑️"
            msg = "No notes in Trash"
        elif self._filter == "archive":
            icon_text = "📥"
            msg = "Your archived notes appear here"
        elif self._filter == "pinned":
            icon_text = "📌"
            msg = "Pinned notes appear here"
        elif self._filter.startswith("tag:"):
            icon_text = "🏷️"
            msg = "No notes with this label"
        else:
            icon_text = "📝"
            msg = "No notes found"

        icon = QLabel(icon_text)
        icon.setFont(_font(64))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"color: {pal('text_lo')};")
        vl.addWidget(icon)

        lbl = QLabel(msg)
        lbl.setFont(_font(15))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {pal('text_mid')};")
        vl.addWidget(lbl)
        return w

    def reload_notes(self):
        self.grid_container.setUpdatesEnabled(False)
        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self._note_widgets.clear()

            rows = self.db.list_all(self._filter, self._search)
            for row in rows:
                card = NoteCard(row, self.grid_container, search=self._search)
                card.clicked.connect(self._edit_note)
                card.menu_requested.connect(self._show_card_menu)
                card.copy_requested.connect(self._copy_note_text)
                self._note_widgets.append(card)

            self._reflow_grid()
        finally:
            self.grid_container.setUpdatesEnabled(True)
        self._refresh_counts()

    def _copy_note_text(self, note_id: int):
        row = self.db.get(note_id)
        if not row: return
        text = row["title"].strip()
        body = row["plain_body"] or ""
        if body:
            text = (text + "\n\n" + body) if text else body
        QApplication.clipboard().setText(text)
        self._toast.show_message("📋 Text copied to clipboard")

    def _reflow_grid(self):
        if not hasattr(self, "grid_layout"): return

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w and w not in self._note_widgets:
                w.deleteLater()

        if not self._note_widgets:
            for c in range(self._last_cols):
                self.grid_layout.setColumnStretch(c, 0)
            for r in range(self._last_rows):
                self.grid_layout.setRowStretch(r, 0)
            self._last_cols = self._last_rows = 0
            self.grid_layout.addWidget(self._make_empty_state(), 0, 0, 1, 5)
            return

        is_list = (self._view_mode == "list")
        if is_list:
            cols = 1
            for card in self._note_widgets:
                card.setMaximumWidth(16777215)
            available = self.scroll.width() - 40
            for card in self._note_widgets:
                card.setMaximumWidth(min(800, available))
        else:
            available = self.scroll.width() - 40
            cols = max(1, available // 250)
            for card in self._note_widgets:
                card.setMaximumWidth(240)

        for i, card in enumerate(self._note_widgets):
            row, col = divmod(i, cols)
            self.grid_layout.addWidget(card, row, col)

        rows = (len(self._note_widgets) + cols - 1) // cols

        for c in range(max(self._last_cols, cols) + 1):
            self.grid_layout.setColumnStretch(c, 0)
        for r in range(max(self._last_rows, rows) + 1):
            self.grid_layout.setRowStretch(r, 0)

        for c in range(cols):
            self.grid_layout.setColumnStretch(c, 1)
        self.grid_layout.setRowStretch(rows, 1)

        self._last_cols = cols
        self._last_rows = rows

    def _new_note(self):
        if self._filter == "trash": return
        dlg = NoteEditDialog(self, self.db)
        if dlg.exec():
            self._reload_all()    # FIX P
            # FIX M: doğru toast (Make a copy için)
            action = getattr(dlg, "_result_action", "saved")
            if action == "duplicated":
                self._toast.show_message("📋 Note duplicated")
            else:
                self._toast.show_message("✓ Note saved")

    def _edit_note(self, note_id: int):
        if self._filter == "trash": return
        dlg = NoteEditDialog(self, self.db, note_id)
        if dlg.exec():
            self._reload_all()    # FIX P
            action = getattr(dlg, "_result_action", "saved")
            if action == "trashed":
                self._toast.show_message("🗑️ Moved to trash")
            elif action == "duplicated":
                self._toast.show_message("📋 Note duplicated")
            else:
                self._toast.show_message("✓ Note updated")

    def _show_card_menu(self, note_id: int, global_pos):
        menu = QMenu(self)
        if self._filter == "trash":
            menu.addAction("♻️ Restore", lambda: self._move_status(note_id, "active"))
            menu.addSeparator()
            menu.addAction("🗑️ Delete forever", lambda: self._delete_permanently(note_id))
        else:
            menu.addAction("✏️ Edit", lambda: self._edit_note(note_id))
            menu.addAction("📌 Pin / Unpin", lambda: self._toggle_pin(note_id))
            menu.addAction("📋 Copy text", lambda: self._copy_note_text(note_id))
            menu.addAction("📄 Download as Markdown", lambda: self._export_card_md(note_id))
            menu.addSeparator()
            if self._filter == "archive":
                menu.addAction("📤 Unarchive", lambda: self._move_status(note_id, "active"))
            else:
                menu.addAction("📦 Archive", lambda: self._move_status(note_id, "archived"))
            menu.addAction("🗑️ Move to Trash", lambda: self._move_status(note_id, "trash"))
        menu.exec(global_pos)

    def _toggle_pin(self, note_id: int):
        self.db.toggle_pin(note_id)
        self._reload_all()    # FIX P

    def _move_status(self, note_id: int, new_status: str):
        self.db.set_status(note_id, new_status)
        self._reload_all()    # FIX P
        msg = {"active": "♻️ Restored", "archived": "📦 Archived", "trash": "🗑️ Moved to trash"}
        self._toast.show_message(msg.get(new_status, "Done"))

    def _delete_permanently(self, note_id: int):
        reply = QMessageBox.question(self, "Delete forever", "Are you sure you want to permanently delete this note?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_permanently(note_id)
            self._reload_all()    # FIX P
            self._toast.show_message("🗑️ Deleted forever")

    def _export_card_md(self, note_id: int):
        row = self.db.get(note_id)
        safe = re.sub(r"[^\w\s\-]", "", (row["title"] if row else "note") or "note")[:60].strip() or "note"
        path, _ = QFileDialog.getSaveFileName(self, "Save as Markdown",
                                              os.path.join(os.path.expanduser("~"), f"{safe}.md"),
                                              "Markdown (*.md);;Text (*.txt)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.db.note_to_markdown(note_id))
            self._toast.show_message("✓ Markdown saved")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {e}")

    def _backup_zip(self):
        default = os.path.join(os.path.expanduser("~"), f"kizen-backup-{datetime.now():%Y%m%d-%H%M}.zip")
        path, _ = QFileDialog.getSaveFileName(self, "Save backup", default, "ZIP (*.zip)")
        if not path: return
        try:
            self.db.export_backup_zip(path)
            self._toast.show_message(f"✓ Backup: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Backup failed: {e}")

    def _export_all_md(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Markdown folder")
        if not dir_path: return
        try:
            n = self.db.export_all_markdown(dir_path)
            self._toast.show_message(f"✓ {n} notes exported")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {e}")

    def _open_settings(self):
        dlg = SettingsDialog(self, _theme_mode)
        if dlg.exec():
            set_mode(dlg.mode)
            if dlg.font_size != _body_font_size:
                _apply_font_size(dlg.font_size)
            _apply_theme(QApplication.instance())
            self._restyle_sidebar()
            self._reload_all()    # FIX P

    def _open_tag_manager(self):
        dlg = TagManagerDialog(self, self.db)
        dlg.exec()
        self._reload_all()    # FIX P

    def _bind_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, self._new_note)
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+Shift+E"), self, self._backup_zip)

    def _focus_search(self):
        self.search_edit.setFocus(); self.search_edit.selectAll()

    def keyPressEvent(self, event):
        focused = QApplication.focusWidget()
        if isinstance(focused, (QLineEdit, QTextEdit)):
            super().keyPressEvent(event); return
        if self._filter == "trash":
            super().keyPressEvent(event); return
        if event.matches(QKeySequence.Paste):
            mime = QApplication.clipboard().mimeData()
            if mime.hasImage():
                img = QImage(mime.imageData())
                if not img.isNull():
                    dest = os.path.join(ASSETS_DIR, f"{uuid.uuid4().hex}.png")
                    img.save(dest)
                    dlg = NoteEditDialog(self, self.db)
                    dlg._image_path = dest
                    dlg._update_image_preview()
                    if dlg.exec():
                        self._reload_all()    # FIX P
                        self._toast.show_message("✓ Note created from clipboard image")
                    else:
                        if os.path.exists(dest):
                            try: os.remove(dest)
                            except Exception: pass
                    event.accept(); return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        try: self.db.close()
        finally: event.accept()


# ============================================================
# ENTRY
# ============================================================
def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("⚡Kizen-Notes")
    app.setFont(_font(11))

    cfg = _load_config()
    global _body_font_size
    _body_font_size = cfg.get("font_size", 13)

    set_mode(cfg.get("theme", "system"))
    _apply_theme(app)

    window = ProjectKizenNotes()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()