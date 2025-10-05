#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import time

class FileBasedBlacklist:
    def __init__(self, max_attempts=3, time_window=60, blacklist_file="blacklist.json"):
        self.max_attempts = max_attempts
        self.time_window = time_window
        self.blacklist_file = blacklist_file
        self.log_file = "/tmp/flask_connections.log"
        
        # Structures en mémoire
        self.ip_attempts = defaultdict(deque)
        self.load_blacklist()
    
    def load_blacklist(self):
        """Charger la blacklist depuis le fichier"""
        try:
            if os.path.exists(self.blacklist_file):
                with open(self.blacklist_file, 'r') as f:
                    data = json.load(f)
                    self.blacklisted_ips = set(data.get('ips', []))
            else:
                self.blacklisted_ips = set()
        except:
            self.blacklisted_ips = set()
    
    def save_blacklist(self):
        """Sauvegarder la blacklist dans le fichier"""
        data = {
            'ips': list(self.blacklisted_ips),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.blacklist_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_to_blacklist(self, ip_address):
        """Ajouter une IP à la blacklist"""
        if ip_address not in self.blacklisted_ips:
            self.blacklisted_ips.add(ip_address)
            self.save_blacklist()
            print(f"[{datetime.now()}] IP {ip_address} ajoutée à la blacklist")
            
            with open('/var/log/auto_blacklist.log', 'a') as f:
                f.write(f"{datetime.now()}: BLACKLISTED {ip_address}\n")
    
    def is_blacklisted(self, ip_address):
        """Vérifier si une IP est blacklistée"""
        return ip_address in self.blacklisted_ips
    
    def cleanup_old_attempts(self, ip_address):
        """Nettoyer les anciennes tentatives"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(seconds=self.time_window)
        
        while (self.ip_attempts[ip_address] and 
               self.ip_attempts[ip_address][0] < cutoff_time):
            self.ip_attempts[ip_address].popleft()
    
    def record_attempt(self, ip_address, port):
        """Enregistrer une tentative de connexion"""
        if ip_address in ['127.0.0.1', '::1']:
            return
        
        current_time = datetime.now()
        self.cleanup_old_attempts(ip_address)
        self.ip_attempts[ip_address].append(current_time)
        
        attempt_count = len(self.ip_attempts[ip_address])
        print(f"Tentative {attempt_count}/{self.max_attempts} de {ip_address}:{port}")
        
        if attempt_count >= self.max_attempts:
            self.add_to_blacklist(ip_address)
            self.ip_attempts[ip_address].clear()
    
    def monitor_flask_logs(self):
        """Surveiller les logs Flask"""
        if not os.path.exists(self.log_file):
            open(self.log_file, 'a').close()
        
        with open(self.log_file, 'r') as f:
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    try:
                        data = json.loads(line.strip())
                        ip_address = data.get('ip')
                        port = data.get('port', 5000)
                        
                        if ip_address and ip_address not in ['127.0.0.1', '::1']:
                            self.record_attempt(ip_address, port)
                            
                    except json.JSONDecodeError:
                        continue
                else:
                    time.sleep(0.1)

def main():
    blacklist = FileBasedBlacklist(max_attempts=3, time_window=60)
    
    print("Démarrage du monitoring avec blacklist fichier...")
    
    monitor_thread = threading.Thread(target=blacklist.monitor_flask_logs, daemon=True)
    monitor_thread.start()
    
    try:
        while True:
            time.sleep(30)
            print(f"IPs blacklistées: {len(blacklist.blacklisted_ips)}")
            for ip in list(blacklist.blacklisted_ips)[:5]:  
                print(f"  - {ip}")
    except KeyboardInterrupt:
        print("Arrêt du monitoring...")

if __name__ == "__main__":
    main()