{{- with secret "elms/data/runtime" }}{{ .Data.data.KEYCLOAK_DB_PASSWORD }}{{ end -}}
