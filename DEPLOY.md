# Deployment Guide for AetherReader

AetherReader is designed to be deployed as a single Docker container that serves both the API and the React frontend.

## Prerequisites

- A VPS (Ubuntu/Debian recommended)
- [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) installed
- (Optional but recommended) A domain name pointing to your VPS IP
- Nextcloud instance with WebDAV access enabled

## Step 1: Clone the Repository

```bash
git clone https://github.com/benhowlett/AetherReader.git
cd AetherReader
```

## Step 2: Configure Environment Variables

Create a `.env` file in the root directory:

```bash
touch .env
```

Add the following content and update with your Nextcloud credentials:

```env
NEXTCLOUD_URL=https://your-nextcloud-domain.com/remote.php/dav/files/your-username/
NEXTCLOUD_USERNAME=your-username
NEXTCLOUD_PASSWORD=your-app-password
```

> **Note:** Use a Nextcloud "App Password" (Settings -> Security) instead of your main password for better security.

## Step 3: Deploy with Docker Compose

Run the following command to build and start the application:

```bash
docker-compose up -d --build
```

The application will now be running on port `3001`. You can access it at `http://your-vps-ip:3001`.

## Step 4: (Recommended) Reverse Proxy with Nginx + SSL

To access your application over HTTPS and a domain name, use Nginx as a reverse proxy.

### Install Nginx and Certbot
```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### Configure Nginx
Create a configuration file: `/etc/nginx/sites-available/aetherreader`

```nginx
server {
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/aetherreader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Obtain SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com
```

## Maintenance

### Updating to the latest version
```bash
git pull
docker-compose up -d --build
```

### Viewing Logs
```bash
docker-compose logs -f
```

### Backup Data
The reading progress is stored in the `./data/sqlite.db` file. Make sure to back up this folder periodically.
