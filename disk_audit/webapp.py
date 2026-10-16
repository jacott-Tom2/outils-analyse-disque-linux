"""Interface web locale en lecture seule pour parcourir un disque."""

from __future__ import annotations

import argparse
import html
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

PREVIEW_TYPES = {
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image", ".webp": "image",
    ".heic": "image", ".pdf": "pdf", ".txt": "text", ".md": "text", ".csv": "text",
}


def safe_path(root: Path, requested: str) -> Path:
    """Resolve un chemin dans root et refuse toute sortie du disque analysé."""
    candidate = (root / unquote(requested.lstrip("/"))).resolve()
    if candidate != root and root not in candidate.parents:
        raise PermissionError("chemin hors du dossier analysé")
    return candidate


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("o", "Ko", "Mo", "Go", "To"):
        if value < 1024 or unit == "To":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} o"


def page(root: Path, current: Path, query: str = "") -> str:
    entries = []
    for item in sorted(current.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
        if query and query.lower() not in item.name.lower():
            continue
        try:
            stat = item.stat(follow_symlinks=False)
        except OSError:
            continue
        relative = item.relative_to(root).as_posix()
        href = "/browse/" + quote(relative, safe="/")
        if item.is_dir():
            entries.append(f"<tr><td>📁</td><td><a href='{href}'>{html.escape(item.name)}/</a></td><td>Dossier</td><td>—</td></tr>")
        else:
            kind = PREVIEW_TYPES.get(item.suffix.lower(), "")
            preview = f"<a href='/preview/{quote(relative, safe='/')}'>aperçu</a>" if kind else ""
            entries.append(f"<tr><td>📄</td><td>{html.escape(item.name)}</td><td>{html.escape(kind or 'fichier')}</td><td>{human_size(stat.st_size)} · {preview}</td></tr>")
    relative = current.relative_to(root).as_posix() if current != root else ""
    parent = current.parent.relative_to(root).as_posix() if current != root else None
    parent_link = f"<a href='/browse/{quote(parent or '', safe='/')}'>⬆ dossier parent</a>" if parent is not None else "Racine du disque"
    return f"""<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Disque USB · {html.escape(relative or 'racine')}</title>
<style>body{{font:16px system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#182230;background:#f7f8fa}}main{{background:white;border:1px solid #dfe4ea;border-radius:14px;padding:1.5rem;box-shadow:0 4px 18px #0000000b}}h1{{margin-top:0}}a{{color:#0757a5}}input{{padding:.6rem;width:min(100%,480px);border:1px solid #bbc5d1;border-radius:8px}}button{{padding:.6rem 1rem;border:0;border-radius:8px;background:#0757a5;color:white}}table{{border-collapse:collapse;width:100%;margin-top:1rem}}td,th{{padding:.7rem;border-bottom:1px solid #e6e9ed;text-align:left}}.note{{background:#fff7df;padding:.8rem;border-radius:8px}}</style>
<main><h1>Consultation du disque USB</h1><p class='note'>Lecture seule · serveur local · aucun fichier n'est modifié.</p>
<form method='get' action='/browse/{quote(relative, safe='/')}'><input name='q' value='{html.escape(query)}' placeholder='Rechercher dans ce dossier'><button>Filtrer</button></form>
<p>{parent_link} · <a href='/'>accueil</a></p><table><tr><th></th><th>Nom</th><th>Type</th><th>Détails</th></tr>{''.join(entries) or '<tr><td colspan=4>Aucun élément</td></tr>'}</table></main>"""


class Handler(BaseHTTPRequestHandler):
    root: Path

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/" or parsed.path.startswith("/browse"):
                requested = parsed.path.removeprefix("/browse").lstrip("/")
                target = safe_path(self.root, requested)
                if not target.is_dir():
                    raise FileNotFoundError
                query = parse_qs(parsed.query).get("q", [""])[0]
                self.send_html(page(self.root, target, query))
                return
            if parsed.path.startswith("/preview/"):
                target = safe_path(self.root, parsed.path.removeprefix("/preview/"))
                if not target.is_file() or target.suffix.lower() not in PREVIEW_TYPES:
                    raise FileNotFoundError
                self.send_file(target, preview=True)
                return
            raise FileNotFoundError
        except (FileNotFoundError, PermissionError, OSError):
            self.send_error(404, "Fichier introuvable ou accès refusé")

    def send_html(self, content: str) -> None:
        data = content.encode("utf-8")
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    def send_file(self, path: Path, preview: bool = False) -> None:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if content_type == "text/plain":
            data = path.read_bytes()[:500_000]
            self.send_html(f"<meta charset='utf-8'><pre>{html.escape(data.decode('utf-8', errors='replace'))}</pre>")
            return
        self.send_response(200); self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(path.stat().st_size)); self.send_header("Content-Disposition", "inline"); self.end_headers()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                self.wfile.write(chunk)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interface graphique locale de consultation en lecture seule")
    parser.add_argument("path", type=Path, help="point de montage à consulter")
    parser.add_argument("--bind", default="127.0.0.1", help="adresse d'écoute, 127.0.0.1 recommandé")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    root = args.path.resolve()
    if not root.is_dir():
        parser.error(f"dossier introuvable : {root}")
    Handler.root = root
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"Consultation de {root}")
    print(f"Serveur local : http://{args.bind}:{args.port}/")
    print("Arrêt : Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
