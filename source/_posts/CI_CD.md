---
title: CI/CD
main_color: "#707DE2"
categories: 云原生
tags:
  - CI/CD
  - 运维
cover: https://www.youstable.com/blog/wp-content/uploads/2025/08/Fixing-CICD-Issues.jpg
---

## CI/CD
CI/CD代表持续集成（Continuous Integration）、持续交付（Continuous Delivery）和持续部署（Continuous Deployment）。这些实践是现代软件开发中提高效率、减少错误和加快产品上市时间的关键方法。

1. **持续集成（Continuous Integration, CI）**：这是一种软件开发实践，其中团队成员频繁地将他们的工作代码合并到共享的主线中。每次集成都通过自动化构建（包括编译、发布、自动化测试）来验证，以便尽早发现集成错误。这种方法有助于减少集成问题，并让团队能够更快地发展项目。

2. **持续交付（Continuous Delivery, CD）**：这是在持续集成的基础上更进一步，确保软件可以快速、可靠地被发布到生产环境。除了自动化测试外，还可能包含部署到预生产环境的自动化过程，以确保应用程序随时可以部署到生产环境中。持续交付的目标是让发布过程变得简单且低风险。

3. **持续部署（Continuous Deployment, CD）**：这是一个更激进的做法，意味着每次更改在通过了所有测试后都会自动部署到生产环境。持续部署要求有非常强的自动化测试覆盖率，以保证质量并降低上线的风险。

实施CI/CD流程通常需要使用特定的工具链来支持，如Jenkins、GitLab CI、CircleCI、Travis CI等用于构建和测试；Docker、Kubernetes等用于容器化和服务编排；以及各种监控和日志记录工具来跟踪应用的性能和健康状况。通过采用CI/CD，团队可以更快地响应客户需求，同时保持高质量标准。

## GitLabCiCd

### GitLab CI/CD

GitLab CI/CD 是 GitLab 提供的一套用于实现持续集成、持续交付和持续部署的工具。通过使用 GitLab CI/CD，开发者可以在代码提交或合并请求时自动执行一系列任务，如构建项目、运行测试、部署应用等，从而确保代码的质量和项目的稳定性。

#### 关键概念

- **Pipeline（流水线）**：一个流水线是由多个阶段组成的序列，每个阶段可以包含一个或多个任务（Job）。在GitLab中，一个典型的流水线包括构建、测试和部署阶段。
  
- **Job（任务）**：定义了要执行的操作，比如编译代码、运行测试等。Jobs 在 Runner 上执行。

- **Runner（运行器）**：执行 Jobs 的独立进程。Runner 可以是共享的、特定组的或者特定项目的。

- **Stages（阶段）**：代表流水线中的不同部分，例如 build、test 和 deploy 阶段。所有属于同一阶段的任务并行执行，而下一阶段的任务只有在前一阶段的所有任务成功完成后才会开始。

- **.gitlab-ci.yml 文件**：这是 GitLab CI/CD 的配置文件，位于项目根目录下。它定义了流水线如何工作，包括 stages、jobs 以及它们的执行规则。

#### 使用步骤

1. **创建 `.gitlab-ci.yml` 文件**：首先，在你的项目根目录下创建一个名为 `.gitlab-ci.yml` 的文件。这个文件将告诉 GitLab 如何执行 CI/CD 流程。下面是一个简单的例子：

    ```yaml
    stages:
      - build
      - test
      - deploy

    build_job:
      stage: build
      script:
        - echo "Building the project..."
    
    test_job:
      stage: test
      script:
        - echo "Running tests..."

    deploy_job:
      stage: deploy
      script:
        - echo "Deploying application..."
    ```

2. **配置 Runner**：你需要有至少一个 Runner 来执行这些任务。你可以在 GitLab 界面中注册一个 Runner，选择适合自己项目的 Runner 类型（共享、组或项目专用）。

3. **提交 `.gitlab-ci.yml` 到仓库**：一旦配置好 `.gitlab-ci.yml` 并设置了 Runner，提交此文件到你的 GitLab 仓库。此时，GitLab 将自动检测到这个文件，并根据其内容启动相应的流水线。

4. **监控与调试**：通过 GitLab UI 中的 CI/CD 部分，你可以查看流水线的状态，包括各个 Job 的输出日志。这对于调试失败的 Job 非常有用。

5. **优化与扩展**：随着项目的增长，你可能需要调整流水线的结构或添加更多复杂的逻辑，例如条件执行、环境变量、依赖管理等。

#### 进阶功能

- **环境与部署策略**：GitLab CI/CD 支持为不同的环境定义部署策略，比如开发、测试和生产环境。这有助于管理复杂的应用程序生命周期。

- **安全扫描**：GitLab 提供了多种内置的安全扫描工具，如 SAST（静态应用程序安全测试）、DAST（动态应用程序安全测试），可以帮助你在早期发现潜在的安全问题。

- **性能与负载测试**：除了基本的单元和集成测试之外，你还可以集成性能和负载测试工具来保证软件质量。


### 常用命令
下面是一个表格，列出了GitLab CI/CD中一些常用的命令和说明。请注意，在GitLab CI/CD的上下文中，“命令”通常指的是在`.gitlab-ci.yml`文件中定义的脚本部分或配置指令，而不是直接运行于终端的命令行指令。

| 命令/配置项          | 描述                                                                                           |
|-------------------|----------------------------------------------------------------------------------------------|
| `stages`           | 定义流水线中的不同阶段，例如`build`, `test`, `deploy`。同一阶段的任务并行执行，按顺序进行下一个阶段。        |
| `job_name`         | 任务名称，用于标识不同的任务。每个任务可以包含多个步骤，由`script`字段定义。                         |
| `script`           | 实际要执行的命令列表。这些命令会在Runner上执行，用来完成构建、测试或部署等操作。                       |
| `before_script`    | 在每个任务之前执行的一组命令。它可用于准备环境，比如安装依赖。                                      |
| `after_script`     | 在所有任务完成后执行的一组命令，无论任务成功与否。适合用于清理工作。                                  |
| `only/except`      | 控制哪些分支或标签触发任务。`only`指定包括的规则，而`except`则指定排除的规则。已逐渐被`rules`取代。       |
| `rules`            | 更灵活的任务触发条件设置，可以根据分支、标签、变量等多种条件组合来控制任务是否应该运行。                    |
| `artifacts`        | 定义哪些文件应该作为构建产物保存，并可用于后续任务或其他流程（如下载到本地）。                             |
| `cache`            | 指定需要缓存的文件或目录，以加速后续的Pipeline运行。常用于保存依赖包，避免每次都重新下载。                   |
| `tags`             | 为任务分配标签，以便选择合适的Runner来执行任务。有助于区分不同类型的Runner，如特定语言或操作系统要求的Runner。 |
| `variables`        | 定义环境变量，可以在整个Pipeline中使用，也可用于控制任务的行为。                                        |
| `services`         | 允许你在Docker容器中运行额外的服务，如数据库，供你的测试或应用使用。                                    |


## 示例
```yaml
variables:
  DOCKER_IMAGE: "zx-backend" # 自定义镜像名称
  CONTAINER_NAME: "zx-backend" # 容器名称
  HARBOR_HOST: "192.168.1.46:8080" # Harbor 地址
  HARBOR_URL: "http://192.168.1.46:8080"
  HARBOR_PROJECT: "library" # Harbor 项目名，可根据实际调整
  IMAGE_NAME: "${HARBOR_HOST}/${HARBOR_PROJECT}/${DOCKER_IMAGE}" # 镜像名称
  HARBOR_USERNAME: "admin" # Harbor 用户名
  HARBOR_PASSWORD: "XzzN@2024" # Harbor 密码
  MAVEN_IMAGE: "maven:3.8.6-jdk-8"
  PORT: "28085"
stages:
  - package # 项目打包
  - build # 构建镜像
  - deploy # 部署项目

package:
  stage: package
  image: $MAVEN_IMAGE
  services:
    - docker:dind
  tags:
    - docker
  # 缓存maven依赖
  cache:
    key: global-cache
    paths:
      - ~/.m2/repository
    policy: pull-push
  script:
    - mkdir -p ~/.m2
    - cp settings.xml ~/.m2/settings.xml # 将项目根目录的 settings.xml 复制到 ~/.m2/settings.xml
    - mvn clean package -DskipTests -Dmaven.repo.local=~/.m2/repository
  after_script:
    - ls -la target
  artifacts:
    expire_in: 1 week
    paths:
      - target/*.jar
  only:
    - develop

build:
  image: docker:latest
  stage: build
  tags:
    - shell
  before_script:
    - docker login -u "$HARBOR_USERNAME" -p "$HARBOR_PASSWORD" "$HARBOR_HOST"
  script:
    - ls -la target/  # 确认 .jar 文件是否存在
    - docker build -t $IMAGE_NAME:$CI_COMMIT_SHA . # 构建镜像
    - CURRENT_DATE_TIME=$(date +%Y-%m-%d-%H%M%S) # 获取当前日期和时间，格式为 YYYY-MM-DD-HHMMSS
    - docker tag $IMAGE_NAME:$CI_COMMIT_SHA $IMAGE_NAME:$CURRENT_DATE_TIME # tag时间
    - docker push $IMAGE_NAME:$CI_COMMIT_SHA # 推送镜像
  only:
    - develop

deploy:
  stage: deploy
  tags:
    - shell
  script:
    # 删除旧容器
    - if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then docker stop ${CONTAINER_NAME} && docker rm ${CONTAINER_NAME}; fi
    - docker pull $IMAGE_NAME:$CI_COMMIT_SHA
    - docker run -d --name $CONTAINER_NAME -p $PORT:8890 $IMAGE_NAME:$CI_COMMIT_SHA
  only:
    - develop
```



## Jenkins

Jenkins 是一个开源的 **持续集成（CI）和持续交付（CD）** 工具，用于自动化软件开发过程中的构建、测试和部署。它基于 Java 开发，支持跨平台运行，并提供了强大的插件生态系统，可以灵活地扩展功能。

---

### **核心功能**
1. **持续集成（CI）**  
   - 自动触发代码构建和测试，确保每次代码提交后快速发现错误。
   - 支持与 Git、SVN 等版本控制系统集成。

2. **持续交付/部署（CD）**  
   - 自动化部署到测试、预发布或生产环境。
   - 支持 Docker、Kubernetes、云平台（AWS、Azure 等）。

3. **任务调度与流水线**  
   - 通过 **Pipeline（Jenkinsfile）** 定义复杂的构建流程（Groovy 语法）。
   - 支持多分支流水线，适应 Git Flow 等开发模式。

4. **丰富的插件生态**  
   - 超过 1,500 个插件，覆盖代码质量分析（SonarQube）、通知（Slack/Email）、安全扫描等。

5. **分布式构建**  
   - 通过 Agent（节点）实现多机器并行构建，加速任务执行。

---

### **核心概念**
- **Job（任务）**：定义一个自动化任务（如构建、测试）。
- **Pipeline**：将多个任务串联成流水线，支持复杂流程。
- **Agent（节点）**：执行任务的机器（Master/Slave 架构）。
- **插件（Plugins）**：扩展 Jenkins 功能（如 Git、Docker、Kubernetes 支持）。

---

### **优势**
- **开源免费**：社区活跃，文档丰富。
- **高度可扩展**：通过插件适应各种技术栈（Java、Python、Go 等）。
- **可视化界面**：提供构建日志、测试报告和趋势分析。
- **跨平台**：支持 Windows、Linux、macOS。

---

### **典型工作流程**
1. 开发者提交代码到 Git 仓库。
2. Jenkins 检测到变更，触发构建。
3. 执行编译、单元测试、代码扫描。
4. 生成构建产物（如 JAR/Docker 镜像）。
5. 部署到测试环境或生产环境（需配置 CD 流程）。

---

### **与其他工具的对比**
| 工具          | 特点                                                                 |
|---------------|----------------------------------------------------------------------|
| **Jenkins**   | 插件丰富、灵活，适合复杂场景，但需手动维护。                         |
| **GitLab CI** | 与 GitLab 深度集成，配置简单（YAML），适合云原生项目。               |
| **GitHub Actions** | 原生集成 GitHub，易用性强，适合开源项目。                    |
| **CircleCI**  | 云托管服务，快速启动，适合中小团队。                                 |

---

### **快速入门**
1. **安装**  
   - 下载 [Jenkins WAR 包](https://www.jenkins.io/download/) 或使用 Docker：
     ```bash
     docker run -p 8080:8080 jenkins/jenkins:lts
     ```
2. **初始化**  
   - 访问 `http://localhost:8080`，按向导完成配置。
3. **创建 Pipeline**  
   - 在 Jenkins 界面定义或直接编写 `Jenkinsfile`。

---

### **适用场景**
- 需要频繁集成和测试的团队。
- 多环境部署（Dev/Test/Production）。
- 微服务架构或容器化项目。

---


## 常用item及场景

以下是Jenkins中常用的项目类型（Item）及其适用场景的表格概述：

| Jenkins Item 类型           | 描述                                                                                   | 适用场景                                                                                      |
|--------------------------|--------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **自由风格软件项目 (Freestyle project)** | 提供高度灵活的配置选项，允许用户组合不同的构建步骤、源码管理方法和构建触发器。          | - 需要自定义构建过程。<br>- 涉及多种技术栈或工具链。<br>- 对于刚开始使用Jenkins且需要灵活性的项目。 |
| **Maven项目 (Maven Project)**         | 专为Java项目设计，特别适合使用Maven作为构建工具的项目。自动解析POM文件并执行相应的生命周期阶段。 | - 基于Maven的Java项目。<br>- 自动化依赖管理和构建过程。<br>- 利用Maven的插件生态系统。              |
| **Pipeline**                    | 使用Groovy脚本定义的持续集成/持续交付流程，支持复杂的CI/CD逻辑。                           | - 需要定义复杂或多阶段的CI/CD流程。<br>- 希望将CI/CD配置纳入版本控制。<br>- 支持多分支流水线等高级特性。 |
| **多分支流水线 (Multibranch Pipeline)** | 自动发现代码仓库中的所有分支，并分别为每个分支创建一个Pipeline。                                | - 开发过程中频繁创建新分支。<br>- 不同分支有不同的构建、测试或部署要求。<br>- 自动化分支级别的CI/CD流程。   |
| **GitHub Organization**       | 自动扫描GitHub组织下的所有仓库，并根据预定义的规则为每个仓库创建对应的Jenkins任务。             | - 管理大型GitHub组织下多个项目的CI/CD。<br>- 快速设置整个组织的自动化流程。<br>- 维护一致的CI/CD标准。      |
| **文件夹 (Folder)**            | 用于组织和管理其他Jenkins任务的容器。可以包含其他任何类型的Jenkins任务。                        | - 管理大量Jenkins任务时提高组织性。<br>- 分类和隔离不同团队或项目的任务。<br>- 应用统一的安全策略或权限控制。 |


## publish ssh
### Publish Over SSH 插件介绍

**Publish Over SSH** 是 Jenkins 中的一个插件，它允许你通过 SSH 协议将文件或目录从 Jenkins 服务器传输到远程服务器，并在远程服务器上执行命令。这对于部署应用、同步文件以及管理远程服务器非常有用。

#### 主要功能

- **文件传输**：支持通过 SCP（Secure Copy Protocol）将构建产物（如 JAR 文件、WAR 文件、配置文件等）上传到远程服务器。
- **远程命令执行**：可以在文件传输完成后，在远程服务器上执行任意的 shell 命令。这可以用于启动服务、重启应用等操作。
- **多个远程服务器支持**：可以配置多个远程服务器，并根据需要选择向哪个服务器发布内容。
- **安全性**：使用 SSH 密钥认证机制来确保安全连接，避免明文密码在网络中传输的风险。

#### 使用步骤

1. **安装插件**：
   - 在 Jenkins 的“Manage Jenkins”页面中找到“Manage Plugins”，然后在“Available”标签页搜索并安装“Publish Over SSH”插件。

2. **配置 SSH Server**：
   - 安装完插件后，进入“Manage Jenkins” -> “Configure System”，向下滚动至“Publish over SSH”部分。
   - 添加新的 SSH server 配置，包括名称、主机名/IP地址、用户名及认证信息（可以是密码或者私钥路径）。测试连接以确保配置正确。

3. **在 Job 中使用 Publish Over SSH**：
   - 创建或编辑你的 Jenkins Job，在构建后的操作中添加“Send build artifacts over SSH”选项。
   - 在这里可以选择之前配置好的 SSH server，并指定要发送的文件或目录（使用相对路径相对于工作区根目录），还可以设置目标路径以及要在远程服务器上执行的命令。

4. **示例配置**：

```yaml
# 示例: 发送 target/myapp.jar 到远程服务器的 /opt/myapp 目录下，并重启服务
Transfers:
  - Remote directory: /opt/myapp
    Source files: target/myapp.jar
    Exec command: |
      sudo systemctl stop myapp.service
      cp myapp.jar /opt/myapp/
      sudo systemctl start myapp.service
```

注意：上面的例子是一个概念性的描述，实际配置时应按照Jenkins界面提供的表单填写相关信息。

5. **触发构建**：
   - 每当 Jenkins Job 被触发时（例如代码提交触发），如果配置了 Publish Over SSH 步骤，则会自动将指定的文件传输到远程服务器，并执行相应的命令。

通过这种方式，你可以自动化地完成从构建到部署的整个过程，提高开发效率，减少人为错误。Publish Over SSH 是实现持续交付（Continuous Delivery）和持续部署（Continuous Deployment）的重要工具之一。



## Jenkins Agent 与 Publish Over SSH 的区别

虽然 Jenkins Agent 和 Publish Over SSH 都涉及到远程服务器的操作，但它们的目的和使用场景有着本质的区别。下面从几个关键点来区分这两者：

#### 1. **目的与功能**

- **Jenkins Agent**：
  - **目的**：扩展 Jenkins 主节点的能力，实现分布式构建。
  - **功能**：通过在不同的机器上运行 Jenkins Agent（以前称为 Slave），可以将构建任务分散到多个节点上执行。这有助于提高构建速度、隔离环境以及利用不同操作系统或硬件资源。
  - **适用场景**：当你需要跨平台构建（如同时支持Windows和Linux）、负载均衡或者隔离构建环境时非常有用。

- **Publish Over SSH**：
  - **目的**：用于部署应用或文件传输到远程服务器。
  - **功能**：主要用来通过SSH协议将构建产物（如JAR/WAR文件）上传到远程服务器，并且可以在远程服务器上执行命令（例如重启服务）。它专注于部署流程而非构建过程本身。
  - **适用场景**：当你的构建完成后需要将生成的文件部署到生产或其他环境中时使用。

#### 2. **操作层面**

- **Jenkins Agent**：
  - 在配置Agent时，你需要指定该Agent如何连接回Jenkins主节点（比如通过JNLP、SSH等方式），并定义其标签（Label），以便于在Pipeline中选择合适的节点执行任务。
  - Jenkins Agent本质上是作为Jenkins的一个工作节点存在，它可以执行任何被分配的任务，包括但不限于编译代码、运行测试等。

- **Publish Over SSH**：
  - 更侧重于“推送”操作，即将本地（通常是Jenkins主节点或某个特定Agent的工作空间）的文件推送到远程服务器，并可能在远程服务器上执行一些命令。
  - 它通常是在构建完成后作为“发布”或“部署”的一部分被调用。

#### 3. **使用场景示例**

- **Jenkins Agent** 示例：
  ```groovy
  pipeline {
      agent { label 'linux' }
      stages {
          stage('Build') {
              steps {
                  sh 'mvn clean package'
              }
          }
      }
  }
  ```
  这段脚本指定了使用带有`linux`标签的Agent来执行构建步骤。

- **Publish Over SSH** 示例：
  ```groovy
  pipeline {
      agent any
      stages {
          stage('Deploy') {
              steps {
                  sshPublisher(
                      publishers: [
                          sshPublisherDesc(
                              configName: 'ProductionServer',
                              transfers: [
                                  sshTransfer(
                                      sourceFiles: 'target/myapp.jar',
                                      removePrefix: 'target',
                                      remoteDirectory: '/opt/myapp/'
                                  )
                              ],
                              execCommand: 'sudo systemctl restart myapp.service'
                          )
                      ]
                  )
              }
          }
      }
  }
  ```
  此脚本展示了如何在构建成功后，使用Publish Over SSH插件将构建产物部署到远程服务器，并重启相关服务。

总结来说，**Jenkins Agent** 是为了实现分布式的构建环境，让构建任务能够在多个不同的环境中高效地执行；而 **Publish Over SSH** 则是为了简化部署流程，帮助你轻松地将构建结果发布到目标服务器上，并可选地执行必要的后续命令。两者在CI/CD流程中扮演的角色不同，但都是不可或缺的部分。


## 一个示例

```java
pipeline {
    agent any

    triggers {
        gitlab(
            triggerOnPush: true,
            triggerOnMergeRequest: false,
            branchFilterType: 'NameBasedFilter',
            branchFilterName: 'project/hg'
        )
    }

    environment {
        // 工作目录
        WORKSPACE_BASE = "/var/jenkins_home/workspace/zx-knowledge-hg"

        // Git 配置
        GIT_REPO = "http://123.57.244.236:1080/production/zx/knowledge-base/danbaizhi-api-develop.git"
        GIT_BRANCH = "project/hg"

        // Maven 镜像
        MAVEN_IMAGE = "maven:3.9.11-eclipse-temurin-17-alpine"
        JAR_PATH = "target/*.jar"

        // Harbor 镜像仓库
        HARBOR_HOST = "123.57.244.236:8079"
        HARBOR_URL = "http://123.57.244.236:8079"
        HARBOR_PROJECT = "library"
        DOCKER_IMAGE_NAME = "zx-backend-hg"
        IMAGE_REPO = "${HARBOR_HOST}/${HARBOR_PROJECT}/${DOCKER_IMAGE_NAME}"

        // 部署配置
        CONTAINER_NAME = "zx-backend-hg"
        APP_PORT = "55285"
        NETWORK = "zx_dev"


        HARBOR_CREDENTIAL_ID = '546a45a5-5eae-4d11-ba80-3d5407b1ad85'
        SSH_CREDENTIAL_ID = '6030f215-cdf3-4bb5-ad6d-21141f339997'
        DEPLOY_SERVER = 'caohongwei@110.157.241.3'
        DEPLOY_SERVER_PORT = '18243'
    }

    stages {

        stage('Checkout Code') {
            steps {
                dir(env.WORKSPACE_BASE) {
                    git(
                        url: env.GIT_REPO,
                        branch: env.GIT_BRANCH,
                        credentialsId: '79d7c253-c260-4c85-b7e9-b47bee9e0cc3',
                        poll: false
                    )
                    sh '''
                        echo "===== 代码目录内容 ====="
                        pwd
                        ls -la
                    '''
                }
            }
        }

        stage('Maven Build') {
            agent {
                docker {
                    image env.MAVEN_IMAGE
                    // 使用 root 用户避免权限问题
                    args '-u root -v $HOME/.m2:/root/.m2 --network=host'
                }
            }
            steps {
                dir(env.WORKSPACE_BASE) {
                    sh '''
                        echo "===== 验证 Maven 配置 ====="
                        cat settings.xml || echo "无自定义settings.xml"

                        mkdir -p /root/.m2
                        cp -f settings.xml /root/.m2/ || echo "使用默认配置"

                        echo "===== 当前 Maven 仓库配置 ====="
                        mvn help:effective-settings | grep -A 10 "<mirrors>"

                        echo "===== 开始构建 ====="
                        mvn clean package -DskipTests -s /root/.m2/settings.xml
                    '''
                }
            }
        }

  stage('Build Docker Image') {
            steps {
                script {
                    def timestamp = new Date().format('yyyy-MM-dd-HHmmss')
                    def imageTag = "${env.DOCKER_IMAGE_NAME}:${timestamp}"

                    dir(env.WORKSPACE_BASE) {
                        echo "构建 Docker 镜像：${imageTag}"
                        sh "docker build -f Dockerfile -t ${imageTag} --build-arg JAR_PATH=${env.JAR_PATH} ."

                        // 打标签 latest
                        sh "docker tag ${imageTag} ${env.DOCKER_IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('Run Docker Container') {
            steps {
                script {
                    echo "停止并移除旧容器（如果存在）"
                    sh """
                        if docker ps -a --format '{{.Names}}' | grep -w ${env.DOCKER_IMAGE_NAME}; then
                            docker stop ${env.DOCKER_IMAGE_NAME} || true
                            docker rm ${env.DOCKER_IMAGE_NAME} || true
                        fi
                    """

                    echo "启动新容器"
                    sh """
                        docker run -d \\
                            --name ${env.DOCKER_IMAGE_NAME} \\
                            -p ${env.APP_PORT}:8890 \\
                            -p 5005:5005 \\
                            --restart unless-stopped \\
                            --memory="16g" \\
                            ${env.DOCKER_IMAGE_NAME}:latest
                    """

                    echo "等待服务启动..."
                    sh "sleep 30"

                    echo "健康检查"
                    sh "curl -I http://localhost:${env.APP_PORT}/health"
                }
            }
        }
    }


    post {
        always {
            script {
                echo "清理工作区前修复权限"
            }
            cleanWs()
        }
        success {
            echo "✅ 部署成功！访问地址：http://${env.DEPLOY_SERVER.split('@')[1]}:${env.APP_PORT}"
        }
        failure {
            emailext(
                subject: "❌ 构建失败: ${env.JOB_NAME} #${BUILD_NUMBER}",
                body: """
                    失败阶段: ${currentBuild.result}
                    详情: ${BUILD_URL}
                    日志: ${BUILD_URL}console
                """,
                to: 'devops@example.com'
            )
        }
    }
}
```


## 一些坑

### docker部署的Jenkins无法使用docker命令

解决方案-在docker内部安装docker-cli,同时挂在docker-sock

### docekr推送到私有仓库是https，docker.login必须有证书


