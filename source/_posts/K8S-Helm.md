---
title: K8S-HELM
main_color: "#707DE2"
categories: 云原生
tags:
  - K8S
cover: https://free.picui.cn/free/2026/03/28/69c74d2a05353.jpg
---

## 什么是 Helm？

Helm 是 Kubernetes 的包管理器，可以把它想象成 Kubernetes 生态中的 "apt"、"yum" 或 "brew"。

### Helm 的核心概念

**Helm 是什么？**
- Helm 是一个 Kubernetes 应用的打包、分发和管理工具
- 通过 Chart（图表）来组织和管理 Kubernetes 应用
- 简化复杂应用的部署和管理工作

**为什么需要 Helm？**
```
传统方式部署一个应用：
├── deployment.yaml      (部署定义)
├── service.yaml         (服务定义)
├── configmap.yaml       (配置定义)
├── secret.yaml          (密钥定义)
├── ingress.yaml         (入口定义)
└── persistentvolume.yaml (存储定义)

使用 Helm：
└── myapp/
    ├── Chart.yaml       (Chart 元数据)
    ├── values.yaml      (默认配置值)
    └── templates/       (Kubernetes 模板)
        ├── deployment.yaml
        ├── service.yaml
        ├── configmap.yaml
        └── ...
```

**Helm 的优势**
1. **简化部署**：一个 `helm install` 命令替代多个 `kubectl apply`
2. **配置管理**：通过 `values.yaml` 统一管理配置
3. **版本控制**：支持应用的版本管理和回滚
4. **模板化**：使用 Go template 实现配置的动态化
5. **共享与复用**：Chart 可以打包、分享、版本化

---

## Helm 的核心组件

### 1. Helm Client（Helm 客户端）
- **作用**：负责管理 Charts 和 Releases
- **功能**：
  - 创建 Charts
  - 管理 Chart Repositories
  - 与 Helm Library 交互
  - 管理 Releases

### 2. Chart（图表）
- **定义**：Helm 的打包格式，包含运行一个应用所需的所有资源
- **结构**：
```
mychart/
├── Chart.yaml              # Chart 元数据文件
├── values.yaml             # 默认配置值文件
├── templates/              # 模板目录
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── _helpers.tpl        # 辅助函数文件
├── charts/                 # 依赖的 Chart 目录
├── LICENSE                 # 可选：许可证文件
├── README.md               # 可选：Chart 说明文件
└── .helmignore             # 可选：忽略文件
```

### 3. Release（发布）
- **定义**：Chart 在 Kubernetes 集群中的一个实例
- **特点**：同一个 Chart 可以安装多次，每次安装都会创建一个新的 Release

### 4. Repository（仓库）
- **定义**：Chart 的存储和分享位置
- **类型**：
  - 本地仓库
  - 私有仓库（Harbor、Artifactory）
  - 公共仓库（Helm Hub、Bitnami）

---

## Helm 基本用法

### 安装 Helm

#### macOS
```bash
# 使用 Homebrew
brew install helm

# 验证安装
helm version
```

#### Linux
```bash
# 使用官方脚本
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 验证安装
helm version
```

### 常用 Helm 命令

#### 1. Chart 仓库管理
```bash
# 添加官方仓库
helm repo add bitnami https://charts.bitnami.com/bitnami

# 添加自定义仓库
helm repo add myrepo http://helm.example.com/charts

# 列出已添加的仓库
helm repo list

# 更新仓库索引
helm repo update

# 搜索 Chart
helm search repo nginx

# 移除仓库
helm repo remove bitnami
```

#### 2. 安装和卸载
```bash
# 安装 Chart（从仓库）
helm install my-nginx bitnami/nginx

# 安装 Chart（从本地目录）
helm install myapp ./mychart

# 指定 Release 名称
helm install my-release ./mychart

# 指定 namespace
helm install myapp ./mychart -n mynamespace

# 自定义配置值
helm install myapp ./mychart --set image.tag=v1.0.0

# 使用配置文件
helm install myapp ./mychart -f custom-values.yaml

# 预览安装（dry-run）
helm install myapp ./mychart --dry-run --debug

# 卸载 Release
helm uninstall myapp

# 查看已安装的 Release
helm list

# 查看所有 Release（包括失败和未安装的）
helm list --all
```

#### 3. 升级和回滚
```bash
# 升级 Release
helm upgrade myapp ./mychart

# 升级并指定新配置
helm upgrade myapp ./mychart --set image.tag=v2.0.0

# 强制重新安装
helm upgrade --install myapp ./mychart

# 查看 Release 历史
helm history myapp

# 回滚到上一个版本
helm rollback myapp

# 回滚到指定版本
helm rollback myapp 2
```

#### 4. Chart 创建和验证
```bash
# 创建新的 Chart
helm create mychart

# 验证 Chart
helm lint ./mychart

# 打包 Chart
helm package ./mychart

# 显示 Chart 信息
helm show chart bitnami/nginx

# 显示 Chart 的 values
helm show values bitnami/nginx
```

#### 5. 状态和调试
```bash
# 查看 Release 状态
helm status myapp

# 获取 Release 的 manifest
helm get manifest myapp

# 获取 Release 的 values
helm get values myapp

# 获取 Release 的所有信息
helm get all myapp
```

---

## Helm Chart 开发流程

### 完整开发流程示例

#### 步骤 1：创建 Chart 结构
```bash
# 创建 Chart
helm create myapp

# 查看创建的结构
tree myapp
```

#### 步骤 2：编写 Chart.yaml
```yaml
apiVersion: v2
name: myapp
description: A Helm chart for my application
type: application
version: 0.1.0
appVersion: "1.0"
maintainers:
  - name: Your Name
    email: your.email@example.com
```

#### 步骤 3：定义 values.yaml
```yaml
# values.yaml - 默认配置值

# 镜像配置
image:
  repository: nginx
  pullPolicy: IfNotPresent
  tag: "1.21"

# 副本数
replicaCount: 3

# 服务配置
service:
  type: ClusterIP
  port: 80
  targetPort: 80

# 资源配置
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

# 自动扩缩容配置
autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

# 健康检查
livenessProbe:
  enabled: true
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  enabled: true
  initialDelaySeconds: 5
  periodSeconds: 5

# Ingress 配置
ingress:
  enabled: true
  className: "nginx"
  annotations: {}
  hosts:
    - host: myapp.example.com
      paths:
        - path: /
          pathType: Prefix
  tls: []
```

#### 步骤 4：编写模板文件

**templates/deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "mychart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        {{- include "mychart.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
              protocol: TCP
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          {{- if .Values.livenessProbe.enabled }}
          livenessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: {{ .Values.livenessProbe.initialDelaySeconds }}
            periodSeconds: {{ .Values.livenessProbe.periodSeconds }}
          {{- end }}
          {{- if .Values.readinessProbe.enabled }}
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: {{ .Values.readinessProbe.initialDelaySeconds }}
            periodSeconds: {{ .Values.readinessProbe.periodSeconds }}
          {{- end }}
```

**templates/service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "mychart.selectorLabels" . | nindent 4 }}
```

**templates/ingress.yaml**
```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "mychart.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
```

**templates/_helpers.tpl**
```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "mychart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "mychart.fullname" -}}
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
{{- define "mychart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mychart.labels" -}}
helm.sh/chart: {{ include "mychart.chart" . }}
{{ include "mychart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mychart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mychart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

#### 步骤 5：验证和测试
```bash
# 验证 Chart 语法
helm lint ./myapp

# 预览渲染结果
helm template myapp ./myapp

# 测试安装（dry-run）
helm install myapp ./myapp --dry-run --debug

# 本地测试（需要 Kubernetes 环境）
helm install myapp ./myapp --create-namespace -n dev
helm status myapp -n dev
helm uninstall myapp -n dev
```

#### 步骤 6：打包和分发
```bash
# 打包 Chart
helm package ./myapp

# 打包后生成 myapp-0.1.0.tgz

# 创建 Chart 仓库（本地）
helm serve --address localhost:8879 --repo-path ./charts

# 推送 Chart 到 Harbor（示例）
helm package ./myapp
helm push myapp-0.1.0.tgz oci://harbor.example.com/chartrepo/library
```

---

## 完整实战示例

### 示例：部署一个 Spring Boot 应用

#### 1. 创建 Chart
```bash
helm create springboot-app
cd springboot-app
```

#### 2. 修改 values.yaml
```yaml
image:
  repository: myharbor.com/library/springboot-demo
  pullPolicy: IfNotPresent
  tag: "v1.0.0"

replicaCount: 2

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

env:
  - name: SPRING_PROFILES_ACTIVE
    value: "prod"
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: url

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: api-tls
      hosts:
        - api.example.com

livenessProbe:
  enabled: true
  httpGet:
    path: /actuator/health/liveness
    port: http
  initialDelaySeconds: 60
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3

readinessProbe:
  enabled: true
  httpGet:
    path: /actuator/health/readiness
    port: http
  initialDelaySeconds: 30
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

#### 3. 部署应用
```bash
# 预览
helm template springboot-app ./springboot-app

# 安装到开发环境
helm install springboot-app ./springboot-app \
  --namespace dev \
  --create-namespace \
  --set image.tag=v1.0.0 \
  --set replicaCount=2

# 查看状态
helm status springboot-app -n dev

# 查看所有资源
kubectl get all -n dev -l app.kubernetes.io/name=springboot-app
```

#### 4. 升级应用
```bash
# 升级到新版本
helm upgrade springboot-app ./springboot-app \
  --namespace dev \
  --set image.tag=v2.0.0 \
  --set replicaCount=3

# 查看升级历史
helm history springboot-app -n dev

# 如果新版本有问题，回滚
helm rollback springboot-app -n dev
```

#### 5. 管理应用
```bash
# 查看配置
helm get values springboot-app -n dev

# 导出当前配置
helm get values springboot-app -n dev > current-values.yaml

# 使用导出的配置升级
helm upgrade springboot-app ./springboot-app -n dev -f current-values.yaml

# 卸载应用
helm uninstall springboot-app -n dev
```

---

## Helm 最佳实践

### 1. Chart 开发建议
- ✅ **使用语义化版本**：遵循 SemVer 规范
- ✅ **编写 README**：说明 Chart 的用途、配置项和使用方法
- ✅ **提供 values.yaml 注释**：帮助用户理解配置项
- ✅ **使用 _helpers.tpl**：复用模板代码
- ✅ **支持多环境**：通过 values 文件区分环境
- ✅ **添加健康检查**：liveness 和 readiness probe
- ✅ **设置资源限制**：避免资源滥用
- ✅ **命名规范**：使用有意义的变量和函数名

### 2. 配置管理建议
```yaml
# 推荐：使用有意义的默认值
replicaCount: 3
image:
  repository: nginx
  tag: "1.21"
  
# 推荐：提供配置示例
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi
```

### 3. 版本管理建议
```
mychart/
├── Chart.yaml          # 主版本号
├── values.yaml         # 默认值
├── values-dev.yaml     # 开发环境值
├── values-staging.yaml # 预发环境值
├── values-prod.yaml    # 生产环境值
└── templates/
```

### 4. 安全建议
- 🔒 **不要硬编码密钥**：使用 Secrets
- 🔒 **使用镜像扫描**：确保镜像安全
- 🔒 **限制权限**：RBAC 最小权限原则
- 🔒 **加密传输**：使用 TLS
- 🔒 **定期更新**：保持 Chart 和镜像版本更新

---

## 常见问题和解决方案

### 1. 模板渲染错误
```bash
# 查看详细错误信息
helm template myapp ./mychart --debug

# 常见错误：变量未定义
# 解决：检查 values.yaml 中是否定义了该变量
```

### 2. 依赖问题
```yaml
# Chart.yaml 中添加依赖
dependencies:
  - name: mysql
    version: 9.0.0
    repository: https://charts.bitnami.com/bitnami
    condition: mysql.enabled

# 更新依赖
helm dependency update ./mychart
```

### 3. 升级失败
```bash
# 查看升级历史
helm history myapp

# 回滚到上一版本
helm rollback myapp

# 强制升级
helm upgrade myapp ./mychart --force
```

### 4. 调试技巧
```bash
# 查看渲染后的 YAML
helm template myapp ./mychart

# 查看某个特定资源
helm get manifest myapp | grep -A 20 "kind: Deployment"

# 使用 kubectl 调试
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

---

## 总结

Helm 是 Kubernetes 生态中不可或缺的工具，它通过 Chart 简化了应用的打包、部署和管理工作。

**核心优势**：
1. 🎯 **简化部署**：一个命令部署复杂应用
2. 🔧 **配置管理**：统一管理多环境配置
3. 📦 **版本控制**：支持升级和回滚
4. 🔄 **模板化**：DRY 原则，避免重复代码
5. 🌐 **生态丰富**：大量现成的 Chart 可用

**学习路径建议**：
1. 熟悉基本命令（install、upgrade、uninstall）
2. 理解 Chart 结构（Chart.yaml、values.yaml、templates）
3. 掌握模板语法（Go Template）
4. 实践创建自定义 Chart
5. 学习 Chart 依赖和复用

通过 Helm，Kubernetes 应用的部署和管理将变得更加简单和高效！

