from pathlib import Path
from tkinter import Tk, Toplevel, ttk, filedialog, messagebox, StringVar, font as tkfont

from .api import build_query_url, fetch_json
from .constants import API_BASE_DEFAULT, APP_TITLE, DATA_JSON_DEFAULT, WINDOW_GEOMETRY, WINDOW_MIN_SIZE
from .data import extract_items, load_default_sql, load_items, prepare_db, run_report
from .models import ApiParams, AppConfig
from .settings import load_app_config, save_app_config


class ReportApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.minsize(*WINDOW_MIN_SIZE)

        self.json_path_var = StringVar(value=str(DATA_JSON_DEFAULT))
        self.api_url_var = StringVar(value=API_BASE_DEFAULT)
        self.aliases_var = StringVar(value="")

        self.param_vars = {
            "page": StringVar(value="1"),
            "page_size": StringVar(value="100"),
            "status": StringVar(value="active"),
            "amount_min": StringVar(value="500"),
            "amount_max": StringVar(value="500"),
            "period_days_max": StringVar(value="30"),
            "rating_min": StringVar(value="45"),
        }

        self.items_cache = None
        self.settings_win = None

        self._apply_style()
        self._build_ui()
        self._load_settings()
        self.refresh()

    def _apply_style(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        base_font = tkfont.nametofont("TkDefaultFont")
        base_font.configure(size=10)
        heading_font = base_font.copy()
        heading_font.configure(size=11, weight="bold")
        small_font = base_font.copy()
        small_font.configure(size=9)

        style.configure("TFrame", background="#f3f2f4")
        style.configure("TLabel", background="#f3f2f4", foreground="#1e1e1e")
        style.configure("Card.TFrame", background="#ffffff", relief="flat", borderwidth=1)
        style.configure("CardHeader.TLabel", background="#ffffff", foreground="#2b2b2b", font=heading_font)
        style.configure("Small.TLabel", background="#ffffff", foreground="#636b74", font=small_font)
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#222222", bordercolor="#cfcfd6")
        style.configure(
            "Primary.TButton",
            background="#2b6b3f",
            foreground="#ffffff",
            padding=(12, 6),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#235a34"), ("pressed", "#1f4f2e")],
            foreground=[("disabled", "#dddddd")],
        )
        style.configure(
            "Secondary.TButton",
            background="#e1ddd6",
            foreground="#1e1e1e",
            padding=(10, 5),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#d6d1c9"), ("pressed", "#c9c3ba")],
        )
        style.configure(
            "Blue.TButton",
            background="#4a84c7",
            foreground="#ffffff",
            padding=(12, 6),
        )
        style.map(
            "Blue.TButton",
            background=[("active", "#3e76b8"), ("pressed", "#356aa8")],
        )
        style.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#1d1d1d",
            rowheight=26,
            bordercolor="#e0dbd2",
        )
        style.configure(
            "Treeview.Heading",
            font=heading_font,
            background="#ece7de",
            foreground="#1e1e1e",
            padding=(6, 4),
        )
        style.map("Treeview.Heading", background=[("active", "#e2ddd4")])
        style.map(
            "Treeview",
            background=[("selected", "#6d94c7")],
            foreground=[("selected", "#ffffff")],
        )

    def _build_ui(self):
        self.root.configure(background="#f3f2f4")

        top = ttk.Frame(self.root, padding=(16, 12, 16, 6))
        top.pack(fill="x")
        top.columnconfigure(1, weight=1)
        top.columnconfigure(4, weight=1)

        ttk.Label(top, text="JSON file").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.json_path_var).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(top, text="Browse", command=self.browse_json, style="Secondary.TButton").grid(row=0, column=2, sticky="w")

        ttk.Button(top, text="Обновить", command=self.refresh, style="Primary.TButton").grid(row=0, column=3, sticky="e", padx=(12, 0))
        ttk.Button(top, text="Настройки", command=self.open_settings, style="Secondary.TButton").grid(row=0, column=4, sticky="e", padx=(8, 0))

        api_card = ttk.Frame(self.root, style="Card.TFrame", padding=(16, 12))
        api_card.pack(fill="x", padx=16, pady=(6, 10))
        api_card.columnconfigure(0, weight=1)

        ttk.Label(api_card, text="Параметры API", style="CardHeader.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Separator(api_card, orient="horizontal").grid(row=1, column=0, sticky="we", pady=(8, 10))

        api = ttk.Frame(api_card)
        api.grid(row=2, column=0, sticky="we")
        api.columnconfigure(1, weight=1)
        api.columnconfigure(3, weight=1)
        api.columnconfigure(5, weight=1)
        api.columnconfigure(7, weight=1)

        ttk.Label(api, text="Base URL").grid(row=0, column=0, sticky="w")
        ttk.Entry(api, textvariable=self.api_url_var).grid(row=0, column=1, columnspan=7, sticky="we", padx=6, pady=(0, 6))

        ttk.Label(api, text="page:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(api, textvariable=self.param_vars["page"], width=10).grid(row=1, column=1, sticky="w", padx=6, pady=(6, 0))

        ttk.Label(api, text="page_size:").grid(row=1, column=2, sticky="w", pady=(6, 0))
        ttk.Spinbox(api, from_=1, to=1000, textvariable=self.param_vars["page_size"], width=10).grid(
            row=1, column=3, sticky="w", padx=6, pady=(6, 0)
        )

        ttk.Label(api, text="status:").grid(row=1, column=4, sticky="w", pady=(6, 0))
        ttk.Combobox(api, textvariable=self.param_vars["status"], values=("active", "inactive", "closed"), width=12).grid(
            row=1, column=5, sticky="w", padx=6, pady=(6, 0)
        )

        ttk.Label(api, text="amount_min:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(api, textvariable=self.param_vars["amount_min"], width=10).grid(row=2, column=1, sticky="w", padx=6, pady=(6, 0))

        ttk.Label(api, text="amount_max:").grid(row=2, column=2, sticky="w", pady=(6, 0))
        ttk.Entry(api, textvariable=self.param_vars["amount_max"], width=10).grid(row=2, column=3, sticky="w", padx=6, pady=(6, 0))

        ttk.Label(api, text="period_days_max:").grid(row=2, column=4, sticky="w", pady=(6, 0))
        ttk.Entry(api, textvariable=self.param_vars["period_days_max"], width=12).grid(row=2, column=5, sticky="w", padx=6, pady=(6, 0))

        ttk.Label(api, text="rating_min:").grid(row=2, column=6, sticky="w", pady=(6, 0))
        ttk.Entry(api, textvariable=self.param_vars["rating_min"], width=8).grid(row=2, column=7, sticky="w", padx=6, pady=(6, 0))

        actions = ttk.Frame(api_card, style="Card.TFrame")
        actions.grid(row=3, column=0, sticky="we", pady=(12, 0))
        actions.columnconfigure(0, weight=1)

        ttk.Button(actions, text="Загрузить данные", command=self.fetch_only, style="Blue.TButton").grid(
            row=0, column=0, sticky="w"
        )
        right_actions = ttk.Frame(actions, style="Card.TFrame")
        right_actions.grid(row=0, column=1, sticky="e")
        ttk.Button(right_actions, text="Загрузить данные", command=self.fetch_only, style="Blue.TButton").pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(right_actions, text="Загрузить обновить", command=self.fetch_and_refresh, style="Primary.TButton").pack(
            side="left"
        )

        table_card = ttk.Frame(self.root, style="Card.TFrame", padding=(8, 8, 8, 10))
        table_card.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self.tree = ttk.Treeview(table_card, columns=(), show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(self.root, orient="horizontal", command=self.tree.xview)
        hsb.pack(fill="x", padx=16, pady=(0, 6))

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.status_var = StringVar(value="")
        status = ttk.Label(self.root, textvariable=self.status_var, padding=(16, 6))
        status.pack(fill="x")

    def browse_json(self):
        path = filedialog.askopenfilename(title="Select JSON", filetypes=[("JSON", "*.json"), ("All", "*")])
        if path:
            self.json_path_var.set(path)
            self._save_settings()

    def refresh(self):
        try:
            json_path = self.json_path_var.get()
            if self.items_cache is None:
                items = load_items(Path(json_path))
            else:
                items = self.items_cache
            conn = prepare_db(items)
            sql_text = load_default_sql()
            columns, rows = run_report(conn, sql_text)
            conn.close()

            self._render_table(columns, rows)
            self.status_var.set(f"Строк: {len(rows)}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def fetch_and_refresh(self):
        try:
            base_url = self.api_url_var.get().strip()
            params = {k: v.get().strip() for k, v in self.param_vars.items()}
            url = build_query_url(base_url, params)
            raw = fetch_json(url)
            self.items_cache = extract_items(raw)
            self._save_settings()
            self.refresh()
            self.status_var.set(f"Fetched rows: {len(self.items_cache)}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def fetch_only(self):
        try:
            base_url = self.api_url_var.get().strip()
            params = {k: v.get().strip() for k, v in self.param_vars.items()}
            url = build_query_url(base_url, params)
            raw = fetch_json(url)
            self.items_cache = extract_items(raw)
            self._save_settings()
            self.status_var.set(f"Fetched rows: {len(self.items_cache)}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _render_table(self, columns, rows):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns

        aliases = self._parse_aliases()
        for col in columns:
            title = aliases.get(col, col)
            self.tree.heading(col, text=title)
            self.tree.column(col, width=150, anchor="center", stretch=True)

        for row in rows:
            values = ["" if v is None else v for v in row]
            self.tree.insert("", "end", values=values)

        for i, item_id in enumerate(self.tree.get_children()):
            if i % 2 == 0:
                self.tree.item(item_id, tags=("even",))
            else:
                self.tree.item(item_id, tags=("odd",))

        self.tree.tag_configure("even", background="#ffffff")
        self.tree.tag_configure("odd", background="#f1eee8")

    def _parse_aliases(self):
        raw = self.aliases_var.get()
        if not raw.strip():
            return {}
        mapping = {}
        pairs = [p.strip() for p in raw.split(",") if p.strip()]
        for pair in pairs:
            if "=" not in pair:
                continue
            key, val = pair.split("=", 1)
            key = key.strip()
            val = val.strip()
            if key and val:
                mapping[key] = val
        return mapping

    def _load_settings(self):
        defaults = AppConfig(
            json_path=str(DATA_JSON_DEFAULT),
            api_base_url=API_BASE_DEFAULT,
            aliases="",
            api_params=ApiParams(),
        )
        cfg = load_app_config(defaults)
        self.json_path_var.set(cfg.json_path)
        self.api_url_var.set(cfg.api_base_url)
        self.aliases_var.set(cfg.aliases)
        for key, value in cfg.api_params.to_dict().items():
            if key in self.param_vars:
                self.param_vars[key].set(value)

    def _save_settings(self):
        config = AppConfig(
            json_path=self.json_path_var.get(),
            api_base_url=self.api_url_var.get(),
            aliases=self.aliases_var.get(),
            api_params=ApiParams.from_dict({k: v.get() for k, v in self.param_vars.items()}),
        )
        save_app_config(config)

    def open_settings(self):
        if self.settings_win and self.settings_win.winfo_exists():
            self.settings_win.focus()
            return

        win = Toplevel(self.root)
        win.title("Settings")
        win.geometry("520x200")
        win.minsize(420, 160)
        win.configure(background="#f6f5f1")
        self.settings_win = win

        frame = ttk.Frame(win, padding=(14, 12, 14, 12))
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Column aliases").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Format: column=Name, other=Custom Title").grid(row=1, column=0, sticky="w", pady=(2, 6))
        entry = ttk.Entry(frame, textvariable=self.aliases_var)
        entry.grid(row=2, column=0, sticky="we")

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Save", command=self._save_and_close, style="Primary.TButton").pack(side="right")
        ttk.Button(buttons, text="Cancel", command=win.destroy, style="Secondary.TButton").pack(side="right", padx=(0, 8))

        entry.focus_set()

    def _save_and_close(self):
        self._save_settings()
        self.refresh()
        if self.settings_win and self.settings_win.winfo_exists():
            self.settings_win.destroy()
