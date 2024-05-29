{{/*
Expand the name of the chart.
*/}}
{{- define "api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "api.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "api.labels" -}}
helm.sh/chart: {{ include "api.chart" . }}
{{ include "api.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: api
app.kubernetes.io/part-of: warren
{{- end }}

{{/*
Environment variables
*/}}
{{- define "api.envs" -}}
- name: "WARREN_API_SERVER_PORT"
  value: "{{ .Values.service.port }}"
- name: "WARREN_API_DB_NAME"
  value: "{{ .Values.fastapi.db.name }}"
- name: "WARREN_API_DB_USER"
  value: "{{ .Values.fastapi.db.user }}"
- name: "WARREN_API_DB_PASSWORD"
  valueFrom:
    secretKeyRef:
      name: warren-api-db
      key: WARREN_API_DB_PASSWORD
- name: "WARREN_API_DB_ENGINE"
  value: "{{ .Values.fastapi.db.engine }}"
- name: "WARREN_API_DB_HOST"
  value: "{{ .Values.fastapi.db.host }}"
- name: "WARREN_API_DB_PORT"
  value: "{{ .Values.fastapi.db.port }}"
- name: "WARREN_ALLOWED_HOSTS"
  value: {{ printf "%q" .Values.fastapi.allowedHosts | replace " " "," | quote }}
- name: "WARREN_LRS_HOSTS"
  value: "{{ .Values.fastapi.lrs.host }}"
- name: "WARREN_LRS_AUTH_BASIC_USERNAME"
  value: "{{ .Values.fastapi.lrs.username }}"
- name: "WARREN_LRS_AUTH_BASIC_PASSWORD"
  valueFrom:
    secretKeyRef:
      name: warren-api-lrs
      key: WARREN_LRS_AUTH_BASIC_PASSWORD
- name: "WARREN_XI_LMS_BASE_URL"
  value: "{{ .Values.fastapi.xi.lmsBaseUrl }}"
- name: "WARREN_XI_LMS_API_TOKEN"
  valueFrom:
    secretKeyRef:
      name: warren-api-lms
      key: WARREN_XI_LMS_API_TOKEN
- name: "WARREN_XI_DEFAULT_LANG"
  value: "{{ .Values.fastapi.xi.defaultLang }}"
- name: "WARREN_APP_SIGNING_ALGORITHM"
  value: "{{ .Values.fastapi.signingAlgorithm }}"
- name: "WARREN_APP_SIGNING_KEY"
  valueFrom:
    secretKeyRef:
      name: warren-signing-key
      key: WARREN_APP_SIGNING_KEY
{{- range $key, $val := .Values.env.secret }}
- name: {{ $val.envName }}
  valueFrom:
    secretKeyRef:
      name: {{ $val.secretName }}
      key: {{ $val.keyName }}
{{- end }}
{{- end }}

{{/*
ImagePullSecrets
*/}}
{{- define "fastapi.imagePullSecrets" -}}
{{- $pullSecrets := .Values.imagePullSecrets }}
{{- if (not (empty $pullSecrets)) }}
imagePullSecrets:
{{- range $pullSecrets }}
- name: {{ . }}
{{ end }}
{{- end -}}
{{- end }}
