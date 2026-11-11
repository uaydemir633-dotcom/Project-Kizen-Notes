<img width="1366" height="768" alt="Screenshot_27" src="https://github.com/user-attachments/assets/ad6bb8c9-1bec-4721-a684-ac9e120c71d0" />
<img width="1366" height="768" alt="Screenshot_28" src="https://github.com/user-attachments/assets/0551231d-fe3c-4a41-bb4e-4a8b289d9537" />
<div align="center">

# ⚡Project-Kizen-Notes

### Local-first, Google Keep-style notes app built with Python + PySide6

**Rich text · Colors · Labels · Pinning · Image attachments · Version history · Markdown & ZIP export**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg?style=flat-square)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](#-license)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)]()
[![UI: PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?style=flat-square&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Status](https://img.shields.io/badge/status-stable-brightgreen?style=flat-square)]()

<br>

[![Download for Windows](https://img.shields.io/badge/Download-Windows%20.exe-0078D7?style=for-the-badge&logo=windows)](https://github.com/uaydemir633-dotcom/Project-Kizen-Notes/releases/download/v1.0.0/Kizen-Notes.exe)
[![View Release Notes](https://img.shields.io/badge/View-Release%20Notes-black?style=for-the-badge&logo=github)](https://github.com/uaydemir633-dotcom/Project-Kizen-Notes/releases)

</div>

---

## 🌟 Overview

**Kizen-Notes** is a fully offline, distraction-free notes app inspired by Google Keep. It runs as a single-file desktop application on top of **PySide6 (Qt 6)** and stores everything locally in a SQLite database — **no cloud, no account, no telemetry**.

Write, color-code, pin, tag, and archive notes. Attach images by picking, dragging & dropping, or pasting. Every edit is preserved in a version history you can restore from. Export your entire workspace as a ZIP backup or as a folder of Markdown files whenever you want.

> **Status:** `v1.0.0` — **Stable**. Ready for daily use.

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
- **Pinned** — pinned notes float here for quick access
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

### Option 1: Download Executable (Windows)
You don't need Python installed to use Kizen-Notes. Simply download the latest `.exe` from the [Releases page](https://github.com/uaydemir633-dotcom/Project-Kizen-Notes/releases/latest) and double-click it to run. 
*(Note: Because the app is newly released, Windows SmartScreen might show an "Unknown Publisher" warning. Click "More info" → "Run anyway". Code signing is currently in progress).*

### Option 2: Run from Source (Python)
```bash
git clone https://github.com/uaydemir633-dotcom/Project-Kizen-Notes.git
cd Project-Kizen-Notes

pip install PySide6

python project_kizen_Notes_v1_0_0.py
```

### First Launch

The app creates its workspace automatically:

```text
~/.kizen/
├── notes.db          # SQLite database (notes + version history)
├── config.json       # Theme, font size, custom labels
└── assets/           # Attached images (content-hashed filenames)
```

- The toast **"✓ ⚡Kizen-Notes v1.0.0"** appears at the top to confirm launch.
- Click **＋ Take a note…** or press `Ctrl + N` to write your first note.

---

## 📁 Project Structure

```text
Project-Kizen-Notes/
├── project_kizen_Notes_v1_0_0.py      # Single-file PySide6 app
├── README.md                           # This file
└── LICENSE                             # MIT
```

Runtime files (auto-created, not in the repo):

```text
~/.kizen/notes.db           # SQLite database
~/.kizen/config.json        # User config
~/.kizen/assets/            # Attached images
```

---

## 🗂️ Version History

### `v1.0.0` — First stable release 🎉

**37 bug fixes since alpha:**

- **Editor:** pin state persistence, no-op save guard, orphan image cleanup on cancel/duplicate/delete
- **Database:** HTML + plain_body sync on tag deletion, `VACUUM INTO` for safe backup
- **Theme:** persisted light/dark/system mode, live widget restyling on switch
- **Sidebar:** property-driven collapse mode, footer hidden when collapsed, auto filter reset on tag deletion
- **History:** restore confirmation dialog, "Restore" button (was "Download")
- **UX:** correct toast messages (saved/trashed/duplicated), "Pinned" label accuracy
- **Extra:** Trash context menu hides "New note", paste-create blocked in Trash view

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

---

## 🐛 Known Limitations

- **No color-filter buttons in the sidebar.** The database layer (`NotesDB.list_all`) supports `filter_mode="color:<name>"`, but the UI doesn't expose color filters yet. Planned for `v1.1.0`.
- **No system tray / global hotkey.** The app must be open to use. Planned for `v1.1.0`.
- **No multi-select / bulk operations.** Notes are processed one at a time. Planned for `v1.1.0`.
- **No import from Google Keep.** Export only, for now. Planned for `v1.2.0`.

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

*Code signing services for Windows executables are provided by the **SignPath Foundation**.*

<br>

**Made with ⚡ by Kizen**

*If Kizen-Notes replaced your note-taking app, consider giving it a ⭐*

</div>
