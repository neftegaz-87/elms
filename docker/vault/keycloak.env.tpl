{{- with secret "elms/data/runtime" }}
KEYCLOAK_DB_PASSWORD={{ printf "%q" .Data.data.KEYCLOAK_DB_PASSWORD }}
KEYCLOAK_ADMIN_PASSWORD={{ printf "%q" .Data.data.KEYCLOAK_ADMIN_PASSWORD }}
KEYCLOAK_CLIENT_SECRET={{ printf "%q" .Data.data.KEYCLOAK_CLIENT_SECRET }}
NEFTEGAZ_REVIEW_CLIENT_SECRET={{ printf "%q" .Data.data.NEFTEGAZ_REVIEW_CLIENT_SECRET }}
YANDEX_CLIENT_ID={{ printf "%q" .Data.data.YANDEX_CLIENT_ID }}
YANDEX_CLIENT_SECRET={{ printf "%q" .Data.data.YANDEX_CLIENT_SECRET }}
{{- end }}
