---
title: "Installation"
space: "Learning"
url: "https://docs.frappe.io/learning/get-started/installation"
updated: "2026-08-27"
---

Frappe Learning can be installed in multiple ways, depending on your requirements. You can either use **Frappe Cloud** for a fully managed experience or install Learning on your own server.

The following sections explain each installation method in detail.

---

## Managed Hosting (Frappe Cloud)

You can install Frappe Learning with a single click using [**Frappe Cloud**](https://frappe.io/redirect?redirect_to=https://frappecloud.com/dashboard/signup?product=lms), the managed hosting platform for Frappe applications.

- Sign up [here](https://frappe.io/redirect?redirect_to=https://frappecloud.com/dashboard/signup?product=lms) to get started
- Your Learning instance will be ready in a few minutes

If you already have a Frappe Cloud site, you can install Frappe Learning directly from the [**Frappe Cloud Marketplace**](https://cloud.frappe.io/marketplace/apps/lms).

:::tip
Recommendation: We strongly recommend trying Frappe Cloud before opting for self-hosting.
:::



---

## Self Hosting

### Production Setup

Follow these steps to set up Frappe Learning in production:

**Step 1**: Download the easy install script

```
wget https://frappe.io/easy-install.py
```

**Step 2**: Run the deployment command

```
python3 ./easy-install.py deploy \
    --project=learning_prod_setup \
    --email=your_email.example.com \
    --image=ghcr.io/frappe/lms \
    --version=stable \
    --app=lms \
    --sitename subdomain.domain.tld
```

Replace the following parameters with your values:

- `your_email.example.com`: Your email address
- `subdomain.domain.tld`: Your domain name where Learning will be hosted

The script will set up a production-ready instance of Frappe Learning with all the necessary configurations in about 5 minutes.

:::note
If hosting on a public server, make sure your DNS A record points to your server's IP and if hosting locally, map your domain to 127.0.0.1 in your /etc/hosts file to avoid 404 Page Not Found error.
:::



---

### Development Setup

#### Docker Setup

To run Learning using Docker, ensure the following are installed:

- Docker
- Docker Compose
- Git

Refer to [Docker documentation](https://docs.docker.com/). After that, follow the steps below:

**Step 1**: Create a directory and download the required files

```
mkdir frappe-learning
cd frappe-learning

# Download the docker-compose file
wget -O docker-compose.yml https://raw.githubusercontent.com/frappe/lms/develop/docker/docker-compose.yml

# Download the setup script
wget -O init.sh https://raw.githubusercontent.com/frappe/lms/develop/docker/init.sh
```

**Step 2**: Start the containers

```
docker compose up -d
```

**Step 3**: Access the application.

The site [http://lms.localhost:8000/lms](http://lms.localhost:8000/lms) should now be available. The default credentials are:

```
Username: Administrator
Password: admin
```

:::tip
Security note: Recommend changing the default password after login.
:::



#### Local Setup (Bench)

To set up the repository locally, follow the steps mentioned below:

1. Install a bench and set up a `frappe-bench` directory by following the [Installation Steps](https://frappeframework.com/docs/user/en/installation)
2. Start the server by running `bench start`
3. In a separate terminal window, create a new site by running `bench new-site learning.test`
4. Map your site to localhost with the command `bench --site learning.test add-to-hosts`
5. Get the Learning app. Run `bench get-app https://github.com/frappe/lms`
6. Run `bench --site learning.test install-app lms`.
7. Now open the URL `http://learning.test:8000/lms` on your browser, you should see the app running