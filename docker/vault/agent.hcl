pid_file = "/tmp/vault-agent.pid"
exit_after_auth = false

vault {
  address = "http://vault:8200"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path   = "/vault/bootstrap/role-id"
      secret_id_file_path = "/vault/bootstrap/secret-id"
    }
  }

}

template_config {
  static_secret_render_interval = "5m"
  exit_on_retry_failure = true
}

template {
  source      = "/vault/templates/runtime.env.tpl"
  destination = "/run/elms-secrets/frappe/runtime.env"
  perms       = "0440"
  error_on_missing_key = true
}

template {
  source      = "/vault/templates/keycloak.env.tpl"
  destination = "/run/elms-secrets/keycloak/runtime.env"
  perms       = "0440"
  error_on_missing_key = true
}

template {
  source      = "/vault/templates/db-password.tpl"
  destination = "/run/elms-secrets/db/db-password"
  perms       = "0440"
  error_on_missing_key = true
}

template {
  source      = "/vault/templates/keycloak-db-password.tpl"
  destination = "/run/elms-secrets/db/keycloak-db-password"
  perms       = "0440"
  error_on_missing_key = true
}
