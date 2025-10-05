import asyncio
import logging

# Dictionnaire contenant les ports, les noms de service et leurs fausses bannières.
TARGET_SERVICES = {
    21: {
        "name": "FTP",
        "banner": b"220 ProFTPD 1.3.5a Server (Debian) [::ffff:127.0.0.1]\r\n"
    },
    22: {
        "name": "SSH",
        "banner": b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1\r\n"
    },
    23: {
        "name": "Telnet",
        "banner": b"\xff\xfd\x01\xff\xfd\x1f\xff\xfb\x01\xff\xfb\x03"
    },
    25: {
        "name": "SMTP",
        "banner": b"220 mail.example.com ESMTP Postfix\r\n"
    },
    80: {
        "name": "HTTP",
        "banner": b"HTTP/1.1 200 OK\r\nServer: Apache/2.4.52 (Ubuntu)\r\n" # Ne jamais envoyer les deux '\r\n' finaux
    },
}

DELAY = 5  
LISTEN_IP = "0.0.0.0"

def setup_logging():
    #logger 
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

async def handler(reader, writer):
    
    # Handler universel qui envoie une bannière lentement en fonction du port.
    
    peer_info = writer.get_extra_info("peername")
    server_port = writer.get_extra_info('sockname')[1]
    service = TARGET_SERVICES.get(server_port, {"name": "Unknown", "banner": b""})

    logging.info(f"[+] Connexion de {peer_info} sur le port {server_port} (Faux service {service['name']})")

    try:
        # Envoyer la bannière caractère par caractère en fonction du delay
        for char_code in service['banner']:
            writer.write(bytes([char_code]))
            await writer.drain()
            await asyncio.sleep(DELAY)

        # maintient de la connexion ouverte
        while True:
            await asyncio.sleep(3600)

    except (ConnectionResetError, asyncio.CancelledError, BrokenPipeError):
        logging.info(f"[-] Déconnexion de {peer_info} du port {server_port}")
    except Exception as e:
        logging.error(f"[!] Erreur sur le port {server_port} avec {peer_info}: {e}")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

async def main():
    setup_logging()
    logging.info("Démarrage du Tarpit multi-protocoles...")

    server_tasks = []
    for port, service in TARGET_SERVICES.items():
        try:
            # Crée un serveur asyncio pour chaque port
            server = await asyncio.start_server(handler, LISTEN_IP, port)
            server_tasks.append(server.serve_forever())
            logging.info(f"[*] Faux service {service['name']} en écoute sur le port {port}")
        except OSError as e:
            # Gère les erreurs si le port est déjà utilisé ou si les permissions sont insuffisantes
            logging.critical(f"[!] Impossible de démarrer le serveur sur le port {port}: {e}")
            logging.critical("    -> Avez-vous les permissions nécessaires (sudo) pour les ports < 1024 ?")

    if not server_tasks:
        logging.critical("Aucun serveur n'a pu être démarré. Arrêt du script.")
        return

    # Maintient tous les serveurs en fonctionnement indéfiniment
    await asyncio.gather(*server_tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\n[!] Arrêt demandé par l'utilisateur. Fermeture des serveurs...")
