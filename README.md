# ledgr_demo

App optionnelle qui génère un dataset de démo réaliste pour LEDGR.

**JAMAIS installer en production.**

## Usage

```bash
# Installer l'app (dev only)
docker exec devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench --site ledgr.localhost install-app ledgr_demo"

# Seed le dataset (wipe préalable des Companies "Fiduciaire Demo SA" et "Mandat Test SARL")
docker exec devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench --site ledgr.localhost seed-demo"

# Wipe sans recréer
docker exec devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench --site ledgr.localhost wipe-demo"
```

## Profils mandats

- **Fiduciaire Demo SA (FID)** — services fiduciaires, ~3 employés, charges récurrentes (Swisscom, loyer, électricité, fournitures), 12 clients
- **Mandat Test SARL** — sera renommée "Boulangerie du Lac SA", commerce alimentaire à Yverdon, ~5 employés, achats fréquents matières premières (Pistor, Migros Pro), TVA mixte 2.6%/8.1%

## Période

12 mois figés : 2025-05-01 → 2026-04-30. Permet 4 trimestres TVA complets et un historique pour Layer 5 (RAG).

## Volume cible

- ~80 Purchase Invoices submitted + 10 drafts par mandat
- ~30-50 Sales Invoices par mandat (selon profil)
- ~12 Journal Entries (paie mensuelle) par mandat
- ~20 Payment Entries (rapprochement) par mandat
- Total : ~250-300 documents
