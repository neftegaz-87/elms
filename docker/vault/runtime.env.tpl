{{- with secret "elms/data/runtime" }}
DB_PASSWORD={{ printf "%q" .Data.data.DB_PASSWORD }}
ADMIN_PASSWORD={{ printf "%q" .Data.data.ADMIN_PASSWORD }}
KEYCLOAK_CLIENT_SECRET={{ printf "%q" .Data.data.KEYCLOAK_CLIENT_SECRET }}
ELMS_REVIEW_HANDOFF_SECRET={{ printf "%q" .Data.data.ELMS_REVIEW_HANDOFF_SECRET }}
NEFTEGAZ_REVIEW_CLIENT_SECRET={{ printf "%q" .Data.data.NEFTEGAZ_REVIEW_CLIENT_SECRET }}
{{- end }}
