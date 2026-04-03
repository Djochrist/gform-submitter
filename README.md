# gform-submitter

Un outil en ligne de commande léger et autonome permettant de soumettre en masse des Google Forms pré-remplis. Aucune configuration complexe : il suffit de modifier un seul fichier TOML. Fonctionne sur n’importe quelle machine avec une seule commande.

---

## Fonctionnalités

* **Aucune friction à l’installation** — `uv` gère automatiquement Python et toutes les dépendances
* **Entièrement configurable** — modifiez un seul fichier pour ajouter autant de formulaires que nécessaire avec des nombres d’envois personnalisés
* **Anti-détection** — délais aléatoires entre les envois, rotation des User-Agents de navigateur, pauses longues périodiques
* **Compatible avec tout Google Form** — fonctionne avec n’importe quel lien de formulaire pré-rempli, sans modification du code
* **Sortie claire** — affichage en temps réel de la progression et tableau récapitulatif final
* **Multi-plateforme** — fonctionne sous Windows, macOS et Linux

---

## Prérequis

* [uv](https://docs.astral.sh/uv/) (installe automatiquement Python et les dépendances)

Pas besoin d’installer Python séparément — `uv` s’occupe de tout.

---

## Installation

**1. Installer uv** (ignorer si déjà installé)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc   # ou redémarrez votre terminal

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Clonez ce repo**

**3. Ouvrir un terminal dans le dossier**

```bash
cd gform-submitter
```

---

## Configuration

Ouvrez `config.toml` dans n’importe quel éditeur de texte.

### Ajouter vos formulaires

Remplacez les URLs d’exemple par vos liens réels de Google Forms pré-remplis :

```toml
[[forms]]
url   = "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform?usp=pp_url&entry.123=your+answer"
count = 100
label = "Groupe A — Femme"

[[forms]]
url   = "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform?usp=pp_url&entry.123=other+answer"
count = 80
label = "Groupe B — Homme"
```

Ajoutez autant de blocs `[[forms]]` que nécessaire. Chaque formulaire est soumis indépendamment, dans l’ordre.

### Comment obtenir un lien pré-rempli

1. Ouvrez votre Google Form
2. Cliquez sur le **menu ⋮** (en haut à droite) → **"Obtenir le lien pré-rempli"**
3. Remplissez les réponses souhaitées
4. Cliquez sur **"Obtenir le lien"** et copiez l’URL
5. Collez-la dans la valeur `url` du fichier `config.toml`

### Paramètres de timing

Ajustez les durées de pause (en secondes) pour contrôler la vitesse d’envoi :

```toml
[settings]
min_pause           = 2.0   # Pause minimale entre les envois
max_pause           = 5.0   # Pause maximale entre les envois
long_pause_every    = 15    # Pause longue toutes les N soumissions
long_pause_min      = 10.0  # Pause longue minimale
long_pause_max      = 20.0  # Pause longue maximale
pause_between_forms = 15.0  # Pause entre deux formulaires différents
```

Pauses plus courtes = exécution plus rapide.
Pauses plus longues = moins de risque de limitation par Google.

---

## Utilisation

```bash
uv run main.py
```

Lors du premier lancement, `uv` télécharge automatiquement la bonne version de Python et installe toutes les dépendances dans un environnement isolé. Aucune installation manuelle requise.

### Exemple de sortie

```
────────────────── Envoi massif de Google Forms ──────────────────

  Formulaires à traiter : 2
  • Groupe A — Femme — 100 soumissions
  • Groupe B — Homme —  80 soumissions

───────────────────── Groupe A — Femme ─────────────────────────
  ID du formulaire : 1FAIpQLSc...
  Champs           : 34 détectés
  Objectif         : 100 soumissions

  ✓ [1/100] Groupe A — Femme
  ✓ [2/100] Groupe A — Femme
  ...
  ⏸  Pause longue 12.4s après 15 soumissions...
  ...
  ✓ [100/100] Groupe A — Femme

  Résultat : 100 OK  0 échec

  Pause de 15.0s avant le prochain formulaire...

───────────────────── Groupe B — Homme ─────────────────────────
  ...
  Résultat : 80 OK  0 échec

──────────────────────── Résumé final ─────────────────────────

  Total des soumissions   180
  Réussies                180
  Échouées                0
  Temps total             18m 42s
```

---

## Structure du projet

```
gform-submitter/
├── main.py          # Script principal — pas besoin de modifier
├── config.toml      # Votre configuration (formulaires, quantités, timing)
├── pyproject.toml   # Métadonnées du projet Python (gérées par uv)
└── README.md        # Ce fichier
```

---

## Notes

* Google Forms ne nécessite pas d’authentification pour soumettre des réponses — les liens pré-remplis fonctionnent directement
* Envoyer un grand volume en peu de temps peut déclencher des limitations ; les paramètres par défaut sont conçus pour réduire ce risque
* Les réponses apparaîtront dans le Google Sheets lié au fur et à mesure
* Si certaines soumissions échouent, elles seront comptabilisées dans le résumé final ; vous pouvez relancer le script pour compléter les envois manquants

---

## ⚠️ Avertissement

Cet outil est destiné uniquement à des fins **éducatives, de test et d’usage personnel**.

En utilisant ce logiciel, vous acceptez les conditions suivantes :

* Vous l’utiliserez **uniquement sur des formulaires dont vous êtes propriétaire ou pour lesquels vous avez une autorisation explicite**
* Vous ne l’utiliserez **pas pour manipuler des sondages, votes ou données publiques**
* Vous ne l’utiliserez **pas à des fins de fraude, d’abus ou d’activités contraires aux lois en vigueur**
* Vous comprenez que les soumissions automatisées peuvent enfreindre les **conditions d’utilisation de Google**

L’auteur décline toute responsabilité en cas de mauvaise utilisation, de dommages ou de conséquences liés à l’usage de cet outil.

Utilisez cet outil de manière responsable.

