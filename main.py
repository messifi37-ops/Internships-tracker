"""
Job Tracker — point d'entrée principal
Lancé toutes les heures par GitHub Actions.
"""
import json
import os
import sys
from datetime import datetime

from scraper import check_site, is_internship
from notifier import send_notification
from sites import SITES, INTERNSHIP_KEYWORDS

KNOWN_JOBS_FILE = "known_jobs.json"


# ─── Persistence ──────────────────────────────────────────────────────────────

def load_state() -> dict:
    if os.path.exists(KNOWN_JOBS_FILE):
        with open(KNOWN_JOBS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_state(state: dict) -> None:
    with open(KNOWN_JOBS_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    state    = load_state()
    findings = []
    errors   = []
    now      = datetime.utcnow().isoformat()

    print(f"\n🔍 Job Tracker — {now}")
    print(f"   {len(SITES)} sites à vérifier\n")

    for company, url in SITES.items():
        result = check_site(company, url)

        if result["error"]:
            print(f"    ⚠️  Erreur : {result['error']}")
            errors.append({"company": company, "error": result["error"]})
            continue

        prev   = state.get(company, {})
        is_new = company not in state   # True = première fois qu'on check ce site

        # ── Workday : on compare les IDs d'offres ──────────────────────────
        if result["platform"] == "workday":
            all_jobs     = result["jobs"]
            # Filtre stages/alternances si des keywords sont définis
            filtered_jobs = [
                j for j in all_jobs
                if is_internship(j["title"], INTERNSHIP_KEYWORDS)
            ]
            current_ids  = {j["id"] for j in filtered_jobs}
            previous_ids = set(prev.get("job_ids", []))
            new_ids      = current_ids - previous_ids

            if not is_new and new_ids:
                new_jobs = [j for j in filtered_jobs if j["id"] in new_ids]
                findings.append({"company": company, "url": url, "new_jobs": new_jobs})
                print(f"    🆕 {len(new_jobs)} nouvelle(s) offre(s) !")

            # Mise à jour de l'état (on sauve TOUS les IDs filtrés)
            state[company] = {
                "platform":     "workday",
                "job_ids":      list(current_ids),
                "last_checked": now,
            }

        # ── Autres plateformes : on compare le hash ────────────────────────
        else:
            current_hash  = result["hash"]
            previous_hash = prev.get("hash")

            if not is_new and current_hash and current_hash != previous_hash:
                findings.append({"company": company, "url": url, "new_jobs": None})
                print(f"    🆕 Changement détecté sur la page !")

            state[company] = {
                "platform":     result["platform"],
                "hash":         current_hash,
                "last_checked": now,
            }

    # ── Notifications ─────────────────────────────────────────────────────────
    print(f"\n📊 Résumé : {len(findings)} nouveauté(s), {len(errors)} erreur(s)")

    if findings:
        print("📧 Envoi de la notification...")
        send_notification(findings)
    else:
        print("😴 Aucune nouveauté — pas d'email.")

    # ── Sauvegarde ────────────────────────────────────────────────────────────
    save_state(state)
    print("💾 État sauvegardé.\n")


if __name__ == "__main__":
    main()
