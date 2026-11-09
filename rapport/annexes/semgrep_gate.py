"""Porte de sécurité SAST : échoue si Semgrep remonte un résultat de sévérité haute.

Usage : python semgrep_gate.py semgrep.json
Sévérités bloquantes : ERROR / HIGH / CRITICAL (configurable via SEMGREP_BLOCKING).
"""
import json
import os
import sys

BLOCKING = {s.strip().upper() for s in os.environ.get("SEMGREP_BLOCKING", "ERROR,HIGH,CRITICAL").split(",")}


def main(path):
    with open(path, encoding="utf-8") as fh:
        results = json.load(fh).get("results", [])

    blocking = [r for r in results if r.get("extra", {}).get("severity", "").upper() in BLOCKING]
    lines = ["## SAST - Semgrep", "", f"Résultats totaux : **{len(results)}** - bloquants : **{len(blocking)}**", ""]
    if results:
        lines += ["| Sévérité | Règle | Fichier:ligne |", "|---|---|---|"]
        for r in results:
            sev = r.get("extra", {}).get("severity", "?")
            lines.append(f"| {sev} | `{r['check_id'].split('.')[-1]}` | `{r['path']}:{r['start']['line']}` |")
    report = "\n".join(lines)
    print(report)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report + "\n")

    if blocking:
        print(f"\n::error::{len(blocking)} vulnérabilité(s) SAST de sévérité haute détectée(s) - pipeline bloqué.")
        return 1
    print("\nAucune vulnérabilité SAST bloquante.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "semgrep.json"))
