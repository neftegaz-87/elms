# syntax=docker/dockerfile:1
# Build from repo root:
#   docker build -f docker/Dockerfile -t elms:local .

ARG PYTHON_VERSION=3.11
ARG DEBIAN_BASE=bookworm
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE} AS base

ARG WKHTMLTOPDF_VERSION=0.12.6.1-3
ARG WKHTMLTOPDF_DISTRO=bookworm
ARG INSTALL_CHROMIUM=true
ARG NODE_VERSION=20

ENV NVM_DIR=/home/frappe/.nvm
ENV NVM_SYMLINK_CURRENT=true
ENV PATH=${NVM_DIR}/current/bin/:${PATH}

RUN useradd -u 1000 -g 0 -d /home/frappe -ms /bin/bash frappe \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates \
    curl \
    git \
    vim \
    nginx \
    gettext-base \
    file \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    restic \
    gpg \
    mariadb-client \
    less \
    libpq-dev \
    postgresql-client \
    wait-for-it \
    jq \
    media-types \
    ffmpeg \
    libmariadb-dev \
    pkg-config \
    && mkdir -p ${NVM_DIR} \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use ${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default ${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && echo 'export NVM_DIR="/home/frappe/.nvm"' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >>/home/frappe/.bashrc \
    && if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_${WKHTMLTOPDF_VERSION}.${WKHTMLTOPDF_DISTRO}_${ARCH}.deb \
    && curl -sLO https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && apt-get install -y ./$downloaded_file \
    && rm $downloaded_file \
    && if [ "$INSTALL_CHROMIUM" != "false" ]; then \
        DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y chromium; \
    fi \
    && rm -rf /var/lib/apt/lists/* \
    && rm -fr /etc/nginx/sites-enabled/default \
    && mkdir -p /etc/nginx/snippets /templates/nginx \
    && pip3 install --no-cache-dir frappe-bench uv \
    && sed -i '/user www-data/d' /etc/nginx/nginx.conf \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log \
    && touch /run/nginx.pid \
    && chgrp -R 0 /home/frappe /etc/nginx /var/log/nginx /var/lib/nginx /run \
    && chmod -R g=u /home/frappe /etc/nginx /var/log/nginx /var/lib/nginx /run

RUN cat <<'SUBEOF' > /etc/nginx/snippets/security_headers.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "same-origin, strict-origin-when-cross-origin" always;
SUBEOF

RUN cat <<'SUBEOF' > /templates/nginx/frappe.conf.template
upstream backend-server {
	server ${BACKEND} fail_timeout=0;
}

upstream socketio-server {
	server ${SOCKETIO} fail_timeout=0;
}

map $http_x_forwarded_proto $proxy_x_forwarded_proto {
	default $scheme;
	https https;
}

server {
	listen ${NGINX_LISTEN_PORT};
	server_name ${FRAPPE_SITE_NAME_HEADER};
	absolute_redirect off;
	root /home/frappe/frappe-bench/sites;

	proxy_buffer_size 128k;
	proxy_buffers 4 256k;
	proxy_busy_buffers_size 256k;

	include /etc/nginx/snippets/security_headers.conf;

	set_real_ip_from ${UPSTREAM_REAL_IP_ADDRESS};
	real_ip_header ${UPSTREAM_REAL_IP_HEADER};
	real_ip_recursive ${UPSTREAM_REAL_IP_RECURSIVE};

	location /assets {
		try_files $uri =404;
	}

	location ~ ^/protected/(.*) {
		internal;
		try_files /${FRAPPE_SITE_NAME_HEADER}/$1 =404;
	}

	location /socket.io {
		proxy_http_version 1.1;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $proxy_x_forwarded_proto;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection "upgrade";
		proxy_set_header X-Frappe-Site-Name ${FRAPPE_SITE_NAME_HEADER};
		proxy_set_header Origin $proxy_x_forwarded_proto://frontend:${NGINX_LISTEN_PORT};
		proxy_set_header Host frontend:${NGINX_LISTEN_PORT};

		proxy_pass http://socketio-server;
	}

	location / {
		rewrite ^(.+)/$ $1 permanent;
		rewrite ^(.+)/index\.html$ $1 permanent;
		rewrite ^(.+)\.html$ $1 permanent;

		location ~ ^/files/.*.(htm|html|svg|xml) {
			include /etc/nginx/snippets/security_headers.conf;
			add_header Content-disposition "attachment";
			try_files /${FRAPPE_SITE_NAME_HEADER}/public/$uri @webserver;
		}

		try_files /${FRAPPE_SITE_NAME_HEADER}/public/$uri @webserver;
	}

	location @webserver {
		proxy_http_version 1.1;
		proxy_set_header X-Forwarded-For $remote_addr;
		proxy_set_header X-Forwarded-Proto $proxy_x_forwarded_proto;
		proxy_set_header X-Frappe-Site-Name ${FRAPPE_SITE_NAME_HEADER};
		proxy_set_header Host $host;
		proxy_set_header X-Use-X-Accel-Redirect True;
		proxy_read_timeout ${PROXY_READ_TIMEOUT};
		proxy_redirect off;

		proxy_pass http://backend-server;
	}

	sendfile on;
	keepalive_timeout 15;
	client_max_body_size ${CLIENT_MAX_BODY_SIZE};
	client_body_buffer_size 16K;
	client_header_buffer_size 1k;

	gzip on;
	gzip_http_version 1.1;
	gzip_comp_level 5;
	gzip_min_length 256;
	gzip_proxied any;
	gzip_vary on;
	gzip_types
		application/atom+xml
		application/javascript
		application/json
		application/rss+xml
		application/vnd.ms-fontobject
		application/x-font-ttf
		application/font-woff
		application/x-web-app-manifest+json
		application/xhtml+xml
		application/xml
		font/opentype
		image/svg+xml
		image/x-icon
		text/css
		text/plain
		text/x-component;
}
SUBEOF

RUN cat <<'SUBEOF' > /usr/local/bin/nginx-entrypoint.sh
#!/bin/bash
set -e

umask 0002

if [[ -z "$BACKEND" ]]; then
  echo "BACKEND defaulting to 0.0.0.0:8000"
  export BACKEND=0.0.0.0:8000
fi
if [[ -z "$SOCKETIO" ]]; then
  echo "SOCKETIO defaulting to 0.0.0.0:9000"
  export SOCKETIO=0.0.0.0:9000
fi
if [[ -z "$NGINX_LISTEN_PORT" ]]; then
  echo "NGINX_LISTEN_PORT defaulting to 8080"
  export NGINX_LISTEN_PORT=8080
fi
if [[ -z "$UPSTREAM_REAL_IP_ADDRESS" ]]; then
  echo "UPSTREAM_REAL_IP_ADDRESS defaulting to 127.0.0.1"
  export UPSTREAM_REAL_IP_ADDRESS=127.0.0.1
fi
if [[ -z "$UPSTREAM_REAL_IP_HEADER" ]]; then
  echo "UPSTREAM_REAL_IP_HEADER defaulting to X-Forwarded-For"
  export UPSTREAM_REAL_IP_HEADER=X-Forwarded-For
fi
if [[ -z "$UPSTREAM_REAL_IP_RECURSIVE" ]]; then
  echo "UPSTREAM_REAL_IP_RECURSIVE defaulting to off"
  export UPSTREAM_REAL_IP_RECURSIVE=off
fi
if [[ -z "$FRAPPE_SITE_NAME_HEADER" ]]; then
  echo 'FRAPPE_SITE_NAME_HEADER defaulting to $host'
  export FRAPPE_SITE_NAME_HEADER='$host'
fi

if [[ -z "$PROXY_READ_TIMEOUT" ]]; then
  echo "PROXY_READ_TIMEOUT defaulting to 120"
  export PROXY_READ_TIMEOUT=120
fi

if [[ -z "$CLIENT_MAX_BODY_SIZE" ]]; then
  echo "CLIENT_MAX_BODY_SIZE defaulting to 50m"
  export CLIENT_MAX_BODY_SIZE=50m
fi

envsubst '${BACKEND}
  ${SOCKETIO}
  ${NGINX_LISTEN_PORT}
  ${UPSTREAM_REAL_IP_ADDRESS}
  ${UPSTREAM_REAL_IP_HEADER}
  ${UPSTREAM_REAL_IP_RECURSIVE}
  ${FRAPPE_SITE_NAME_HEADER}
  ${PROXY_READ_TIMEOUT}
  ${CLIENT_MAX_BODY_SIZE}' \
  < /templates/nginx/frappe.conf.template > /etc/nginx/conf.d/frappe.conf

nginx -g 'daemon off;'
SUBEOF

RUN chmod 755 /usr/local/bin/nginx-entrypoint.sh \
    && chmod 644 /templates/nginx/frappe.conf.template /etc/nginx/snippets/security_headers.conf

FROM base AS builder

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    wget \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    libpq-dev \
    libffi-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadb-dev \
    libsasl2-dev \
    libtiff-dev \
    libwebp-dev \
    pkg-config \
    redis-tools \
    rlwrap \
    tk8.6-dev \
    cron \
    gcc \
    build-essential \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=frappe:0 frappe /home/frappe/src/frappe
COPY --chown=frappe:0 elms /home/frappe/src/elms

USER frappe
WORKDIR /home/frappe

ENV GIT_TERMINAL_PROMPT=0
RUN mkdir -p /home/frappe/frappe-bench/apps \
             /home/frappe/frappe-bench/sites \
             /home/frappe/frappe-bench/config/pids \
             /home/frappe/frappe-bench/logs \
    && cd /home/frappe/frappe-bench \
    && uv venv env --seed --python python3 \
    && cp -a /home/frappe/src/frappe apps/frappe \
    && cp -a /home/frappe/src/elms apps/elms \
    && rm -rf /home/frappe/src

RUN cd /home/frappe/frappe-bench \
    && ./env/bin/pip install --no-cache-dir -e apps/frappe \
    && ./env/bin/pip install --no-cache-dir -e apps/elms

RUN . ${NVM_DIR}/nvm.sh \
    && yarn config set network-timeout 600000 \
    && cd /home/frappe/frappe-bench \
    && for i in 1 2 3 4 5; do yarn --cwd apps/frappe install && break || sleep 15; done

COPY --chown=frappe:0 design-system /home/frappe/frappe-bench/apps/design-system

RUN . ${NVM_DIR}/nvm.sh \
    && cd /home/frappe/frappe-bench \
    && printf 'frappe\nelms\n' > sites/apps.txt \
    && printf '{"socketio_port":9000}\n' > sites/common_site_config.json \
    && touch patches.txt \
    && mkdir -p sites/assets \
    && cd sites \
    && ../env/bin/python -m frappe.utils.bench_helper frappe build --force

FROM base AS backend

USER frappe
COPY --from=builder --chown=frappe:0 --chmod=g=u /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

RUN chmod g=u /home/frappe/frappe-bench \
    && cp -r /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets \
    && rm -rf /home/frappe/frappe-bench/sites/assets

VOLUME [ \
  "/home/frappe/frappe-bench/sites", \
  "/home/frappe/frappe-bench/logs" \
]

USER root
RUN cat <<'SUBEOF' > /usr/local/bin/entrypoint.sh
#!/bin/bash
set -e

umask 0002

ASSETS_PATH="/home/frappe/frappe-bench/sites/assets"
BAKED_PATH="/home/frappe/frappe-bench/assets"

echo "Linking fresh assets to volume..."
rm -rf "$ASSETS_PATH"
mkdir -p "$(dirname "$ASSETS_PATH")"
ln -s "$BAKED_PATH" "$ASSETS_PATH"

exec "$@"
SUBEOF

RUN cat <<'SUBEOF' > /usr/local/bin/start.sh
#!/bin/bash
set -e

GUNICORN_THREADS=${GUNICORN_THREADS:-4}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-120}

echo "Booting Gunicorn with $GUNICORN_WORKERS workers and $GUNICORN_THREADS threads..."

exec /home/frappe/frappe-bench/env/bin/gunicorn \
  --chdir=/home/frappe/frappe-bench/sites \
  --bind=0.0.0.0:8000 \
  --threads="$GUNICORN_THREADS" \
  --workers="$GUNICORN_WORKERS" \
  --worker-class=gthread \
  --worker-tmp-dir=/dev/shm \
  --timeout="$GUNICORN_TIMEOUT" \
  --preload \
  frappe.app:application
SUBEOF

RUN chmod 755 /usr/local/bin/entrypoint.sh /usr/local/bin/start.sh

USER frappe
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["start.sh"]
