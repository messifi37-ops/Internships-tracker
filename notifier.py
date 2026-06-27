import os
import requests
from datetime import datetime

RESEND_API_KEY     = os.environ.get("RESEND_API_KEY", "")
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL", "messifi37@outlook.com")


def send_notification(findings: list) -> None:
    """
    findings = [
        {
          "company": "Nomura",
          "url": "https://...",
          "new_jobs": [{"title": "...", "url": "...", "location": "..."}],  # Workday
          # OR
          "new_jobs": None,  # Generic — we know the page changed but not the exact jobs
        },
        ...
    ]
    """
    if not RESEND_API_KEY:
        print("⚠️  RESEND_API_KEY manquante — email non envoyé.")
        return

    count = len(findings)
    subject = f"🚨 {count} entreprise(s) avec de nouvelles offres !"
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:auto;">
      <h2 style="color:#1a1a1a;">🚨 Nouvelles offres détectées</h2>
      <p style="color:#555;">Détecté le <strong>{now}</strong> — {count} entreprise(s) concernée(s)</p>
      <hr style="border:none;border-top:1px solid #eee;margin:16px 0;">
    """

    for f in findings:
        company   = f["company"]
        url       = f["url"]
        new_jobs  = f.get("new_jobs")

        html += f'<h3 style="margin-bottom:4px;">🏦 {company}</h3>'

        if new_jobs:
            html += "<ul style='margin-top:4px;'>"
            for job in new_jobs:
                job_url  = job.get("url", url)
                title    = job.get("title", "Offre sans titre")
                location = job.get("location", "")
                loc_str  = f" — {location}" if location else ""
                html += (
                    f'<li style="margin-bottom:6px;">'
                    f'<a href="{job_url}" style="color:#0057e7;font-weight:bold;">{title}</a>'
                    f'<span style="color:#888;">{loc_str}</span>'
                    f'</li>'
                )
            html += "</ul>"
        else:
            html += (
                f'<p style="color:#555;">⚠️ Changement détecté sur la page carrière. '
                f'<a href="{url}" style="color:#0057e7;">Voir les offres →</a></p>'
            )

        html += '<hr style="border:none;border-top:1px solid #eee;margin:12px 0;">'

    html += """
      <p style="color:#aaa;font-size:12px;">Envoyé par ton Job Tracker GitHub Actions</p>
    </div>
    """

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from":    "Job Tracker <onboarding@resend.dev>",
            "to":      [NOTIFICATION_EMAIL],
            "subject": subject,
            "html":    html,
        },
        timeout=15,
    )

    if resp.status_code in (200, 201):
        print(f"✅ Email envoyé à {NOTIFICATION_EMAIL}")
    else:
        print(f"❌ Erreur Resend {resp.status_code} : {resp.text}")
