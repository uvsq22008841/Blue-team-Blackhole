#!/usr/bin/env python3
import asyncio
import random

# --- Paramètres de limite ---
MAX_CONNEXIONS = 500
active_connections = []  # liste globale pour suivre les connexions

# --- Bannières réalistes/troll par service ---
BANNERS = {
    22: [
        "SSH-2.0-OpenSSH_7.9p1 Debian-10+deb9u2",
        "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5",
        "SSH-2.0-RedStarSSH_3.5 (조선민주주의인민공화국 Linux)",
        "SSH-2.0-OpenSSH_9.0p1 Ubuntu-1ubuntu7.4\r\n",
        "SSH-2.0-OpenSSH_9.0p1 Go-eat-your-dead-9.3\r\n",
        "SSH-2.0-dropbear_2019.78\r\n",
        "SSH-2.0-libssh-0.9.4\r\n",
    ],
    80: [
        "HTTP/1.1 200 OK\r\nServer: Apache/2.4.29 (Ubuntu)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: nginx/1.18.0 (Debian)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: Microsoft-IIS/10.0 (Windows Server 2019)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: Apache/2.2.22 (Red Star OS 3.0)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: lighttpd/1.4.59 (Haiku R1/Beta3)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: nginx/1.16.1 (Solaris 11.4)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: Apache/2.4.52 (Ubuntu_Satanic_Edition)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: nginx/1.20.1 (Red_Star_OS_Karaoke)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: nginx/1.21.3 (LindowsOS)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: Apache/2.4.52 (Hannah Montana Linux)\r\nContent-Length: 0\r\n\r\n",
    ],
    25: [
        "220 mail.example.com ESMTP Postfix (Debian/GNU)\r\n",
        "220 smtp.redstar.kp ESMTP Sendmail 8.14.4/8.14.4\r\n",
        "220 mx.hannahmontana.lol ESMTP Exim 4.92\r\n",
        "220 smtp.example.com Microsoft ESMTP MAIL Service ready\r\n",
        "220 smtp.example.com Microsoft ESMTP MAIL Service ready at Tue, 8 Sep 2025 15:00:00 +0000\r\n",
        "220 mail.example.org ESMTP Sendmail 8.15.2/8.15.2\r\n",
        "220 mx.example.net ESMTP Exim 4.94.2\r\n",
    ],
    21: [
        "220 (vsFTPd 3.0.3)\r\n",
        "220 ProFTPD 1.3.5 Server ready.\r\n",
        "220 ProFTPD 1.3.6 Server (Debian)\r\n",
        "220 FileZilla Server 0.9.60 beta\r\n",
        "220 Microsoft FTP Service\r\n",
        "220 HannahFTPd ready for action!\r\n",
    ],
    110: [
        "+OK POP3 server ready <1896.697170952@dbc.mtview.ca.us>\r\n",
        "+OK Dovecot ready.\r\n",
        "+OK Courier-POP3 server ready <21483.1538962049@pop3.example.com>\r\n",
    ],
    995: [
        "+OK POP3 server ready (SSL/TLS)\r\n",
        "+OK Dovecot secure POP3 service ready.\r\n",
        "+OK RedStar POP3 over SSL service ready.\r\n",
    ],
    # ports non standards : mélange libre
    "generic": [
        "HTTP/1.1 200 OK\r\nServer: nginx/1.21.3 (LindowsOS)\r\nContent-Length: 0\r\n\r\n",
        "POP3 server ready <1896.697170952@dbc.mtview.ca.us>\r\n",
        "IMAP4rev1 Service Ready\r\n",
        "HTTP/1.1 200 OK\r\nServer: lighttpd/1.4.58 (Hannah_Montana_Linux)\r\nContent-Length: 0\r\n\r\n",
        "220 Welcome to Microsoft Exchange SMTP Server\r\n",
        "HTTP/1.0 500 Internal Server Error\r\nServer: Apache/1.3.29 (RedStar OS)\r\n\r\n",
        "SSH-2.0-Go_eat_your_dead_9.3\r\n",
        "HTTP/1.1 200 OK\r\nServer: Apache/2.4.29 (Ubuntu)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: nginx/1.18.0 (Debian)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: Microsoft-IIS/10.0 (Windows Server 2019)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: Apache/2.2.22 (Red Star OS 3.0)\r\nContent-Length: 0\r\n\r\n",
        "220 mail.example.org ESMTP Sendmail 8.15.2/8.15.2\r\n",
        "220 mx.example.net ESMTP Exim 4.94.2\r\n",
        "HTTP/1.1 200 OK\r\nServer: lighttpd/1.4.59 (Haiku R1/Beta3)\r\nContent-Length: 0\r\n\r\n",
        "HTTP/1.1 200 OK\r\nServer: nginx/1.16.1 (Solaris 11.4)\r\nContent-Length: 0\r\n\r\n",
    ],
}

# --- Délai progressif par service ---
def get_delay(port, i):
    if port == 22:  # SSH
        if i <= 6: return random.randint(1, 5)
        else: return random.randint(30, 120)

    elif port in (80, 8080, 443):  # HTTP
        if i <= 10: return random.uniform(0.5, 3)
        elif i <= 20: return random.randint(10, 60)
        else: return random.randint(60, 300)

    elif port in (25, 465, 587):  # SMTP
        if i <= 6: return random.randint(5, 20)
        elif i <= 12: return random.randint(30, 120)
        else: return random.randint(120, 300)

    elif port == 21:  # FTP
        if i <= 4: return random.randint(1, 10)
        elif i <= 10: return random.randint(30, 90)
        else: return random.randint(60, 240)

    elif port in (110, 995):  # POP3
        if i <= 4: return random.randint(1, 10)
        elif i <= 10: return random.randint(20, 60)
        else: return random.randint(60, 180)
        
    else:  # Ports non standards
        if i <= 6: return random.randint(5, 30)
        elif i <= 10: return random.randint(30, 120)
        elif i <= 14: return random.randint(120, 360)
        else: return random.randint(240, 360)

def filler_delay(port):
    """Délai entre les envois de '...\\r\\n' après la bannière, adapté par service."""
    if port == 22:  # SSH
        return random.randint(60, 300)      # 1 à 5 minutes
    elif port in (80, 8080, 443):  # HTTP
        return random.randint(30, 180)     # 30s à 3minutes
    elif port in (25, 465, 587):  # SMTP
        return random.randint(60, 240)     # 1 à 4minutes
    elif port in (110, 995):  # POP3        
        return random.randint(60, 180)     # 1 à 3minutes
    else:  # générique
        return random.randint(60, 360)     # 1 à 6 minutes

async def slow_send(writer, message, port):
    """
    Envoi progressif de la bannière (caractère par caractère), puis boucle
    infinie qui envoie "...\\r\\n" périodiquement pour maintenir le tarpit.
    """
    peer = writer.get_extra_info('peername')
    try:
        # Assure que la bannière se termine par CRLF pour être propre
        if not message.endswith("\r\n"):
            message = message + "\r\n"

        # Envoi caractère par caractère (comportement existant)
        for i, ch in enumerate(message, start=1):
            writer.write(ch.encode())
            await writer.drain()
            delay = get_delay(port, i)
            await asyncio.sleep(delay)

        # Bannière terminée -> entrer dans la boucle "filler"
        print(f"[~] Bannière complète envoyée à {peer}, entrée en boucle '...'.")
        while True:
            writer.write(b"...\r\n")
            await writer.drain()
            # délai adaptable par port
            await asyncio.sleep(filler_delay(port))

    except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
        # Le client a fermé / reset la connexion ou la coroutine a été annulée
        pass

# --- Gestion client ---
async def handle_client(reader, writer, port):
    global active_connections

    addr = writer.get_extra_info('peername')

    # Vérifier limite max
    if len(active_connections) >= MAX_CONNEXIONS:
        old_writer = active_connections.pop(0)
        old_writer.close()
        await old_writer.wait_closed()
        print(f"[!] Expulsé ancienne connexion pour accepter {addr} | Connexions actives: {len(active_connections)}")

    # Nettoyage préventif si proche de la limite
    if len(active_connections) >= MAX_CONNEXIONS - 20:
        for _ in range(min(10, len(active_connections))):
            old_writer = active_connections.pop(0)
            old_writer.close()
            await old_writer.wait_closed()
        print(f"[!] Nettoyage préventif effectué | Connexions actives: {len(active_connections)}")

    # Ajouter la connexion
    active_connections.append(writer)

    # Choix bannière
    if port in BANNERS:
        banner = random.choice(BANNERS[port])
    else:
        banner = random.choice(BANNERS["generic"])

    print(f"[+] Connexion de {addr[0]}:{addr[1]} sur le port {port} | Connexions actives: {len(active_connections)}")
    await slow_send(writer, banner, port)

    # Nettoyage en fin de session
    if writer in active_connections:
        active_connections.remove(writer)
        print(f"[-] Connexion terminée {addr[0]}:{addr[1]} | Connexions actives: {len(active_connections)}")

# --- Serveur principal ---
async def main():
    ports = [22, 21, 25, 80, 110, 995] + list(range(10000, 10010))
    servers = []
    for port in ports:
        server = await asyncio.start_server(
            lambda r, w, p=port: handle_client(r, w, p), '0.0.0.0', port
        )
        servers.append(server)
        print(f"[+] BlackHole actif sur les ports {port}")
    try:
        await asyncio.gather(*(s.serve_forever() for s in servers))
    except KeyboardInterrupt:
        print("\n[!] BlackHole arrêté")

if __name__ == "__main__":
    asyncio.run(main())