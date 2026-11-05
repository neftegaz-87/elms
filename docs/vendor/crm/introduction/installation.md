---
title: "Installation"
space: "CRM"
url: "https://docs.frappe.io/crm/introduction/installation"
updated: "2026-04-21"
---

Frappe CRM can be installed in multiple ways, depending on your requirements. You can either use **Frappe Cloud** for a fully managed experience or install CRM on your own server.

The following sections explain each installation method in detail.

---

## Managed Hosting (Frappe Cloud)

You can install Frappe CRM with a single click using **[Frappe Cloud](https://frappecloud.com/crm/signup)**, the managed hosting platform for Frappe applications.

- Sign up [here](https://frappecloud.com/crm/signup) to get started
- Your CRM instance will be ready in a few minutes

If you already have a Frappe Cloud site, you can install Frappe CRM directly from the **[Frappe Cloud Marketplace](https://cloud.frappe.io/marketplace/apps/crm)**.

:::tip
Recommendation: We strongly recommend trying Frappe Cloud before opting for self-hosting.
:::





---

## Self Hosting

### Production Setup

Follow these steps to set up Frappe CRM in production:

**Step 1**: Download the easy install script

```
wget https://frappe.io/easy-install.py
```

**Step 2**: Run the deployment command

```
python3 ./easy-install.py deploy \
    --project=crm_prod_setup \
    --email=email.example.com \
    --image=ghcr.io/frappe/crm \
    --version=stable \
    --app=crm \
    --sitename subdomain.domain.tld
```

Replace the following parameters with your values:

- `your_email.example.com`: Your email address
- `subdomain.domain.tld`: Your domain name where CRM will be hosted

The script will set up a production-ready instance of Frappe CRM with all the necessary configurations in about 5 minutes.

:::note
If hosting on a public server, make sure your DNS A record points to your server's IP and if hosting locally, map your domain to 127.0.0.1 in your /etc/hosts file to avoid 404 Page Not Found error.
:::





---

### Development Setup

#### Docker Setup

To run CRM using Docker, ensure the following are installed:

- Docker
- Docker Compose
- Git

Refer to [Docker documentation](https://docs.docker.com/). After that, follow the steps below:

**Step 1**: Create a directory and download the required files

```bash
mkdir frappe-crm
cd frappe-crm

# Download the docker-compose file
wget -O docker-compose.yml https://raw.githubusercontent.com/frappe/crm/develop/docker/docker-compose.yml

# Download the setup script
wget -O init.sh https://raw.githubusercontent.com/frappe/crm/develop/docker/init.sh
```

**Step 2**: Start the containers

```
docker compose up -d
```

**Step 3**: Access the application.

The site [http://crm.localhost:8000/crm](http://crm.localhost:8000/crm) should now be available. The default credentials are:

```
Username: Administrator
Password: admin
```

:::tip
Security note: Recommend changing the default password after login.
:::





#### Local Setup (Bench)

1. [Setup Bench](https://docs.frappe.io/framework/user/en/installation).
2. In the frappe-bench directory, run `bench start` and keep it running.
3. Open a new terminal session and cd into `frappe-bench` directory and run following commands:
  ```
  $ bench get-app crm
  $ bench new-site sitename.localhost --install-app crm
  $ bench browse sitename.localhost --user Administrator
  ```
4. Access the crm page at `sitename.localhost:8000/crm` in your web browser.

**For Frontend Development**

1. Open a new terminal session and cd into `frappe-bench/apps/crm`, and run the following commands:
  ```
  yarn install
  yarn dev

  ```
2. Now, you can access the site on the Vite dev server at `http://sitename.localhost:8080`

**Note:** You'll find all the code related to Frappe CRM's frontend inside `frappe-bench/apps/crm/frontend`