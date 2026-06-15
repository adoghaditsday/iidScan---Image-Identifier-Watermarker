import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from .activity_log import EncodedActivityLog
from .auth import create_account, derive_user_key, verify_login
from .config import APP_NAME, APP_VERSION, LOGO_PATH, MARKED_DIR, SNAPSHOT_DIR, REPORT_DIR, STORAGE_DIR
from .database import IdentifierDatabase
from .reports import create_mark_report, create_scan_report
from .snapshots import create_snapshot
from .watermark import build_payload, embed_identifier, extract_identifier, generate_identifier, sha256_file

IMAGE_TYPES = [("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All files", "*.*")]

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

SMOKE = "#08090c"
PANEL = "#111318"
PANEL_2 = "#171a21"
TEXT = "#f2f4f8"
MUTED = "#9ca3af"
RED = "#9d1f2f"
BLUE = "#1f4fa3"
GREEN = "#237847"
HOVER_RED = "#c12d42"
HOVER_BLUE = "#2f6bd8"
HOVER_GREEN = "#2e9b5d"


class ImageIdentifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1040x720")
        self.minsize(900, 620)
        self.configure(fg_color=SMOKE)

        self.db = IdentifierDatabase()
        self.current_user = None
        self.user_key = None
        self.activity_log = None
        self.preview_photo_refs = []
        self.selected_paths = []
        self.selected_card_indices = set()
        self.card_widgets = {}
        self.active_modal = None
        self.mode_var = tk.StringVar(value="Simplified")
        self.status_var = tk.StringVar(value="Ready")
        self.output_dir_var = tk.StringVar(value=str(STORAGE_DIR.resolve()))
        self.last_action_summary = tk.StringVar(value="No image submitted yet.")
        self.last_save_path = tk.StringVar(value="")

        self.after(150, self._show_splash)

    def _clear_root(self):
        for child in self.winfo_children():
            child.destroy()

    def _show_splash(self):
        self._clear_root()
        frame = ctk.CTkFrame(self, fg_color=SMOKE, corner_radius=0)
        frame.pack(fill="both", expand=True)
        try:
            img = Image.open(LOGO_PATH)
            img.thumbnail((430, 240))
            self.logo_photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            ctk.CTkLabel(frame, image=self.logo_photo, text="").pack(expand=True)
        except Exception:
            ctk.CTkLabel(frame, text="GSG3\nIMAGE IDENTIFIER", font=("Segoe UI", 34, "bold"), text_color=TEXT).pack(expand=True)
        ctk.CTkLabel(frame, text="Local identifier studio", font=("Segoe UI", 12), text_color=MUTED).pack(pady=(0, 28))
        self.after(1100, self._show_auth)

    def _show_auth(self):
        self._clear_root()
        shell = ctk.CTkFrame(self, fg_color=SMOKE, corner_radius=0)
        shell.pack(fill="both", expand=True, padx=32, pady=32)
        card = ctk.CTkFrame(shell, fg_color=PANEL, corner_radius=24, border_width=1, border_color="#242936")
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="Image Identifier", font=("Segoe UI", 30, "bold"), text_color=TEXT).pack(padx=42, pady=(34, 6))
        ctk.CTkLabel(card, text="Local sign-in", font=("Segoe UI", 13), text_color=MUTED).pack(pady=(0, 24))

        self.auth_username = ctk.CTkEntry(card, width=330, height=42, placeholder_text="Username", fg_color=PANEL_2, border_color=BLUE)
        self.auth_username.pack(padx=42, pady=(0, 12))
        self.auth_password = ctk.CTkEntry(card, width=330, height=42, placeholder_text="Password", show="*", fg_color=PANEL_2, border_color=BLUE)
        self.auth_password.pack(padx=42, pady=(0, 18))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(pady=(0, 18))
        ctk.CTkButton(row, text="Sign In", command=self._sign_in, fg_color=BLUE, hover_color=HOVER_BLUE, width=155, height=40).pack(side="left", padx=(0, 10))
        ctk.CTkButton(row, text="Create Account", command=self._sign_up, fg_color=GREEN, hover_color=HOVER_GREEN, width=155, height=40).pack(side="left")

        self.auth_status = ctk.CTkLabel(card, text="", text_color=MUTED, width=360)
        self.auth_status.pack(pady=(0, 28))
        self.auth_username.focus_set()
        self.bind("<Return>", lambda _e: self._sign_in())

    def _sign_up(self):
        ok, msg = create_account(self.auth_username.get(), self.auth_password.get())
        self.auth_status.configure(text=msg, text_color=(GREEN if ok else HOVER_RED))

    def _sign_in(self):
        username = self.auth_username.get()
        password = self.auth_password.get()
        ok, msg, normalized = verify_login(username, password)
        if not ok or not normalized:
            self.auth_status.configure(text=msg, text_color=HOVER_RED)
            return
        self.current_user = normalized
        self.user_key = derive_user_key(normalized, password)
        self.activity_log = EncodedActivityLog(normalized, self.user_key)
        self.activity_log.append(f"User signed in: {normalized}")
        self.unbind("<Return>")
        self._build_main_ui()

    def _build_main_ui(self):
        self._clear_root()
        self.configure(fg_color=SMOKE)

        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=68)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Image Identifier", font=("Segoe UI", 22, "bold"), text_color=TEXT).pack(side="left", padx=22)

        self.mode_switch = ctk.CTkSegmentedButton(header, values=["Simplified", "Advanced"], variable=self.mode_var, command=lambda _v: self._render_mode(),
                                                  fg_color=PANEL_2, selected_color=RED, selected_hover_color=HOVER_RED, unselected_color=PANEL_2,
                                                  unselected_hover_color="#222733")
        self.mode_switch.pack(side="left", padx=14)

        self.user_menu = ctk.CTkOptionMenu(header, values=[self.current_user or "User", "Sign Out", "Close Program"], command=self._user_menu_action,
                                           fg_color=PANEL_2, button_color=BLUE, button_hover_color=HOVER_BLUE, dropdown_fg_color=PANEL_2,
                                           dropdown_hover_color=RED, text_color=TEXT, width=190)
        self.user_menu.set(self.current_user or "User")
        self.user_menu.pack(side="right", padx=22)

        self.body = ctk.CTkFrame(self, fg_color=SMOKE, corner_radius=0)
        self.body.pack(fill="both", expand=True, padx=18, pady=18)

        self._render_mode()
        self._log("Main interface opened.")

    def _user_menu_action(self, choice):
        self.user_menu.set(self.current_user or "User")
        if choice == "Sign Out":
            self._sign_out()
        elif choice == "Close Program":
            self.destroy()

    def _render_mode(self):
        for child in self.body.winfo_children():
            child.destroy()
        if self.mode_var.get() == "Advanced":
            self._build_advanced()
        else:
            self._build_simplified()

    def _top_controls(self, parent):
        controls = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=18)
        controls.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(controls, text="Signature", text_color=MUTED).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.signature_name = ctk.CTkEntry(controls, fg_color=PANEL_2, border_color=BLUE)
        self.signature_name.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        self.signature_name.insert(0, self.current_user or "Local User")

        ctk.CTkLabel(controls, text="Note", text_color=MUTED).grid(row=0, column=1, sticky="w", padx=8, pady=(14, 4))
        self.signature_note = ctk.CTkEntry(controls, fg_color=PANEL_2, border_color=BLUE)
        self.signature_note.grid(row=1, column=1, sticky="ew", padx=8, pady=(0, 14))

        ctk.CTkLabel(controls, text="Save Folder", text_color=MUTED).grid(row=0, column=2, sticky="w", padx=8, pady=(14, 4))
        self.output_dir_entry = ctk.CTkEntry(controls, textvariable=self.output_dir_var, fg_color=PANEL_2, border_color=BLUE)
        self.output_dir_entry.grid(row=1, column=2, sticky="ew", padx=8, pady=(0, 14))
        ctk.CTkButton(controls, text="Change", command=self.change_output_dir, fg_color=BLUE, hover_color=HOVER_BLUE, width=92).grid(row=1, column=3, padx=(4, 16), pady=(0, 14))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=2)
        return controls

    def _action_buttons(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))
        ctk.CTkButton(row, text="Select Images", command=self.select_images, fg_color=BLUE, hover_color=HOVER_BLUE, height=42).pack(side="left", padx=(0, 10))
        ctk.CTkButton(row, text="Mark Selected", command=self.mark_selected, fg_color=GREEN, hover_color=HOVER_GREEN, height=42).pack(side="left", padx=(0, 10))
        ctk.CTkButton(row, text="Scan Selected", command=self.scan_selected, fg_color=RED, hover_color=HOVER_RED, height=42).pack(side="left", padx=(0, 10))
        ctk.CTkButton(row, text="Open Save Folder", command=self.open_storage, fg_color=PANEL_2, hover_color="#262b38", height=42).pack(side="left")
        return row

    def _build_simplified(self):
        self._top_controls(self.body)
        self._action_buttons(self.body)
        main = ctk.CTkFrame(self.body, fg_color="transparent")
        main.pack(fill="both", expand=True)
        preview_card = ctk.CTkFrame(main, fg_color=PANEL, corner_radius=18)
        preview_card.pack(side="left", fill="both", expand=True, padx=(0, 14))
        ctk.CTkLabel(preview_card, text="Submitted Images", font=("Segoe UI", 16, "bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(16, 8))
        self._create_preview_area(preview_card)

        status_card = ctk.CTkFrame(main, fg_color=PANEL, corner_radius=18, width=310)
        status_card.pack(side="right", fill="y")
        status_card.pack_propagate(False)
        ctk.CTkLabel(status_card, text="Status", font=("Segoe UI", 16, "bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(18, 8))
        ctk.CTkLabel(status_card, textvariable=self.last_action_summary, text_color=TEXT, justify="left", wraplength=260).pack(anchor="w", padx=18, pady=(4, 16))
        ctk.CTkLabel(status_card, text="Saved To", text_color=MUTED).pack(anchor="w", padx=18, pady=(8, 4))
        ctk.CTkLabel(status_card, textvariable=self.last_save_path, text_color=MUTED, justify="left", wraplength=260).pack(anchor="w", padx=18)

        if self.selected_paths:
            self._display_submitted_images(self.selected_paths)

    def _build_advanced(self):
        self._top_controls(self.body)
        self._action_buttons(self.body)
        tabs = ctk.CTkTabview(self.body, fg_color=PANEL, segmented_button_selected_color=RED, segmented_button_selected_hover_color=HOVER_RED)
        tabs.pack(fill="both", expand=True)
        img_tab = tabs.add("Images")
        log_tab = tabs.add("Action Log")
        report_tab = tabs.add("Storage")
        self._create_preview_area(img_tab)
        if self.selected_paths:
            self._display_submitted_images(self.selected_paths)

        log_row = ctk.CTkFrame(log_tab, fg_color="transparent")
        log_row.pack(fill="x", padx=12, pady=12)
        ctk.CTkButton(log_row, text="Refresh Log", command=self._refresh_action_log, fg_color=BLUE, hover_color=HOVER_BLUE).pack(side="left", padx=(0, 10))
        ctk.CTkButton(log_row, text="Open Encoded Log", command=self._open_encoded_log_file, fg_color=PANEL_2, hover_color="#262b38").pack(side="left")
        self.action_log_view = ctk.CTkTextbox(log_tab, fg_color="#0b0d11", text_color=TEXT, font=("Consolas", 11), wrap="word")
        self.action_log_view.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._refresh_action_log()

        ctk.CTkLabel(report_tab, text="Local folders", font=("Segoe UI", 16, "bold"), text_color=TEXT).pack(anchor="w", padx=16, pady=(18, 8))
        for label, p in [("Base", self._base_dir()), ("Marked", self._marked_dir()), ("Snapshots", self._snapshot_dir()), ("Reports", self._report_dir())]:
            row = ctk.CTkFrame(report_tab, fg_color=PANEL_2, corner_radius=12)
            row.pack(fill="x", padx=14, pady=6)
            ctk.CTkLabel(row, text=label, width=90, text_color=MUTED).pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(row, text=str(p), text_color=TEXT, anchor="w").pack(side="left", fill="x", expand=True, padx=10)
            ctk.CTkButton(row, text="Open", width=70, command=lambda path=p: self._open_path(path), fg_color=BLUE, hover_color=HOVER_BLUE).pack(side="right", padx=10, pady=8)

    def _create_preview_area(self, parent):
        self.preview_scroll = ctk.CTkScrollableFrame(parent, fg_color=PANEL, corner_radius=0)
        self.preview_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.empty_preview = ctk.CTkLabel(self.preview_scroll, text="No images selected.", text_color=MUTED, font=("Segoe UI", 14))
        self.empty_preview.grid(row=0, column=0, padx=16, pady=16, sticky="w")

    def _base_dir(self) -> Path:
        p = Path(self.output_dir_var.get()).expanduser()
        return p

    def _marked_dir(self) -> Path:
        return self._base_dir() / "marked"

    def _snapshot_dir(self) -> Path:
        return self._base_dir() / "snapshots"

    def _report_dir(self) -> Path:
        return self._base_dir() / "reports"

    def _ensure_dirs(self):
        for p in [self._base_dir(), self._marked_dir(), self._snapshot_dir(), self._report_dir()]:
            p.mkdir(parents=True, exist_ok=True)

    def change_output_dir(self):
        chosen = filedialog.askdirectory(title="Choose save folder", initialdir=str(self._base_dir() if self._base_dir().exists() else STORAGE_DIR))
        if chosen:
            self.output_dir_var.set(chosen)
            self._ensure_dirs()
            self.last_save_path.set(chosen)
            self._log(f"Save folder changed: {chosen}")
            self._render_mode()

    def select_images(self):
        files = filedialog.askopenfilenames(title="Select image files", filetypes=IMAGE_TYPES)
        if not files:
            return
        self.selected_paths = [Path(f) for f in files]
        self.selected_card_indices = set(range(len(self.selected_paths)))
        self._display_submitted_images(self.selected_paths)
        self.last_action_summary.set(f"Selected {len(self.selected_paths)} image(s).")
        self._log(f"Selected {len(self.selected_paths)} image(s).")

    def _display_submitted_images(self, paths):
        if not hasattr(self, "preview_scroll"):
            return
        for child in self.preview_scroll.winfo_children():
            child.destroy()
        self.preview_photo_refs.clear()
        self.card_widgets = {}
        if not paths:
            ctk.CTkLabel(self.preview_scroll, text="No images selected.", text_color=MUTED, font=("Segoe UI", 14)).grid(row=0, column=0, padx=16, pady=16, sticky="w")
            return
        self.selected_card_indices = {i for i in self.selected_card_indices if i < len(paths)} or set(range(len(paths)))
        for index, path in enumerate(paths):
            r, c = divmod(index, 4)
            cell = ctk.CTkFrame(self.preview_scroll, fg_color=PANEL_2, corner_radius=16, border_width=1, border_color="#242936")
            cell.grid(row=r, column=c, padx=10, pady=10, sticky="n")
            self.card_widgets[index] = cell
            cell.bind("<Button-1>", lambda _e, i=index: self._focus_card(i))
            try:
                img = Image.open(path)
                img.thumbnail((170, 130))
                photo = ctk.CTkImage(light_image=img.copy(), dark_image=img.copy(), size=img.size)
                self.preview_photo_refs.append(photo)
                image_label = ctk.CTkLabel(cell, image=photo, text="")
                image_label.pack(padx=10, pady=(10, 6))
                image_label.bind("<Button-1>", lambda _e, i=index: self._focus_card(i))
            except Exception:
                fallback = ctk.CTkLabel(cell, text="Preview unavailable", width=170, height=100, text_color=MUTED)
                fallback.pack(padx=10, pady=10)
                fallback.bind("<Button-1>", lambda _e, i=index: self._focus_card(i))
            name_label = ctk.CTkLabel(cell, text=path.name, text_color=TEXT, wraplength=170, justify="center", font=("Segoe UI", 10))
            name_label.pack(padx=8, pady=(0, 8))
            name_label.bind("<Button-1>", lambda _e, i=index: self._focus_card(i))
            toggle = ctk.CTkButton(cell, text="Selected", width=120, height=28, fg_color=PANEL, hover_color="#262b38",
                                   command=lambda i=index: self._toggle_card_selection(i))
            toggle.pack(pady=(0, 10))
            toggle.bind("<Return>", lambda _e, i=index: self._toggle_card_selection(i))
            toggle.bind("<space>", lambda _e, i=index: self._toggle_card_selection(i))
        self._refresh_card_styles()

    def _paths_for_action(self):
        if not self.selected_paths:
            return []
        valid = sorted(i for i in self.selected_card_indices if 0 <= i < len(self.selected_paths))
        if not valid:
            return list(self.selected_paths)
        return [self.selected_paths[i] for i in valid]

    def _toggle_card_selection(self, index):
        if index in self.selected_card_indices:
            self.selected_card_indices.remove(index)
        else:
            self.selected_card_indices.add(index)
        self._refresh_card_styles()

    def _focus_card(self, index):
        self.selected_card_indices = {index}
        self._refresh_card_styles()

    def _refresh_card_styles(self):
        for index, cell in getattr(self, "card_widgets", {}).items():
            if index in self.selected_card_indices:
                cell.configure(border_color=GREEN, border_width=2, fg_color="#1a2021")
            else:
                cell.configure(border_color="#242936", border_width=1, fg_color=PANEL_2)
        count = len(self.selected_card_indices)
        if self.selected_paths:
            self.status_var.set(f"{count or len(self.selected_paths)} image(s) active")

    def _remove_paths_from_selected(self, remove_paths):
        remove_set = {str(Path(p)) for p in remove_paths}
        self.selected_paths = [p for p in self.selected_paths if str(Path(p)) not in remove_set]
        self.selected_card_indices = set(range(len(self.selected_paths)))
        self._display_submitted_images(self.selected_paths)
        self.last_action_summary.set(f"Removed {len(remove_set)} image(s) from selected.")
        self._log(f"Removed {len(remove_set)} image(s) from selected list.")

    def _show_app_confirm(self, title, message, buttons):
        if self.active_modal is not None:
            try:
                self.active_modal.destroy()
            except Exception:
                pass
            self.active_modal = None

        overlay = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        card = ctk.CTkFrame(overlay, fg_color=PANEL, corner_radius=18, border_width=1, border_color="#343b4d")
        card.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 18, "bold"), text_color=TEXT).pack(anchor="w", padx=24, pady=(22, 6))
        ctk.CTkLabel(card, text=message, text_color=TEXT, justify="left", wraplength=430).pack(anchor="w", padx=24, pady=(0, 18))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(0, 22))

        def close_then(callback=None):
            try:
                self.unbind("<Escape>")
                self.unbind("<Return>")
            except Exception:
                pass
            try:
                overlay.destroy()
            finally:
                self.active_modal = None
            if callback:
                callback()

        color_cycle = [BLUE, GREEN, RED, PANEL_2]
        hover_cycle = [HOVER_BLUE, HOVER_GREEN, HOVER_RED, "#262b38"]
        first_btn = None
        for i, (label, callback) in enumerate(buttons):
            btn = ctk.CTkButton(row, text=label, width=122, height=36,
                                fg_color=color_cycle[i % len(color_cycle)],
                                hover_color=hover_cycle[i % len(hover_cycle)],
                                command=lambda cb=callback: close_then(cb))
            btn.pack(side="left", padx=(0, 10))
            if first_btn is None:
                first_btn = btn
        self.active_modal = overlay
        if first_btn:
            first_btn.focus_set()
            self.bind("<Return>", lambda _e: first_btn.invoke())
        self.bind("<Escape>", lambda _e: close_then(None))

    def _signature(self):
        name = getattr(self, "signature_name", None)
        note = getattr(self, "signature_note", None)
        return (name.get().strip() if name else self.current_user or "Local User", note.get().strip() if note else "")

    def mark_selected(self):
        if not self.selected_paths:
            self.select_images()
        action_paths = self._paths_for_action()
        if not action_paths:
            return
        self._ensure_dirs()
        sig_name, sig_note = self._signature()
        created, skipped = [], []
        self._log(f"Mark request started for {len(action_paths)} image(s).")

        for path in action_paths:
            try:
                existing = extract_identifier(path)
                if existing:
                    report_path = self._handle_detected_existing(path, existing, sig_name, sig_note)
                    skipped.append((path.name, report_path))
                    self._log(f"Existing identifier found in {path.name}; report created: {report_path}")
                    continue
                identifier = generate_identifier()
                payload = build_payload(identifier, sig_name, sig_note)
                output_path = self._marked_dir() / f"{path.stem}_{identifier}.png"
                snapshot_path = self._snapshot_dir() / f"{path.stem}_{identifier}.jpg"
                embed_identifier(path, output_path, payload)
                create_snapshot(output_path, snapshot_path)
                record = {
                    "identifier_code": identifier,
                    "original_filename": path.name,
                    "original_path": str(path),
                    "marked_path": str(output_path),
                    "snapshot_path": str(snapshot_path),
                    "sha256_hash": sha256_file(path),
                    "signature_name": sig_name,
                    "signature_note": sig_note,
                    "created_at": payload["created_at"],
                }
                record_id = self.db.add_image_record(**record)
                report_path = create_mark_report(record, report_dir=self._report_dir())
                self.db.update_image_record(record_id, report_path=str(report_path))
                created.append((identifier, output_path))
                self._log(f"Marked {path.name} -> {output_path} | ID: {identifier}")
            except Exception as exc:
                skipped.append((path.name, str(exc)))
                self._log(f"ERROR marking {path.name}: {exc}")

        if created:
            self.last_action_summary.set(f"Marked {len(created)} image(s) successfully.")
            self.last_save_path.set(str(self._marked_dir()))
        elif skipped:
            self.last_action_summary.set(f"No new marks created. {len(skipped)} image(s) already marked or failed.")
        message = f"Marked {len(created)} image(s)."
        if skipped:
            message += f"\nSkipped or reported: {len(skipped)}"
        self._render_mode()
        self._show_app_confirm("Mark Complete", message, [("Ok", None)])

    def scan_selected(self):
        if not self.selected_paths:
            self.select_images()
        action_paths = self._paths_for_action()
        if not action_paths:
            return
        self._ensure_dirs()
        sig_name, sig_note = self._signature()
        found, clean, reports = 0, 0, []
        marked_paths = []
        self._log(f"Scan request started for {len(action_paths)} image(s).")
        for path in action_paths:
            try:
                payload = extract_identifier(path)
                matched = None
                if payload:
                    found += 1
                    identifier = payload.get("identifier_code")
                    matched = self.db.find_by_identifier(identifier) if identifier else None
                    self._log(f"Identifier detected in {path.name}: {identifier}")
                    marked_paths.append(path)
                else:
                    clean += 1
                    self._log(f"No identifier detected in {path.name}")
                suffix = payload.get("identifier_code") if payload else "NO_IDENTIFIER"
                snapshot_path = self._snapshot_dir() / f"scan_{path.stem}_{suffix}.jpg"
                create_snapshot(path, snapshot_path)
                report_path = create_scan_report(path.name, str(path), payload, matched, sig_name, sig_note, report_dir=self._report_dir())
                self.db.add_scan_report(
                    scanned_filename=path.name,
                    scanned_path=str(path),
                    identifier_code=payload.get("identifier_code") if payload else None,
                    matched_record_id=matched.get("id") if matched else None,
                    report_path=str(report_path),
                    signature_name=sig_name,
                    signature_note=sig_note,
                )
                reports.append(report_path)
            except Exception as exc:
                self._log(f"ERROR scanning {path.name}: {exc}")
        self.last_action_summary.set(f"Marked found: {found}\nUnmarked: {clean}")
        self.last_save_path.set(str(self._report_dir()))
        self._render_mode()

        if found:
            message = f"Detected identifiers in {found} image(s)."
            if clean:
                message += f"\nUnmarked image(s): {clean}"
            message += "\n\nA scan report was created."
            buttons = [
                ("Check Report", (lambda p=reports[0]: self._open_path(p)) if reports else None),
                ("Ignore", None),
                ("Remove from Selected", lambda paths=list(marked_paths): self._remove_paths_from_selected(paths)),
            ]
            self._show_app_confirm("Marked Image Detected", message, buttons)
        else:
            self._show_app_confirm("Scan Complete", "No identifiers detected.\n\nThe selected image(s) are not marked.", [("Ok", None)])

    def _handle_detected_existing(self, path: Path, payload, sig_name: str, sig_note: str) -> Path:
        identifier = payload.get("identifier_code")
        matched = self.db.find_by_identifier(identifier) if identifier else None
        report_path = create_scan_report(path.name, str(path), payload, matched, sig_name, sig_note, report_dir=self._report_dir())
        self.db.add_scan_report(
            scanned_filename=path.name,
            scanned_path=str(path),
            identifier_code=identifier,
            matched_record_id=matched.get("id") if matched else None,
            report_path=str(report_path),
            signature_name=sig_name,
            signature_note=sig_note,
        )
        return report_path

    def open_storage(self):
        self._ensure_dirs()
        self._open_path(self._base_dir())
        self._log("Save folder opened.")

    def _log(self, text: str):
        if self.activity_log:
            self.activity_log.append(text)
        if hasattr(self, "action_log_view"):
            self._refresh_action_log()

    def _refresh_action_log(self):
        if not hasattr(self, "action_log_view") or not self.activity_log:
            return
        self.action_log_view.configure(state="normal")
        self.action_log_view.delete("1.0", "end")
        self.action_log_view.insert("end", self.activity_log.read() or "No actions logged yet.")
        self.action_log_view.configure(state="disabled")

    def _open_encoded_log_file(self):
        if self.activity_log:
            self._open_path(self.activity_log.path)

    def _sign_out(self):
        if self.activity_log and self.current_user:
            self.activity_log.append(f"User signed out: {self.current_user}")
        self.current_user = None
        self.user_key = None
        self.activity_log = None
        self.selected_paths = []
        self.selected_card_indices = set()
        self.card_widgets = {}
        self.active_modal = None
        self._show_auth()

    def _open_path(self, path: Path):
        path = Path(path)
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif os.name == "posix":
                import subprocess
                subprocess.Popen(["xdg-open", str(path)])
            else:
                messagebox.showinfo("Path", str(path))
        except Exception:
            messagebox.showinfo("Path", str(path))
