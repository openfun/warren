{{/*
Expand the name of the chart.
*/}}
{{- define "app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "app.fullname" -}}
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
{{- define "app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "app.labels" -}}
helm.sh/chart: {{ include "app.chart" . }}
{{ include "app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: app
app.kubernetes.io/part-of: warren
{{- end }}

{{/*
Environment variables
*/}}
{{- define "app.envs" -}}
- name: "DJANGO_SETTINGS_MODULE"
  value: "{{ .Values.django.settings }}"
- name: "DJANGO_CONFIGURATION"
  value: "{{ .Values.django.configuration }}"
- name: "WARREN_APP_SECRET_KEY"
  valueFrom:
    secretKeyRef:
      name: warren-app-secret-key
      key: WARREN_APP_SECRET_KEY
- name: "WARREN_APP_ALLOWED_HOSTS"
  value: "{{ .Values.django.allowedHosts | join "," }}"
- name: "WARREN_APP_DB_NAME"
  value: "{{ .Values.django.db.name }}"
- name: "WARREN_APP_DB_USER"
  value: "{{ .Values.django.db.user }}"
- name: "WARREN_APP_DB_PASSWORD"
  valueFrom:
    secretKeyRef:
      name: warren-app-db
      key: WARREN_APP_DB_PASSWORD
- name: "WARREN_APP_DB_HOST"
  value: "{{ .Values.django.db.host }}"
- name: "WARREN_APP_DB_PORT"
  value: "{{ .Values.django.db.port }}"
- name: "WARREN_APP_SIGNING_ALGORITHM"
  value: "{{ .Values.django.signingAlgorithm }}"
- name: "WARREN_APP_SIGNING_KEY"
  valueFrom:
    secretKeyRef:
      name: warren-signing-key
      key: WARREN_APP_SIGNING_KEY 
- name: "WARREN_APP_ACCESS_TOKEN_LIFETIME"
  value: "{{ .Values.django.accessTokenLifetime }}"
- name: "WARREN_APP_REFRESH_TOKEN_LIFETIME"
  value: "{{ .Values.django.refreshTokenLifetime }}"
- name: "WARREN_APP_LTI_ACCESS_TOKEN_LIFETIME"
  value: "{{ .Values.django.ltiAccessTokenLifetime }}"
- name: "WARREN_API_ROOT_URL"
  value: {{ .Values.django.apiRootUrl | quote }}
- name: "WARREN_APP_ROOT_URL"
  value: {{ .Values.django.appRootUrl | quote }}
- name: "WARREN_APP_CORS_ALLOWED_ORIGINS"
  value: {{ join "," .Values.django.corsAllowedOrigins | quote }}
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
{{- define "django.imagePullSecrets" -}}
{{- $pullSecrets := .Values.imagePullSecrets }}
{{- if (not (empty $pullSecrets)) }}
imagePullSecrets:
{{- range $pullSecrets }}
- name: {{ . }}
{{ end }}
{{- end -}}
{{- end }}
