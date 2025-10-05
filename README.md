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

## Code 3

*(Description du troisième code à ajouter ici)*

---

## Code 4

*(Description du quatrième code à ajouter ici)*
