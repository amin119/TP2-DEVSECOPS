"""Porte de sécurité DAST : analyse le rapport JSON d'OWASP ZAP.

Le pipeline échoue si une alerte atteint le niveau de risque ZAP_FAIL_RISK
(3 = High, niveau le plus élevé de ZAP, assimilé à « critique » ; 2 = Medium...).
Usage : python zap_gate.py zap-report.json
"""
import json
import os
import sys

RISK_NAMES = {0: "Informational", 1: "Low", 2: "Medium", 3: "High"}
THRESHOLD = int(os.environ.get("ZAP_FAIL_RISK", "3"))


def main(path):
    with open(path, encoding="utf-8") as fh:
        report = json.load(fh)

    alerts = []
    for site in report.get("site", []):
        for alert in site.get("alerts", []):
            alerts.append({
                "risk": int(alert.get("riskcode", 0)),
                "name": alert.get("alert") or alert.get("name"),
                "id": alert.get("pluginid"),
                "count": len(alert.get("instances", [])) or int(alert.get("count", 0)),
                "url": (alert.get("instances") or [{}])[0].get("uri", ""),
            })
    alerts.sort(key=lambda a: -a["risk"])

    counts = {name: sum(1 for a in alerts if a["risk"] == code) for code, name in RISK_NAMES.items()}
    blocking = [a for a in alerts if a["risk"] >= THRESHOLD]

    lines = [
        "## DAST - OWASP ZAP",
        "",
        "| High | Medium | Low | Info |",
        "|---|---|---|---|",
        f"| {counts['High']} | {counts['Medium']} | {counts['Low']} | {counts['Informational']} |",
        "",
        f"Seuil bloquant : **{RISK_NAMES[THRESHOLD]}** et plus - alertes bloquantes : **{len(blocking)}**",
        "",
    ]
    if alerts:
        lines += ["| Risque | Alerte (ID) | Instances | Exemple d'URL |", "|---|---|---|---|"]
        for a in alerts:
            lines.append(f"| {RISK_NAMES[a['risk']]} | {a['name']} ({a['id']}) | {a['count']} | `{a['url']}` |")
    text = "\n".join(lines)
    print(text)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")

    if blocking:
        print(f"\n::error::{len(blocking)} faille(s) DAST de risque >= {RISK_NAMES[THRESHOLD]} - pipeline bloqué.")
        return 1
    print("\nAucune faille DAST bloquante.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "zap-report.json"))
