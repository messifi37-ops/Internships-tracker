# 🔍 Job Tracker — Alertes offres de stage en temps réel

Surveille automatiquement **56 sites carrières** de banques et boutiques M&A,
et t'envoie un email dès qu'une nouvelle offre apparaît.

Tourne toutes les heures via **GitHub Actions** — 100 % gratuit.

---

## ⚙️ Installation (5 étapes)

### 1. Crée le repo GitHub
- Nouveau repo public nommé `job-tracker`
- Coche "Add a README file"

### 2. Upload les fichiers
Dépose tous ces fichiers dans le repo :
```
job-tracker/
├── .github/workflows/job-tracker.yml
├── main.py
├── scraper.py
├── notifier.py
├── sites.py
├── known_jobs.json
└── requirements.txt
```

### 3. Crée un compte Resend
- Va sur [resend.com](https://resend.com) → Sign up gratuit
- **API Keys** → **Create API Key** → copie la clé

### 4. Configure les secrets GitHub
Dans ton repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Nom | Valeur |
|-----|--------|
| `RESEND_API_KEY` | Ta clé Resend (ex: `re_abc123...`) |
| `NOTIFICATION_EMAIL` | `messifi37@outlook.com` |

### 5. Lance un premier test
- Onglet **Actions** → **Job Tracker** → **Run workflow**
- Regarde les logs — si tout est vert, c'est bon !

> ⚠️ **Le premier run ne t'envoie pas d'email** — il initialise juste la base de référence.
> Dès le 2ème run, toute nouvelle offre déclenche une notification.

---

## 📧 Format des emails

- **Sites Workday** (Nomura, Houlihan Lokey, etc.) : titre exact du poste + lien direct
- **Autres sites** : alerte "changement détecté" + lien vers la page carrière

---

## ➕ Ajouter un site

Dans `sites.py`, ajoute une ligne dans le dictionnaire `SITES` :

```python
"Nom Entreprise": "https://entreprise.com/careers",
```

---

## 🔧 Modifier la fréquence

Dans `.github/workflows/job-tracker.yml`, modifie le cron :
- Toutes les heures : `"0 * * * *"`
- Toutes les 30 min : `"*/30 * * * *"`
- 3 fois par jour : `"0 8,12,18 * * *"`
