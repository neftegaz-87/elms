{{- with secret "elms/data/runtime" }}{{ .Data.data.DB_PASSWORD }}{{ end -}}
