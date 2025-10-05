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

## Code 2

*(Description du deuxième code à ajouter ici)*

---

## Code 3

*(Description du troisième code à ajouter ici)*

---

## Code 4

*(Description du quatrième code à ajouter ici)*
