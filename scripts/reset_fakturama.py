"""Reset Fakturama's master data by soft-deleting it (keeping the defaults).

Fakturama stores its data in an HSQLDB file database and soft-deletes records
by setting a ``DELETED`` boolean. To time a "fresh" run of the pipeline we only
need the master data (products, contacts/addresses, payment methods) gone, while
the seeded defaults (VAT rates, categories, ...) must stay.

This script stops Fakturama, rewrites the active master-data rows to
``DELETED=TRUE`` in the HSQLDB ``.script`` file, and restarts Fakturama. It does
not touch the documents (orders/invoices) or the default tables.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

DB_SCRIPT = Path(r"C:\Fakturama\Database\Database.script")
FAKTURAMA_EXE = r"C:\Program Files\Fakturama2\Fakturama.exe"

# INSERT statement prefix (with the exact quoting HSQLDB uses) -> 1-based index
# of the DELETED boolean column.
MASTER_TABLES = {
    'INSERT INTO "FKT_PRODUCT" VALUES(': 12,
    'INSERT INTO FKT_CONTACT VALUES(': 7,
    'INSERT INTO FKT_ADDRESS VALUES(': 8,
    'INSERT INTO "FKT_PAYMENT" VALUES(': 4,
}


def _split_values(body: str) -> list[str]:
    """Split a HSQLDB VALUES body on commas, respecting single-quoted strings."""
    parts: list[str] = []
    cur: list[str] = []
    in_str = False
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if in_str:
            if ch == "'":
                if i + 1 < n and body[i + 1] == "'":
                    cur.append("''")
                    i += 2
                    continue
                in_str = False
                cur.append("'")
            else:
                cur.append(ch)
        elif ch == "'":
            in_str = True
            cur.append("'")
        elif ch == ",":
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return parts


def _soft_delete_line(line: str) -> str:
    for prefix, del_col in MASTER_TABLES.items():
        if not line.lstrip().startswith(prefix):
            continue
        start = line.index("VALUES(") + len("VALUES(")
        stripped = line.rstrip("\r\n")
        end = stripped.rfind(")")
        if end <= start:
            return line
        parts = _split_values(line[start:end])
        if len(parts) >= del_col:
            parts[del_col - 1] = "TRUE"
        return line[:start] + ",".join(parts) + line[end:]
    return line


def _kill() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "Fakturama.exe"], capture_output=True)
    time.sleep(2)


def _start() -> None:
    subprocess.Popen([FAKTURAMA_EXE])


def reset(wait: float = 15.0) -> None:
    _kill()
    if not DB_SCRIPT.exists():
        _start()
        time.sleep(wait)
        return
    text = DB_SCRIPT.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    changed = 0
    for idx, line in enumerate(lines):
        new = _soft_delete_line(line)
        if new != line:
            changed += 1
            lines[idx] = new
    DB_SCRIPT.write_text("".join(lines), encoding="utf-8")
    print(f"soft-deleted {changed} master-data rows")
    _start()
    time.sleep(wait)


def main(argv: list[str]) -> int:
    wait = float(argv[1]) if len(argv) > 1 else 15.0
    reset(wait)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
