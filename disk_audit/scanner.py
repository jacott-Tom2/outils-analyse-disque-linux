from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import subprocess
import sys
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PERSONAL = {
    ".jpg": "photo", ".jpeg": "photo", ".png": "photo", ".gif": "photo", ".webp": "photo",
    ".heic": "photo", ".tif": "photo", ".tiff": "photo", ".cr2": "photo", ".nef": "photo",
    ".arw": "photo", ".dng": "photo", ".pdf": "pdf", ".doc": "word", ".docx": "word",
    ".odt": "word", ".rtf": "word", ".xls": "excel", ".xlsx": "excel", ".ods": "excel",
    ".csv": "excel", ".ppt": "powerpoint", ".pptx": "powerpoint", ".odp": "powerpoint",
    ".mp4": "video", ".mov": "video", ".avi": "video", ".mkv": "video", ".mp3": "audio",
    ".wav": "audio", ".zip": "archive", ".7z": "archive", ".rar": "archive", ".tar": "archive",
}
SYSTEM_DIRS = {"windows", "program files", "program files (x86)", "programdata", "system volume information",
               "$recycle.bin", "bin", "boot", "dev", "etc", "lib", "opt", "proc", "root", "sbin", "sys", "usr", "var", "system", "library", "applications", "private"}
SUSPICIOUS = {".exe", ".dll", ".sys", ".msi", ".deb", ".rpm", ".iso", ".img", ".sh", ".bat", ".cmd"}


def classify(relative: str, suffix: str) -> tuple[str, str]:
    parts = {p.lower() for p in Path(relative).parts}
    suffix = suffix.lower()
    if suffix in PERSONAL:
        return PERSONAL[suffix], "personnel probable"
    if parts & SYSTEM_DIRS or suffix in SUSPICIOUS:
        return "systeme_probable", "a verifier"
    return "inconnu", "a verifier"


def run_json(command: list[str]) -> dict:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"available": False, "error": result.stderr.strip() or f"code {result.returncode}"}
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"available": False, "error": str(exc)}


def smart_report(device: str | None) -> dict:
    if not device:
        return {"available": False, "error": "aucun périphérique fourni (--device)"}
    data = run_json(["smartctl", "--json=o", "-a", device])
    data["device"] = device
    return data


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def scan(root: Path, output: Path, device: str | None, no_hash: bool) -> dict:
    root = root.resolve()
    output.mkdir(parents=True, exist_ok=True)
    files, errors, hashes = [], [], defaultdict(list)
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
        for name in names:
            path = Path(current) / name
            rel = str(path.relative_to(root))
            try:
                stat = path.stat(follow_symlinks=False)
                category, status = classify(rel, path.suffix)
                item = {"path": rel, "name": name, "extension": path.suffix.lower(), "category": category,
                        "status": status, "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()}
                if not no_hash and stat.st_size > 0:
                    item["sha256"] = hash_file(path)
                    hashes[(stat.st_size, item["sha256"])].append(rel)
                files.append(item)
            except (OSError, PermissionError) as exc:
                errors.append({"path": rel, "error": str(exc)})
    duplicates = [{"size_bytes": size, "sha256": digest, "paths": paths}
                  for (size, digest), paths in hashes.items() if len(paths) > 1]
    total = sum(item["size_bytes"] for item in files)
    categories = Counter(item["category"] for item in files)
    risks = len(errors) + sum(item["category"] == "systeme_probable" for item in files)
    usage = shutil.disk_usage(root)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "root": str(root),
              "files": files, "errors": errors, "duplicates": duplicates,
              "categories": dict(categories), "total_bytes": total, "risk_count": risks,
              "capacity": {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free},
              "smart": smart_report(device)}
    write_reports(output, report)
    return report


def write_reports(output: Path, report: dict) -> None:
    fields = ["path", "name", "extension", "category", "status", "size_bytes", "modified", "sha256"]
    with (output / "files.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(report["files"])
    with (output / "duplicates.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(["size_bytes", "sha256", "paths"])
        for item in report["duplicates"]: writer.writerow([item["size_bytes"], item["sha256"], " | ".join(item["paths"])])
    tree = Counter(Path(item["path"]).parts[0] if Path(item["path"]).parts else "." for item in report["files"])
    with (output / "tree.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(["top_level", "file_count"]); writer.writerows(tree.items())
    (output / "smart.json").write_text(json.dumps(report["smart"], indent=2, ensure_ascii=False), encoding="utf-8")
    rows = "".join(f"<tr><td>{html.escape(str(k))}</td><td>{v:,}</td></tr>" for k, v in sorted(report["categories"].items()))
    duplicate_rows = "".join(f"<tr><td>{d['size_bytes']:,}</td><td><code>{d['sha256']}</code></td><td>{html.escape(' | '.join(d['paths']))}</td></tr>" for d in report["duplicates"])
    error_rows = "".join(f"<li>{html.escape(e['path'])}: {html.escape(e['error'])}</li>" for e in report["errors"])
    capacity = report["capacity"]
    page = f"""<!doctype html><meta charset='utf-8'><title>Rapport {html.escape(report['root'])}</title>
<style>body{{font:16px sans-serif;max-width:1100px;margin:2em auto}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:.4em;text-align:left}}.risk{{color:#a00}}</style>
<h1>Rapport d'analyse</h1><p><b>Source :</b> {html.escape(report['root'])}</p><p><b>Fichiers :</b> {len(report['files']):,} — <b>Volume :</b> {report['total_bytes']:,} octets — <b>Risque :</b> <span class='risk'>{report['risk_count']}</span></p>
<p><b>Capacité du système de fichiers :</b> {capacity['total_bytes']:,} octets — <b>utilisés :</b> {capacity['used_bytes']:,} — <b>libres :</b> {capacity['free_bytes']:,}</p>
<h2>Catégories</h2><table><tr><th>Catégorie</th><th>Nombre</th></tr>{rows}</table>
<h2>Doublons ({len(report['duplicates'])})</h2><table><tr><th>Taille</th><th>SHA-256</th><th>Fichiers</th></tr>{duplicate_rows}</table>
<h2>Erreurs d'accès ({len(report['errors'])})</h2><ul>{error_rows or '<li>Aucune</li>'}</ul>
<p>Inventaire détaillé : <a href='files.csv'>files.csv</a> · <a href='tree.csv'>tree.csv</a> · <a href='smart.json'>smart.json</a></p>"""
    (output / "summary.html").write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse non destructive d'un disque monté")
    parser.add_argument("path", type=Path, help="point de montage ou dossier à analyser")
    parser.add_argument("-o", "--output", type=Path, default=Path("rapport-disque"))
    parser.add_argument("--device", help="périphérique bloc, ex. /dev/sdb, pour SMART")
    parser.add_argument("--no-hash", action="store_true", help="ne pas calculer les SHA-256")
    args = parser.parse_args()
    if not args.path.is_dir():
        parser.error(f"dossier introuvable : {args.path}")
    report = scan(args.path, args.output, args.device, args.no_hash)
    print(f"Analyse terminée : {len(report['files'])} fichiers, {len(report['duplicates'])} groupes de doublons")
    print(f"Rapport HTML : {args.output / 'summary.html'}")


if __name__ == "__main__":
    main()
