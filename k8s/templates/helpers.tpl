{{- define "helpers.list-env-variables"}}
{{- range $key, $val := .Values.deployment.env.secrets }}
- name: {{ $key }}
  valueFrom:
    secretKeyRef:
      name: authn-sec
      key: {{ $key }}
{{- end}}
{{- end }}

{{- define "helpers.list-vars-db-loc"}}
{{- range $key, $val := .Values.deployment.env.db }}
- name: {{ $key }}
  value: "{{ $val }}"
{{- end }}
{{- end }}
