---
title: "Falcon Self-Hosting Guide"
space: "Learning"
url: "https://docs.frappe.io/learning/falcon-self-hosting-guide"
updated: "2026-02-06"
---

This guide walks you through setting up and deploying your own instance of Falcon — a live code execution engine.


### Prerequisites


1. A cloud server (e.g., DigitalOcean droplet or any VPS)
2. Python 3.11+
3. Docker and Docker Compose
4. Git
5. Nginx
6. A domain

### Clone the Repository

    git clone https://github.com/fossunited/falcon
    cd falcon

Or use your own fork if needed.


### Setup Python Environment

    python3 -m venv env
    source env/bin/activate
    pip install --upgrade pip
    pip install -r dev-requirements.txt
    
Ensure you also install uvicorn[standard] for WebSocket support:


    pip install 'uvicorn[standard]'

### Pull Docker Images
Falcon uses Docker containers for sandboxed code execution. Pull the base runtimes:

    
    docker pull fossunited/falcon-python:3.9
    docker pull fossunited/falcon-golang
    docker pull fossunited/falcon-rust
    docker pull frappedevs/falcon-javascript

### Create systemd Service
Create a service file at /etc/systemd/system/falcon.service:


    [Unit]
    Description=Falcon LiveCode Service
    After=network.target
    [Service]
    User=root
    WorkingDirectory=/root/falcon
    ExecStart=/root/falcon/env/bin/uvicorn livecode_server.server:app --host 0.0.0.0 --port 8000
    Restart=always
    [Install]
    WantedBy=multi-user.target
    
Then reload and start the service:

    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload
    sudo systemctl enable falcon
    sudo systemctl start falcon

Check logs:

    journalctl -u falcon -f

### Configure Nginx
Install Nginx if not already:

    
    sudo apt update
    sudo apt install nginx
    
Create a new site config under /etc/nginx/sites-available/falcon:


    server {
        listen 80;
        server_name falcon.example.com;
        location / {
            proxy_pass http://localhost:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
    
Enable the site:


    sudo ln -s /etc/nginx/sites-available/falcon /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx

(Optional) Set up HTTPS with Certbot:

    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx

### Test Your Setup
In your browser or frontend app, test a session:

First add the script on a page

    const script = document.createElement('script')
    script.src = `https://falcon.frappe.io/static/livecode.js`
    document.head.appendChild(script)

Then run the session

    const session = new LiveCodeSession({
      base_url: "https://falcon.example.com",
      runtime: "python",
      code: "print('Hello')",
      onMessage: console.log
    });
    
You should see:


    { msgtype: "welcome", message: "welcome to livecode" }


### Troubleshooting
1. 403 or 502 errors: Check journalctl -u falcon -f and nginx -t
2. WebSocket not working: Make sure uvicorn[standard] is installed and Nginx supports WebSockets.
3. Docker errors in tests: Ensure runtime images are pulled correctly.

