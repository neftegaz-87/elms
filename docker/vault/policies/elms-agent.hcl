# Least-privilege policy for the Vault Agent used by ELMS runtime services.
# The agent may render only the single KV v2 data object referenced by the
# templates. Operator/admin operations use a separate human token and are
# never mounted into application containers.
path "elms/data/runtime" {
  capabilities = ["read"]
}
