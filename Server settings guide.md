# VPN Node Setup Guide (Ubuntu 24, 3x-ui, Reality+TCP)

## 1. Обновление системы

```bash
apt update && apt upgrade -y
```

## 2. Установка зависимостей

```bash
apt install -y git ufw curl
```

## 3. Настройка UFW

```bash
ufw allow ssh
ufw allow 6443/tcp
ufw allow 2765/tcp
ufw enable
```

> Порт `6443` — VLESS, порт `2765` — панель 3x-ui. Измените если используете другие.

## 4. Установка 3x-ui

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

При установке задайте:
- Username
- Password
- Port
- Web base path: придумайте случайный (например `/abc123/`)

## 5. Настройка BBR

```bash
echo 'net.core.default_qdisc=fq' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_congestion_control=bbr' >> /etc/sysctl.conf
sysctl -p
```

## 6. Создание inbound в панели

Откройте панель: `https://<IP>:2765/<base_path>/`

Создайте inbound:
- **Protocol**: VLESS
- **Port**: 6443
- **Network**: tcp
- **Security**: reality
- **SNI**: `www.cloudflare.com`
- **Fingerprint**: qq
- **Flow**: xtls-rprx-vision
- Нажмите **Get New Cert** для генерации ключей

## 7. Добавление ноды в .env бота

После создания inbound скопируйте ссылку из панели и добавьте в `.env`:

```env
VPN_NODE_X_KEY=xx_direct
VPN_NODE_X_FLAG=🏳️
VPN_NODE_X_NAME=XX Direct
VPN_NODE_X_PROFILE_NAME="Country TCP #1"
VPN_NODE_X_HOST=<IP сервера>
VPN_NODE_X_PORT=6443
VPN_NODE_X_NETWORK=tcp
VPN_NODE_X_SECURITY=reality
VPN_NODE_X_PUBLIC_KEY=<public key из панели>
VPN_NODE_X_SHORT_ID=<первый short id из панели>
VPN_NODE_X_SNI=www.cloudflare.com
VPN_NODE_X_FINGERPRINT=qq
VPN_NODE_X_FLOW=xtls-rprx-vision
VPN_NODE_X_SPIDER_X=/
VPN_NODE_X_PANEL=https://<IP>:2765/<base_path>/
VPN_NODE_X_USERNAME=grayshark_
VPN_NODE_X_PASSWORD=nope
VPN_NODE_X_INBOUND_ID=1
VPN_NODE_X_SUB_BASE_URL=https://<IP>:2765/<base_path>/sub
```

Замените `X` на номер ноды (6, 7, ...).

## 8. Перезапуск бота

```bash
cd ~/fish_vpn_bot && docker compose up -d
```

## 9. Синхронизация пользователей

Отправьте в боте:
```
/sync_vpn
```
