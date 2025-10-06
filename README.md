# Projet : IPv4 Blackhole

## Code 1 : `false_bannier_all.py`

Ce script Python met en place un serveur "tarpit" multi-protocoles. Son objectif principal est de ralentir considérablement les scanners de ports et les tentatives de connexion automatisées en acceptant les connexions sur des ports spécifiques, en envoyant très lentement de fausses bannières de service, puis en maintenant la connexion ouverte le plus longtemps possible.

**Fonctionnement :**

*   **Serveur Multi-ports :** Le script utilise `asyncio` pour démarrer simultanément plusieurs serveurs, chacun écoutant sur un port défini (21 pour FTP, 22 pour SSH, 23 pour Telnet, 25 pour SMTP, et 80 pour HTTP).
*   **Fausses Bannières :** Pour chaque port, une fausse bannière correspondant au service habituellement associé est définie (par exemple, une bannière ProFTPD pour le port 21).
*   **Envoi Ralenti :** Lorsqu'un client se connecte, le script envoie la bannière correspondante caractère par caractère, avec un délai configurable entre chaque octet. Cette méthode monopolise les ressources du client qui attend une réponse complète, le ralentissant ainsi efficacement.
*   **Maintien de la Connexion :** Après l'envoi de la bannière, le script maintient la connexion ouverte en entrant dans une boucle infinie, forçant le client à rester connecté ou à gérer un grand nombre de connexions ouvertes.
*   **Journalisation :** Toutes les tentatives de connexion, les déconnexions et les erreurs sont enregistrées avec leur adresse IP, le port de destination et l'heure, permettant une surveillance des activités suspectes.

---

## Code 2 : `blackh2 (1).py`

Ce script Python implémente un système de surveillance et de blacklisting automatique des adresses IP basé sur la détection de connexions suspectes. Son objectif principal est d'identifier et de bloquer automatiquement les adresses IP qui effectuent trop de tentatives de connexion dans un laps de temps donné.

## Fonctionnement :

* **Surveillance des Logs :** Le script surveille en temps réel un fichier de log (`/tmp/flask_connections.log`) contenant les connexions. Il utilise un thread dédié pour lire continuellement les nouvelles entrées du fichier.

* **Détection des Tentatives Répétées :** Pour chaque adresse IP, le système maintient un historique horodaté des tentatives de connexion dans une fenêtre de temps glissante (par défaut 60 secondes). Les tentatives trop anciennes sont automatiquement supprimées pour ne garder que les connexions récentes.

* **Blacklisting Automatique :** Si une adresse IP dépasse le nombre maximal de tentatives autorisées (par défaut 3) dans la fenêtre de temps définie, elle est automatiquement ajoutée à la blacklist. Les adresses locales (127.0.0.1, ::1) sont exemptées de cette surveillance.

* **Persistance sur Fichier :** La liste des IPs blacklistées est sauvegardée dans un fichier JSON (`blacklist.json`) pour persister entre les redémarrages du script. Ce fichier contient également la date de dernière mise à jour.

* **Journalisation :** Toutes les actions de blacklisting sont enregistrées dans un fichier de log dédié (`/var/log/auto_blacklist.log`) avec horodatage, permettant un audit des décisions automatiques du système.

* **Monitoring Continu :** Le script affiche périodiquement (toutes les 30 secondes) le nombre total d'IPs blacklistées et un échantillon des adresses bloquées pour permettre un suivi en temps réel de l'activité.

---

## Code 3 : blackholev7.py

Création d'une solution qui a pour bute principale de faire perdre un maximum de temps au attaquants voulant scanner nos ports pour trouver les ports et services ouvert et qui tourne sur notre serveur.

- Objectif : accrocher l'attaquant le plus longtemps possible sur nos ports fermés de façon à ce que son analyse prenne un temps monstre et qu'il ne puisse pas différencier un port ouvert d'un port fermé. Envoyer des entêtes de protocoles par les ports dédiés (non utilsé comme le port 22 ) lorsque ces ports sont scannés. Pour les ports génériques, créer une liste d'entête liée à plusieurs protocoles/services et en envoyer un aléatoirement. Faire en sorte que l'envoi se fasse caractère par caractère de façon de plus en plus lente pour ferrer le poisson, mais qu'il passe quand même un temps monstrueux sur chaque port.

- On a la possibilité de gérer le nombre maximum de communications que l'on garde dans notre Black_Hole simultanément grâce à la constante `MAX_CONNEXIONS`, modifier sa valeur selon la puissance de calcule que vous voulez alouer au script et donc la taille de votre machine.

- On a une gestion du delai d'envoie des caractères des bannières de service. selon le service et le nombre de caractères déjà envoyer la bannière s'envoie plus ou moins vite.

- Dans la fonction `main` on peut gérer les ports sur les quelles ont veut faire tourner le service : exemple :
```python
ports = [22, 21, 25, 80, 110, 995] + list(range(10000, 10010))
```
*cela dit a notre script d'écouter sur les ports 22, 21, 25, 80, 110 et 995 et sur les ports de 10000 à 10010.*

on uilise la bibliotèque `asyncio` pour que l'OS communique a notre script les tentative de connexion sur les ports non utilisé si ils font partie de notre liste.

Le script envoie des logs des connexions en cours. celle qui commence? celle qui se termine et a un compteur du nombre de connexion simultanée.

---

## Code 4 `blackhole.sh`

Script bash pour Linux qui met en place un filtrage réseau strict (“no-pass” par défaut) et une détection anti-scan avec dégradation active du trafic des scanneurs.

- Par défaut: tout trafic est silencieusement DROP (no-response → “filtered”), sauf les ports explicitement autorisés.
- Whitelist par ports TCP/UDP configurables (ex. SSH 22).
- Anti-scan dynamique: si une IP envoie ≥ N SYN en T secondes, elle est ajoutée à un ipset et subit une latence/perte de paquets via `tc netem` sur l’ingress (IFB) et l’egress.
- Chaînes et objets utilisés: `iptables` (BH_INPUT, BH_SCANNER), `ipset` (set “scanners”), `tc` (qdisc prio + netem), IFB (`ifb0` par défaut).

### Prérequis
- Linux avec `iptables`, `ipset`, `iproute2 (tc)`, module noyau `ifb`.
- Droits root (sudo).
- Interface réseau détectable automatiquement ou spécifiée.

### Paramètres clés
- `WHITELIST_TCP` / `WHITELIST_UDP`: ports autorisés (ex: `WHITELIST_TCP=(22)`).
- `ADMIN_ALLOW`: IP/CIDR autorisées à tout contourner (ex: `("192.168.1.10/32")`).
- `IFACE`: interface réseau (auto si vide).
- Anti-scan: `SCANNER_SYNS` (par défaut 10), `SCANNER_WINDOW` (5s), `ATTACK_DELAY_MS` (10000ms), `ATTACK_LOSS_PC` (50%).
- Avancé: `SCANNER_IPSET_NAME` (scanners), `SCANNER_IFB` (ifb0), `BH_MARK_HEX` (0x30).

### Commandes
```bash
# Activer le blackhole strict + anti-scan
sudo ./blackhole.sh apply

# Afficher l’état (iptables/ipset/tc)
sudo ./blackhole.sh status

# Retirer toutes les règles et le shaping
sudo ./blackhole.sh rollback


*(Description du cinquième code à ajouter ici)*
