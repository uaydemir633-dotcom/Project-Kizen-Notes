<div align="center">

# ⚡Project-Kizen-Notes

### Local-first, Google Keep-style notes app built with Python + PySide6

**Rich text · Colors · Labels · Pinning · Image attachments · Version history · Markdown & ZIP export**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.0.0a1-orange.svg?style=flat-square)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](#-license)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)]()
[![UI: PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?style=flat-square&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Status](https://img.shields.io/badge/status-alpha-orange?style=flat-square)]()

</div>

---

## 🌟 Overview

**Kizen-Notes** is a fully offline, distraction-free notes app inspired by Google Keep. It runs as a single-file desktop application on top of **PySide6 (Qt 6)** and stores everything locally in a SQLite database — **no cloud, no account, no telemetry**.

Write, color-code, pin, tag, and archive notes. Attach images by picking, dragging & dropping, or pasting. Every edit is preserved in a version history you can restore from. Export your entire workspace as a ZIP backup or as a folder of Markdown files whenever you want.

> **Status:** `v1.0.0a1` — Alpha. Core functionality is stable and ready for daily use, but expect occasional polish passes on UI details.

---

## ✨ Features

### 📝 Notes Management

- **Create / Edit / Delete** notes with a Keep-style editor dialog
- **Pin notes** to the top of the list with the 📌 toggle
- **7 note colors** — Default, Red, Orange, Yellow, Green, Blue, Purple (auto-adapts to light/dark theme)
- **Rich text** — Bold, Italic, Underline, Strikethrough formatting
- **Checkboxes** — insert `[ ]` / `[x]` items that render as ☐ / ☑ in the preview
- **Images** — attach via file picker, drag & drop, or paste from clipboard (Ctrl+V)
- **Duplicate notes** from the editor's ⋮ menu ("Make a copy")
- **Version history** — every save snapshots the previous state; restore any version later
- **Empty-note guard** — empty notes are quietly discarded, no clutter

### 🗂️ Organization

- **Notes** — all active notes
- **Reminders** — pinned notes float here for quick access
- **Archive** — keep completed notes but out of the main view
- **Trash** — recoverable; delete permanently only when you choose
- **Labels** — write `#tag` inline, and the tag appears in the sidebar and as chips on the note card
- **Label manager** — create custom labels without writing them in a note, delete labels from all notes at once

### 🔍 Search

- **Real-time search** (300 ms debounce) across titles and bodies
- **Highlighted matches** — matched text is highlighted with yellow in both title and preview
- **Clear button** appears while searching

### 🎨 Interface

- **Gemini/Keep-inspired clean layout** — header + sidebar + grid of note cards
- **Grid view ↔ List view** toggle
- **Collapsible sidebar** — full (256 px) or icon-only (72 px)
- **Light / Dark / System theme** — switchable from Settings or the ⚙ menu
- **Accent color** (soft yellow `#FDD663`) for highlights, pins, and the FAB
- **Adjustable body font size** — Small (11), Normal (13), Large (15)
- **Drag & drop** images directly into the editor
- **Toast notifications** for save / copy / restore actions
- **Drop shadows** on cards and FAB for a soft Material feel
- **Empty state illustrations** — tailored per view (Notes / Archive / Trash / Search / Label)

### 💾 Export & Backup

| Action | Where | Output |
|---|---|---|
| **Save note as Markdown** | ⋮ menu on card or editor | Single `.md` file with image link |
| **Export all notes** | Right-click on grid → *Export all notes to Markdown folder* | One `.md` file per note in a folder |
| **Backup everything** | Right-click on grid → *Backup all notes as ZIP* or `Ctrl + Shift + E` | `.zip` containing `notes.db` + all attached assets |

### ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + N` | New note |
| `Ctrl + F` | Focus search |
| `Ctrl + Shift + E` | Backup all notes as ZIP |
| `Ctrl + S` | Save (inside the editor) |
| `Esc` | Save and close the editor |

### 🖱️ Context Menus

**Right-click on any note card:**

- ✏️ Edit
- 📌 Pin / Unpin
- 📋 Copy text (title + body to clipboard)
- 📄 Download as Markdown
- 📦 Archive / 📤 Unarchive
- 🗑️ Move to Trash

**In Trash:**

- ♻️ Restore
- 🗑️ Delete forever (with confirmation)

**Right-click on empty grid area:**

- ＋ New note
- 🗂️ Backup all notes as ZIP
- 📄 Export all notes to Markdown folder

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/Project-Kizen-Notes.git
cd Project-Kizen-Notes

pip install PySide6

python project_kizen_Notes_v1_0_0a1.py
```

### First Launch

The app creates its workspace automatically:

```text
~/.kizen/
├── notes.db          # SQLite database (notes + version history)
├── config.json       # Theme, font size, custom labels
└── assets/           # Attached images (content-hashed filenames)
```

- The toast **"✓ ⚡Kizen-Notes v1.0.0a1"** appears at the top to confirm launch.
- Click **＋ Take a note…** or press `Ctrl + N` to write your first note.

---

## 📁 Project Structure

```text
Project-Kizen-Notes/
├── project_kizen_Notes_v1_0_0a1.py   # Single-file PySide6 app
├── README.md                          # This file
└── LICENSE                            # MIT
```

Runtime files (auto-created, not in the repo):

```text
~/.kizen/notes.db           # SQLite database
~/.kizen/config.json        # User config
~/.kizen/assets/            # Attached images
```

---

## 🗂️ Version History

### `v1.0.0a1` — Initial alpha

- 🎉 First public release of the standalone notes app
- **PySide6 (Qt 6)** UI, Google Keep-inspired design
- Notes CRUD with pinning, colors, trash, archive
- Rich-text editor with B/I/U/S, checkboxes, image attachment (pick / drag / paste)
- Per-note **version history** with restore
- Label system based on `#tags` in body text + custom labels via Label Manager
- Real-time search with match highlighting
- Grid / List view toggle, collapsible sidebar
- Light / Dark / System theme, adjustable font size
- Export to Markdown (single or bulk), full ZIP backup (`Ctrl + Shift + E`)
- Keyboard shortcuts: `Ctrl+N`, `Ctrl+F`, `Ctrl+Shift+E`, `Ctrl+S`, `Esc`

---

## 🐛 Known Limitations

- **No color-filter buttons in the sidebar.** The database layer (`NotesDB.list_all`) supports `filter_mode="color:<name>"`, but `_build_sidebar` only creates buttons for *Notes*, *Reminders*, *Archive*, *Trash*, and label filters. If you want to expose color filters in the UI, add buttons in `_build_sidebar` that call `_set_filter(f"color:{name}")`.
- **Default font size is 14, but the Settings dialog only offers 11 / 13 / 15.** Opening Settings will visually show no preset selected; picking any option will overwrite the default. If you want the middle option to be the default, either change `_body_font_size = 13` in the code or add a 14 option to `SettingsDialog`.
- **`__version__.py` is optional.** The module tries `from __version__ import __version__, __repo__` and falls back to `1.0.0a1` / `uaydemir633-dotcom/Kizen-Notes`. If you ship a separate `__version__.py`, keep it in sync with `README.md`'s badges.
- **Version history button says "Download" but actually restores.** `HistoryDialog` labels the action `Download`; clicking it calls `db.restore_version` and overwrites the current note. This is intentional in the code path but the label is misleading.

---

## 🤝 Contributing

Issues and pull requests are welcome. Guidelines:

1. **Bug reports** — include Python version, PySide6 version, OS, and the full traceback
2. **Feature requests** — open a discussion first for anything beyond a small patch
3. **Code style** — keep the single-file structure; the whole app is intentionally readable top-to-bottom
4. **Testing** — smoke test **create → edit → pin → color → label → search → export → backup** before submitting

---

## 🙏 Acknowledgments

- [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/) — the UI framework
- Google Keep — for the original visual inspiration
- [Project-Kizen-Client](../Project-Kizen-Client) — sibling AI client sharing the `~/.kizen/` workspace convention

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

**Made with ⚡ by Kizen**

*If Kizen-Notes replaced your note-taking app, consider giving it a ⭐*

</div>
