#!/usr/bin/env bash
set -euo pipefail

# =========================================
# Blackhole v4 – STRICT "no-pass" + anti-scan
# =========================================
# - Par défaut: TOUT DROP (no-response) -> "filtered" partout.
# - Seuls les ports/TCP de la WHITELIST restent accessibles.
# - Anti-scan dynamique: si une IP émet >= SCANNER_SYNS SYN en SCANNER_WINDOW s,
#   on lui applique DELAY/PERTES sur TOUT son trafic (egress + ingress via IFB).
# - Pas de DELAY/TARPIT par port ici (philosophie "ne jamais laisser passer").
#
# LANCE EN ROOT. Teste d'abord en console pour éviter de te verrouiller.

# -------- PARAMÈTRES --------

# Ports autorisés (TCP/UDP) – tout le reste est blackhole (DROP)
WHITELIST_TCP=(22)      # ⚠️ garde 22 si tu administres à distance
WHITELIST_UDP=()        # souvent vide

# IP(s) d’admin qui contournent tout (sources autorisées)
# Exemple: ADMIN_ALLOW=("192.168.10.23/32" "10.0.0.0/24")
ADMIN_ALLOW=()

# Interface réseau (auto si vide)
IFACE=""

# ---- Anti-scan dynamique (Nmap, etc.) ----
SCANNER_SYNS=10          # déclenchement si >= 10 SYN
SCANNER_WINDOW=5         # dans 5 secondes
ATTACK_DELAY_MS=10000    # +10 s de latence
ATTACK_LOSS_PC=50        # +50% de pertes
SCANNER_IPSET_NAME="scanners"
SCANNER_IFB="ifb0"

# Marque fw/connmark (pour shaping interne si besoin futur)
BH_MARK_HEX=0x30

# ----------------------------

need_cmd(){ command -v "$1" >/dev/null 2>&1 || { echo "Manque: $1"; exit 1; }; }

detect_iface(){
  if [ -z "${IFACE}" ]; then
    IFACE=$(ip -o -4 route show to default | awk '{print $5}' | head -n1 || true)
  fi
  [ -n "${IFACE}" ] || { echo "[!] Impossible de détecter l'interface. Renseigne IFACE=..." ; exit 1; }
}

ensure_base(){
  need_cmd iptables
  need_cmd ip
  need_cmd tc
  need_cmd ipset
}

create_chains(){
  sudo iptables -N BH_INPUT 2>/dev/null || true
  sudo iptables -C INPUT -j BH_INPUT >/dev/null 2>&1 || \
    sudo iptables -I INPUT 1 -j BH_INPUT -m comment --comment "blackhole: jump to BH_INPUT"

  sudo iptables -t mangle -N BH_SCANNER 2>/dev/null || true
}

flush_chains(){
  sudo iptables -F BH_INPUT 2>/dev/null || true
  sudo iptables -t mangle -F BH_SCANNER 2>/dev/null || true
}

delete_chains(){
  sudo iptables -D INPUT -j BH_INPUT -m comment --comment "blackhole: jump to BH_INPUT" 2>/dev/null || true
  sudo iptables -X BH_INPUT 2>/dev/null || true
  sudo iptables -t mangle -X BH_SCANNER 2>/dev/null || true
}

apply_input_policy(){
  # 0) Admin bypass en tout début (sources autorisées)
  for ip in "${ADMIN_ALLOW[@]}"; do
    sudo iptables -I BH_INPUT 1 -s "$ip" -j ACCEPT -m comment --comment "blackhole: admin allow $ip"
  done

  # 1) Autoriser la boucle locale
  sudo iptables -A BH_INPUT -i lo -j ACCEPT -m comment --comment "blackhole: allow loopback"

  # 2) Autoriser les ports WHITELIST_TCP
  if [ "${#WHITELIST_TCP[@]}" -gt 0 ]; then
    sudo iptables -A BH_INPUT -p tcp -m multiport --dports "$(IFS=,; echo "${WHITELIST_TCP[*]}")" \
      -j ACCEPT -m comment --comment "blackhole: allow tcp whitelist"
  fi

  # 3) Autoriser les ports WHITELIST_UDP
  if [ "${#WHITELIST_UDP[@]}" -gt 0 ]; then
    sudo iptables -A BH_INPUT -p udp -m multiport --dports "$(IFS=,; echo "${WHITELIST_UDP[*]}")" \
      -j ACCEPT -m comment --comment "blackhole: allow udp whitelist"
  fi

  # 4) DROP silencieux de tout le reste (=> filtered no-response)
  sudo iptables -A BH_INPUT -p tcp -j DROP -m comment --comment "blackhole: drop all other tcp"
  sudo iptables -A BH_INPUT -p udp -j DROP -m comment --comment "blackhole: drop all other udp"
  sudo iptables -A BH_INPUT -j DROP -m comment --comment "blackhole: drop all other"
}

setup_antiscan(){
  detect_iface

  # a) ipset des scanneurs
  sudo ipset create "$SCANNER_IPSET_NAME" hash:ip timeout 3600 2>/dev/null || true

  # b) Détection burst de SYN → ajoute source dans ipset
  sudo iptables -t mangle -C PREROUTING -p tcp --syn -m recent --name NMAP --set >/dev/null 2>&1 || \
    sudo iptables -t mangle -A PREROUTING -p tcp --syn -m recent --name NMAP --set -m comment --comment "blackhole: recent set"

  sudo iptables -t mangle -C PREROUTING -m recent --name NMAP --rcheck --seconds "$SCANNER_WINDOW" --hitcount "$SCANNER_SYNS" \
    -j SET --add-set "$SCANNER_IPSET_NAME" src >/dev/null 2>&1 || \
    sudo iptables -t mangle -A PREROUTING -m recent --name NMAP --rcheck --seconds "$SCANNER_WINDOW" --hitcount "$SCANNER_SYNS" \
      -j SET --add-set "$SCANNER_IPSET_NAME" src -m comment --comment "blackhole: flag scanner src"

  # c) IFB + redirection de l'ingress
  sudo modprobe ifb 2>/dev/null || true
  ip link show "$SCANNER_IFB" >/dev/null 2>&1 || sudo ip link add "$SCANNER_IFB" type ifb
  sudo ip link set dev "$SCANNER_IFB" up

  sudo tc qdisc add dev "$IFACE" handle ffff: ingress 2>/dev/null || true
  if ! sudo tc filter show dev "$IFACE" parent ffff: 2>/dev/null | grep -q "mirred egress redirect dev $SCANNER_IFB"; then
    sudo tc filter add dev "$IFACE" parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev "$SCANNER_IFB"
  fi

  # d) EGRESS (IFACE) : prio + netem agressif
  sudo tc qdisc show dev "$IFACE" | grep -q 'qdisc prio 1:' || sudo tc qdisc add dev "$IFACE" root handle 1: prio
  sudo tc qdisc add dev "$IFACE" parent 1:3 handle 40: netem delay ${ATTACK_DELAY_MS}ms loss ${ATTACK_LOSS_PC}% 2>/dev/null || true

  # e) INGRESS (via IFB) : prio + netem agressif
  sudo tc qdisc add dev "$SCANNER_IFB" root handle 1: prio 2>/dev/null || true
  sudo tc qdisc add dev "$SCANNER_IFB" parent 1:3 handle 40: netem delay ${ATTACK_DELAY_MS}ms loss ${ATTACK_LOSS_PC}% 2>/dev/null || true

  # f) Marquer les flux vers/depuis IP scanneuses (fwmark 0x40) et router vers la file 1:3 (netem)
  sudo iptables -t mangle -C PREROUTING -m set --match-set "$SCANNER_IPSET_NAME" src -j BH_SCANNER >/dev/null 2>&1 || \
    sudo iptables -t mangle -A PREROUTING -m set --match-set "$SCANNER_IPSET_NAME" src -j BH_SCANNER -m comment --comment "blackhole: jump scanner src"
  sudo iptables -t mangle -C OUTPUT -m set --match-set "$SCANNER_IPSET_NAME" dst -j BH_SCANNER >/dev/null 2>&1 || \
    sudo iptables -t mangle -A OUTPUT -m set --match-set "$SCANNER_IPSET_NAME" dst -j BH_SCANNER -m comment --comment "blackhole: jump scanner dst"

  sudo iptables -t mangle -F BH_SCANNER 2>/dev/null || true
  sudo iptables -t mangle -A BH_SCANNER -j MARK --set-mark 0x40 -m comment --comment "blackhole: mark scanner flow"
  sudo iptables -t mangle -A BH_SCANNER -j CONNMARK --save-mark -m comment --comment "blackhole: connmark save scanner"

  sudo tc filter add dev "$IFACE" parent 1: protocol ip handle 64 fw flowid 1:3 2>/dev/null || true
  sudo tc filter add dev "$SCANNER_IFB" parent 1: protocol ip handle 64 fw flowid 1:3 2>/dev/null || true
}

teardown_antiscan(){
  detect_iface || true
  sudo iptables -t mangle -F BH_SCANNER 2>/dev/null || true
  sudo iptables -t mangle -D PREROUTING -m set --match-set "$SCANNER_IPSET_NAME" src -j BH_SCANNER 2>/dev/null || true
  sudo iptables -t mangle -D OUTPUT -m set --match-set "$SCANNER_IPSET_NAME" dst -j BH_SCANNER 2>/dev/null || true
  sudo ipset destroy "$SCANNER_IPSET_NAME" 2>/dev/null || true
  sudo tc qdisc del dev "$IFACE" ingress 2>/dev/null || true
  sudo tc qdisc del dev "$SCANNER_IFB" root 2>/dev/null || true
  ip link set "$SCANNER_IFB" down 2>/devnull || true
  ip link del "$SCANNER_IFB" 2>/dev/null || true
  sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
}

apply_all(){
  ensure_base
  create_chains
  flush_chains
  apply_input_policy
  setup_antiscan
  echo "[OK] Blackhole v4 appliqué."
  echo "[Info] Tout est DROP (no-response) hors WHITELIST."
  echo "[Info] Anti-scan: ${SCANNER_SYNS} SYN / ${SCANNER_WINDOW}s => +${ATTACK_DELAY_MS}ms & ${ATTACK_LOSS_PC}% perte."
}

rollback_all(){
  teardown_antiscan
  flush_chains
  delete_chains
  echo "[OK] Blackhole v4 retiré."
}

show_status(){
  detect_iface || true
  echo "=== iptables (filter: BH_INPUT) ==="
  sudo iptables -S BH_INPUT || true
  echo "=== iptables (mangle: BH_SCANNER) ==="
  sudo iptables -t mangle -S BH_SCANNER || true
  echo "=== ipset sets ==="
  sudo ipset list "$SCANNER_IPSET_NAME" 2>/dev/null || true
  echo "=== tc qdisc dev $IFACE ==="
  sudo tc qdisc show dev "${IFACE:-lo}" 2>/dev/null || true
  echo "=== tc filters dev $IFACE (root & ingress) ==="
  sudo tc filter show dev "${IFACE:-lo}" parent 1: 2>/dev/null || true
  sudo tc filter show dev "${IFACE:-lo}" parent ffff: 2>/dev/null || true
  echo "=== tc qdisc dev $SCANNER_IFB ==="
  sudo tc qdisc show dev "$SCANNER_IFB" 2>/dev/null || true
  echo "=== tc filters dev $SCANNER_IFB ==="
  sudo tc filter show dev "$SCANNER_IFB" parent 1: 2>/dev/null || true
}

usage(){
  cat <<EOF
Usage: $0 [apply|rollback|status]
  apply     : active blackhole strict + anti-scan dynamique
  rollback  : retire règles & shaping
  status    : affiche l'état
Paramètres: WHITELIST_TCP/UDP, ADMIN_ALLOW, IFACE,
           SCANNER_SYNS, SCANNER_WINDOW, ATTACK_DELAY_MS, ATTACK_LOSS_PC
EOF
}

case "${1:-}" in
  apply) apply_all ;;
  rollback) rollback_all ;;
  status) show_status ;;
  *) usage ; exit 1 ;;
esac