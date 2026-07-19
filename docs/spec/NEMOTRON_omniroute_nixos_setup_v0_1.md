# Instructions Nemotron — Mise en place d'OmniRoute et configuration des free tiers (NixOS)

*Document destiné à un agent de code (Nemotron sur OpenCode). Le cadrage est fixé ici — l'agent exécute, vérifie, loggue. Il ne prend aucune décision de périmètre : voir §0. Chaque tâche a un critère d'acceptation vérifiable. En cas d'écart entre ce document et la réalité du dépôt OmniRoute (les quotas et commandes des free tiers changent vite), l'agent documente l'écart dans `SETUP_LOG.md` et applique la documentation officielle du dépôt — jamais une supposition.*

> **Version 0.1** · Cible : NixOS (dernière stable) · Projet : banc d'essai ETAU/SECS v0.2 + outillage de dev
> **Référence amont** : `ETAU_SECS_banc_essai_multisprint_v0_2.md`, décision D2 (§6)

---

## 0. Périmètre — à lire avant toute commande

OmniRoute est installé ici pour **deux usages distincts, à ne jamais confondre** :

| Usage | Autorisé | Configuration |
|---|---|---|
| **U1 — Outillage de dev** : Nemotron/OpenCode et autres agents de code routés vers les free tiers, avec fallback et compression | Oui, c'est l'usage principal | Combo `dev-auto` (§5.1) |
| **U2 — Chemin expérimental du banc d'essai** : les appels des pipelines P0-P4 | **Par défaut : NON.** La décision D2 du banc (critère 4) impose l'API directe, sans gateway intermédiaire. Si l'arbitre final décide malgré tout de router l'expérience via OmniRoute, seul le profil verrouillé `banc-essai-pinned` (§5.2) est admissible — et l'écart à D2 doit être consigné dans `ANALYSIS_PROTOCOL.md` du banc | Combo `banc-essai-pinned` (§5.2), sinon rien |

Raison du verrou U2, non négociable : le banc d'essai est un instrument de mesure. L'auto-fallback (changement silencieux de modèle) détruit l'attribution des résultats à une architecture ; la compression (RTK/Caveman) réécrit les prompts en transit, ce qui invalide l'isolation contrôlée du §2bis du banc. Un gateway est un confort pour coder, un facteur confondant pour mesurer.

**Ce que Nemotron ne fait pas** : créer des comptes chez les fournisseurs (action humaine, §3) ; committer une clé API où que ce soit ; modifier les documents du banc d'essai ; activer un provider dont les conditions d'utilisation sont signalées "ToS-flagged" par le dashboard OmniRoute sans validation humaine explicite.

---

## 1. Spécificités NixOS — contraintes d'installation

NixOS n'a pas de `/usr/bin` mutable ni de `npm install -g` fonctionnel hors environnement. Trois voies d'installation, **dans cet ordre de préférence** :

### Voie A — Flake du dépôt (préférée : reproductible, déclarative)

Le dépôt OmniRoute contient un `flake.nix`. Vérifier qu'il expose un package ou une devShell, puis :

```bash
# Cloner et inspecter ce que le flake expose réellement
git clone https://github.com/diegosouzapw/OmniRoute.git ~/tools/omniroute
cd ~/tools/omniroute
nix flake show 2>&1 | tee -a ~/projets/banc-essai/SETUP_LOG.md

# Si un package/app est exposé :
nix run .#<nom-app>            # d'après la sortie de flake show
# Sinon, devShell + lancement npm classique DANS le shell :
nix develop
npm ci && npm run build && npm start
```

Si `flake.nix` ne construit pas proprement (dépendances natives non packagées, etc.), **ne pas patcher le flake** — consigner l'échec dans `SETUP_LOG.md` et passer à la voie B.

### Voie B — Shell Nix éphémère + npx (rapide, non déclarative)

```bash
nix-shell -p nodejs_22 --run "npx -y omniroute"
```

Pour un usage récurrent, créer un `shell.nix` dans le dossier projet :

```nix
# ~/projets/banc-essai/tooling/shell.nix
{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.nodejs_22 ];
  shellHook = ''
    echo "OmniRoute : lancer avec  npx -y omniroute"
    echo "Dashboard : http://localhost:20128"
  '';
}
```

Attention : vérifier la version de Node exigée par le dépôt (`.node-version` / `.nvmrc` à la racine) et aligner `nodejs_XX` en conséquence.

### Voie C — Conteneur (isolation maximale, si Docker/Podman déjà activé)

Prérequis déclaratif dans `configuration.nix` (action humaine si absent — Nemotron le signale, ne l'applique pas lui-même sans accord) :

```nix
virtualisation.podman.enable = true;   # ou virtualisation.docker.enable = true;
virtualisation.podman.dockerCompat = true;
```

Puis :

```bash
podman run -d --name omniroute \
  -p 127.0.0.1:20128:20128 \
  -v ~/tools/omniroute-data:/data \
  --env-file ~/projets/banc-essai/tooling/.env.omniroute \
  docker.io/diegosouzapw/omniroute:latest
```

Le dépôt contient aussi `contrib/podman/` — s'il fournit un compose ou des unités, les préférer à la commande ci-dessus et consigner ce qui a été utilisé.

**Règle commune aux trois voies** : bind sur `127.0.0.1` uniquement. Jamais `0.0.0.0` — le gateway détient les clés.

### Tâche 1 — Installation
Choisir la voie A ; replier sur B puis C en cas d'échec, chaque repli documenté.
**Critère d'acceptation** : `curl -s http://127.0.0.1:20128/v1/models` répond (même avec une liste vide) ; la voie retenue, la version de Node et la version d'OmniRoute sont consignées dans `SETUP_LOG.md`.

---

## 2. Secrets — règle NixOS impérative

Aucune clé API dans : `configuration.nix`, un flake, un fichier committé, le store Nix (tout ce qui passe par un fichier .nix lu par le daemon finit en clair dans `/nix/store`, lisible par tous les utilisateurs).

Emplacement imposé : `~/projets/banc-essai/tooling/.env.omniroute`, mode `600`, listé dans `.gitignore` avant d'écrire la moindre clé dedans.

```bash
install -m 600 /dev/null ~/projets/banc-essai/tooling/.env.omniroute
grep -qxF '.env.omniroute' ~/projets/banc-essai/.gitignore || \
  echo 'tooling/.env.omniroute' >> ~/projets/banc-essai/.gitignore
```

Gabarit du fichier (les valeurs seront remplies par l'humain, §3) :

```bash
# .env.omniroute — clés free tiers. NE JAMAIS COMMITTER.
GEMINI_API_KEY=
GROQ_API_KEY=
CEREBRAS_API_KEY=
MISTRAL_API_KEY=
NVIDIA_API_KEY=
# Clé d'accès locale au gateway lui-même (générer : openssl rand -hex 24)
OMNIROUTE_API_KEY=
```

Si le projet adopte plus tard une gestion déclarative des secrets (sops-nix, agenix), la migration se fait par l'humain ; Nemotron n'introduit pas cette machinerie de sa propre initiative.

### Tâche 2 — Secrets
**Critère d'acceptation** : le fichier existe en mode 600, est gitignoré (vérifié par `git check-ignore`), `OMNIROUTE_API_KEY` est généré et renseigné ; aucune clé n'apparaît dans `git log -p` ni dans un fichier du store (`grep -r` de contrôle sur le repo).

---

## 3. Comptes free tiers — actions humaines, checklist à remettre

Nemotron **prépare la checklist et s'arrête** : la création de comptes et l'acceptation de conditions d'utilisation sont des actes humains. Produire `FREE_TIERS_CHECKLIST.md` avec, pour chaque fournisseur : l'URL de la console, la clé attendue dans `.env.omniroute`, et une colonne "quota constaté à la date de création" que l'humain remplit — **ne pas pré-remplir les quotas de mémoire, ils changent**.

| Fournisseur | Console | Variable | Rôle prévu |
|---|---|---|---|
| Google AI Studio (Gemini) | aistudio.google.com | `GEMINI_API_KEY` | Candidat D2 principal (grande fenêtre de contexte) |
| Groq | console.groq.com | `GROQ_API_KEY` | Candidat D2 / second modèle Cycle C (famille Llama, entraînement éloigné) |
| Cerebras | cloud.cerebras.ai | `CEREBRAS_API_KEY` | Volume quotidien confortable, fallback dev |
| Mistral La Plateforme | console.mistral.ai | `MISTRAL_API_KEY` | Troisième famille d'entraînement (utile ETAU natif, hors banc) |
| NVIDIA NIM | build.nvidia.com | `NVIDIA_API_KEY` | Réserve dev, catalogue large |

Note à inscrire en tête de la checklist, reprise de D2 : les free tiers peuvent impliquer que les données envoyées servent à l'entraînement du fournisseur. Acceptable pour un corpus anonymisé destiné à un dépôt versionné (décision D1 du banc) ; à re-vérifier si D1 change.

### Tâche 3 — Checklist
**Critère d'acceptation** : `FREE_TIERS_CHECKLIST.md` existe ; exécution en pause jusqu'à ce que l'humain confirme que `.env.omniroute` est rempli. Reprise sur confirmation explicite uniquement.

---

## 4. Connexion des providers dans OmniRoute

Une fois les clés en place, connecter chaque provider. Deux chemins selon ce que la version installée expose (vérifier `omniroute --help` et la doc du dépôt) :

- **CLI** : commandes de la famille `omniroute keys` / `omniroute providers` si disponibles ;
- **Dashboard** : `http://127.0.0.1:20128` → ajout de providers par clé API. Consulter `/dashboard/free-tiers` pour l'état des quotas.

Règles :
1. Connecter **uniquement** les cinq providers de §3 — pas les providers "session-cookie", "web", ou reverse-engineerés du catalogue, et rien de ce que le dashboard marque ToS-flagged, sans validation humaine.
2. Désactiver la télémétrie si un toggle existe (le README annonce zéro télémétrie par défaut — vérifier, consigner).
3. Mémoire OmniRoute : **off** (c'est le défaut annoncé — vérifier, consigner).

### Tâche 4 — Providers
**Critère d'acceptation** : `curl -s -H "Authorization: Bearer $OMNIROUTE_API_KEY" http://127.0.0.1:20128/v1/models` liste au moins un modèle par provider connecté ; capture de la sortie dans `SETUP_LOG.md`.

---

## 5. Les deux combos — dev vs banc d'essai

### 5.1 Combo `dev-auto` (usage U1 — Nemotron, OpenCode, agents de code)

Objectif : ne jamais s'arrêter de coder, coût zéro. Configuration via dashboard ou CLI :

- Stratégie : `auto` (ou `auto/coding` si disponible) sur les cinq providers connectés.
- Fallback : actif (c'est le but).
- Compression : au choix de l'humain ; préréglage `Lite` recommandé par défaut — jamais plus agressif que `Standard` pour du travail de code, afin de ne pas dégrader les prompts d'agent.

### 5.2 Combo `banc-essai-pinned` (usage U2 — seulement si l'arbitre final déroge à D2)

Profil verrouillé, chaque point est bloquant :

- **Un seul target** : le modèle exact choisi en D2 (provider + identifiant de modèle figés). Stratégie `priority` avec une liste d'un seul élément.
- **Fallback : désactivé.** Un échec doit être un échec visible du run, jamais une bascule silencieuse de modèle. Si OmniRoute ne permet pas de désactiver totalement le fallback sur un combo, **ce combo ne doit pas être créé** et U2 est abandonné — retour à l'API directe.
- **Compression : off, totalement.** Aucun engine actif sur ce combo. Si la version installée le permet, forcer aussi côté client l'en-tête par requête `x-omniroute-compression: off` (vérifier le nom exact dans la doc compression du dépôt) dans le code du banc — double verrou.
- **Mémoire, guardrails de réécriture, tout middleware modifiant le contenu : off.**
- **Vérification d'identité de modèle** : le code du banc loggue, pour chaque réponse, le champ `model` retourné par l'API et tout en-tête `X-OmniRoute-*` pertinent ; un test automatisé échoue si un seul appel d'un cycle rapporte un modèle différent de celui de D2.

### Tâche 5 — Combos
**Critère d'acceptation 5.1** : une requête chat de test sur `dev-auto` répond ; couper artificiellement le provider prioritaire (clé invalide temporaire) fait basculer sur le suivant — testé et consigné.
**Critère d'acceptation 5.2** *(seulement si U2 activé par l'humain)* : 10 appels consécutifs sur `banc-essai-pinned` retournent 10 fois le même identifiant de modèle ; un diff entre le prompt envoyé par le client et le prompt reçu par le provider (logs OmniRoute) est vide — preuve que la compression est réellement inactive, pas seulement décochée.

---

## 6. Intégration OpenCode (Nemotron)

Le dépôt fournit une intégration OpenCode : soit la commande de setup dédiée (famille `omniroute setup-*` — chercher `setup-opencode` ou équivalent dans `omniroute --help`), soit le plugin npm `@omniroute/opencode-provider`. Préférer la commande de setup si elle existe ; sinon le plugin ; en dernier recours, configuration manuelle d'OpenCode vers un endpoint OpenAI-compatible :

- Base URL : `http://127.0.0.1:20128/v1`
- API key : la valeur de `OMNIROUTE_API_KEY`
- Modèle : `auto` (le combo `dev-auto` fait le reste)

Sur NixOS, si OpenCode est lui-même lancé via nix, s'assurer que la configuration OpenCode (fichier de config utilisateur, pas le store) porte l'endpoint — même règle secrets qu'en §2.

### Tâche 6 — OpenCode
**Critère d'acceptation** : depuis une session OpenCode/Nemotron, une génération de code aboutit via le gateway ; le dashboard OmniRoute montre la requête et le provider qui l'a servie ; consigné dans `SETUP_LOG.md`.

---

## 7. Smoke test D2 — exigé par le banc d'essai v0.2 avant de figer D2

Indépendamment du chemin retenu (API directe recommandée, ou `banc-essai-pinned` par dérogation), exécuter le smoke test prévu par D2 pour chaque modèle candidat (au minimum : Gemini, Groq) :

```
5 appels par candidat, séquentiels, prompt fixe demandant une liste
d'assertions au format JSON strict avec champ source_ref
{session_id, tour_n}, sur un extrait de corpus factice de ~2 pages.
```

Mesurer et consigner dans `SMOKE_TEST_D2.md` : taux de JSON valide (5/5 attendu), latence par appel, tout throttling rencontré, identifiant de modèle exact retourné. Ce fichier est l'entrant de la décision D2 — il est remis à l'arbitre final, Nemotron ne choisit pas le modèle.

### Tâche 7 — Smoke test
**Critère d'acceptation** : `SMOKE_TEST_D2.md` existe avec les mesures pour ≥2 candidats ; aucun candidat n'est déclaré "retenu" dans le document — seulement les chiffres.

---

## 8. Livrables et ordre d'exécution

```
tooling/
├── SETUP_LOG.md               # journal horodaté de chaque tâche, écarts inclus
├── FREE_TIERS_CHECKLIST.md    # §3 — rempli par l'humain
├── SMOKE_TEST_D2.md           # §7 — entrant de la décision D2
├── shell.nix                  # si voie B retenue
└── .env.omniroute             # mode 600, gitignoré, jamais committé
```

Ordre strict : Tâche 1 → 2 → 3 **(pause humaine)** → 4 → 5 → 6 → 7. Toute tâche dont le critère d'acceptation échoue bloque la suivante ; l'échec est consigné, pas contourné.

---

## 9. Ce que cette installation ne décide pas

Elle ne décide pas D2 (le modèle du banc — décision humaine sur la base de `SMOKE_TEST_D2.md`). Elle ne lève pas le critère "API directe" du banc d'essai — la dérogation U2, si elle a lieu, est un acte de l'arbitre final, tracé dans `ANALYSIS_PROTOCOL.md`. Elle ne touche pas à AGORA, qui se termine dans ses conditions définies (Anthropic + DeepSeek directs). Elle n'installe aucun provider dont l'accès repose sur des sessions web ou des mécanismes contournant les conditions d'utilisation des fournisseurs.

---

*Document v0.1 — instructions autonomes pour exécution agentique sur NixOS. Les commandes marquées "vérifier" reflètent un dépôt qui évolue vite : la documentation du dépôt OmniRoute fait foi sur la syntaxe exacte, ce document fait foi sur le périmètre et les verrous.*
