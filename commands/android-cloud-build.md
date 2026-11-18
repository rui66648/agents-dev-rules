---
name: android-cloud-build
version: v1.0.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-08-03
description: 斜杠命令：android-cloud-build - 启动 android-cloud-build 工作流
---
# /android-cloud-build - Android 云端构建

> 触发词: "构建 APK"、"GitHub Actions 打包"、"Android 发布"、"打 release 包"
>
> 适用项目：应用 A（Capacitor + WebView）、应用 B（原生 Kotlin + Compose）
> 更新日期：2026-07-23

---

## 命令语法

```
/android-cloud-build [project-type] [--version=X.Y.Z] [--sign=true|false] [--track=internal|beta|production]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project-type` | enum | 否 | `capacitor` | 项目类型：`capacitor`（Capacitor + Web）、`native`（原生 Kotlin） |
| `--version` | string | 否 | 自动递增 | 版本号，格式 `X.Y.Z`；如未指定，自动基于上版本递增 |
| `--sign` | bool | 否 | `true` | 是否启用签名（发布正式包时必须为 `true`） |
| `--track` | enum | 否 | `internal` | 发布渠道：`internal`（内测）、`beta`（公测）、`production`（正式） |

## 触发场景

- 功能开发完成，需要打包 APK 供测试或发布
- 版本迭代结束，需要构建正式签名包
- 修复 Bug 后，需要重新构建并分发
- CI/CD 流水线中，自动触发构建
- 需要验证云端构建环境配置是否正确

## 前置条件

1. GitHub Secrets 已配置完整（`SIGNING_KEY`、`KEYSTORE_PASSWORD`、`KEY_ALIAS`、`KEY_PASSWORD`）
2. 代码已提交并推送至 GitHub
3. `AndroidManifest.xml` 中 `versionCode` 已递增（或启用自动递增）
4. 项目根目录存在 `.github/workflows/release.yml`
5. 签名密钥（`.jks` 文件）已正确生成 base64 编码并存入 Secrets

## 执行流程

1. **版本确认** — 确认 `versionCode` / `versionName` 与 `--version` 参数一致
2. **标签创建** — 基于版本号创建 Git Tag（`vX.Y.Z`）
3. **推送触发** — 推送 Tag 到 GitHub，触发 `release` Workflow
4. **环境准备** — GitHub Actions 准备 Node 22 / JDK 21 / Gradle 环境
5. **依赖安装** — 安装 npm 依赖（Capacitor 项目）或 Gradle 依赖（原生项目）
6. **构建打包** — 构建 JS bundle（Capacitor）-> Sync -> 编译 Android 项目 -> 生成 APK
7. **签名处理** — 解码 keystore，配置签名参数，生成签名 APK
8. **产物上传** — 上传 APK 到 GitHub Releases，自动生成 Release Notes
9. **结果通知** — 构建成功/失败通知，输出下载链接

## 产出物

- **APK 文件**：`app-release.apk`（已签名）
- **GitHub Release**：含 APK 下载链接、版本说明、变更日志
- **构建日志**：GitHub Actions 完整执行日志
- **构建检查清单**：环境版本、签名状态、构建耗时

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| Workflow 语法错误（secrets 不能直接用于 `if`） | 通过 `env` 中转变量后再判断，参见踩坑清单第 1 条 |
| Node.js 版本不足（Capacitor 要求 >= 22） | 显式指定 `actions/setup-node@v4` 的 `node-version: 22` |
| JDK 版本不足（AGP 8.5+ 建议 JDK 21） | 统一使用 `actions/setup-java@v4` 配置 JDK 21 |
| 签名密钥 base64 编码无效 | 使用 PowerShell `[Convert]::ToBase64String` 重新生成，验证解码 |
| 资源文件被误存为 base64 文本（PNG 损坏） | 删除损坏文件，使用 XML 矢量图标替代 |
| R.drawable 引用语法错误 | Java/Kotlin 代码中使用点号（`R.drawable.xxx`），XML 中使用斜杠（`@drawable/xxx`） |
| GitHub 网络连接不稳定（国内环境） | 多次重试推送，使用代理或 SSH，或切换 Gitee 镜像 |
| 构建失败排查 | 按"Runner 日志 -> 环境版本 -> 签名配置 -> 资源文件 -> 依赖缓存 -> 网络问题"顺序排查 |

## 示例

### 示例 1：Capacitor 项目构建内测包

```
/android-cloud-build capacitor --version=1.4.2 --sign=true --track=internal
```

**预期输出**：
- 创建 Tag `v1.4.2` 并推送
- GitHub Actions 触发构建
- 输出 APK：`app-release.apk`（约 15MB）
- GitHub Release 页面：`https://github.com/<owner>/<repo>/releases/tag/v1.4.2`

### 示例 2：原生 Android 项目构建正式包

```
/android-cloud-build native --version=2.0.0 --sign=true --track=production
```

**预期输出**：
- 构建正式签名 APK
- 上传至 GitHub Releases
- 生成 Release Notes（基于提交历史）
- 通知：构建成功，耗时 8 分钟

---

## 一、流程总览

```
本地提交 → 打 Tag (vX.Y.Z) → 推送 → GitHub Actions 触发
→ 环境准备 (Node / JDK / Gradle)
→ 代码检出 → 依赖安装 → 构建
→ 签名 → 发布到 GitHub Releases
```

---

## 二、今日踩坑清单与解决方案

### 1. Workflow 语法错误：secrets 不能直接用在 step 的 if 条件中

**现象**
```yaml
- name: Decode keystore
  if: secrets.SIGNING_KEY != ''   # ❌ 语法错误
  run: ...
```

**原因**
GitHub Actions 中，`secrets` 上下文只能用在 `env` 和 `with` 中，不能直接用于 `if` 条件判断。

**解决方案**
通过 `env` 中转，在 `if` 中判断 `env` 变量：

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      SIGNING_KEY: ${{ secrets.SIGNING_KEY }}    # 中转到 env
    steps:
      - name: Decode keystore
        if: env.SIGNING_KEY != ''                 # ✅ 用 env 判断
        run: echo "$SIGNING_KEY" | base64 --decode > app/release.jks
```

---

### 2. Node.js 版本不足（Capacitor 项目）

**现象**
Capacitor CLI 要求 Node >= 22，默认 ubuntu-latest 的 Node 20 报错。

**解决方案**
```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: 22
    cache: 'npm'
```

---

### 3. JDK 版本不足

**现象**
- AGP 8.5+ 建议 JDK 21
- Capacitor Android 最新版要求 Java 21
- JDK 17 构建时出现版本兼容错误

**解决方案**
统一使用 JDK 21：

```yaml
- name: Set up JDK 21
  uses: actions/setup-java@v4
  with:
    java-version: '21'
    distribution: 'temurin'
```

> AGP 8.x 最低 JDK 17，JDK 21 向下兼容，建议新项目直接用 21。

---

### 4. 签名密钥 base64 编码无效

**现象**
```
error: error loading keystore
base64: invalid input
```

**原因**
Windows PowerShell 生成 base64 时可能带 BOM 或换行格式问题，或复制时截断。

**正确生成方式（PowerShell）**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("D:\path\to\release.jks")) | Set-Clipboard
```

**验证方法**
```bash
# 在 Linux / CI 中验证
echo "$SIGNING_KEY" | base64 --decode | keytool -list -v -keystore /dev/stdin -storepass $KEYSTORE_PASSWORD
```

**GitHub Secrets 配置**
- 名称：`SIGNING_KEY`（或 `KEYSTORE_BASE64`）
- 值：base64 字符串（一整串，无换行）
- 配套 secrets：`KEYSTORE_PASSWORD`、`KEY_ALIAS`、`KEY_PASSWORD`

---

### 5. 资源文件被误存为 base64 文本（PNG 图标损坏）

**现象**
```
AAPT: error: failed to parse PNG
```
构建时 Android 资源文件中的 PNG 图标无法解析。

**原因**
PNG 文件被误保存为 base64 文本内容，而非二进制文件。

**解决方案**
- 删除损坏的 PNG 文件
- 使用 XML 矢量图标替代（drawable XML）
- 或恢复正确的二进制 PNG 文件

---

### 6. R.drawable 引用语法错误

**现象**
```java
// ❌ 错误：用了斜杠
R.drawable/ic_stat_notify

// ✅ 正确：用点号
R.drawable.ic_stat_notify
```

**原因**
混淆了 XML 资源引用（`@drawable/xxx`）和 Java/Kotlin 代码引用（`R.drawable.xxx`）的语法。

---

### 7. GitHub 网络连接不稳定（国内环境）

**现象**
```
fatal: unable to access '...': Recv failure: Connection was reset
fatal: unable to access '...': Failed to connect to github.com:443
```

**原因**
国内网络对 GitHub 的间歇性屏蔽。

**解决方案**
- 多次重试推送（间隔 5-10 秒）
- 使用代理或镜像加速
- 使用 SSH 而非 HTTPS
- Gitee 作为国内镜像仓库

---

## 三、标准 Workflow 模板

### 模板 A：Capacitor + Web 项目（应用 A型）

文件路径：`.github/workflows/release.yml`

```yaml
name: Build & Release APK

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      SIGNING_KEY: ${{ secrets.SIGNING_KEY }}
      KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
      KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
      KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js 22
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build JS bundle
        run: npm run build

      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'

      - name: Decode keystore
        if: env.SIGNING_KEY != ''
        run: |
          mkdir -p android/app
          echo "$SIGNING_KEY" | base64 --decode > android/app/release.jks

      - name: Create keystore.properties
        if: env.KEYSTORE_PASSWORD != ''
        run: |
          cat > android/keystore.properties << EOF
          storeFile=release.jks
          storePassword=$KEYSTORE_PASSWORD
          keyAlias=$KEY_ALIAS
          keyPassword=$KEY_PASSWORD
          EOF

      - name: Create local.properties
        run: |
          cat > android/local.properties << EOF
          sdk.dir=$ANDROID_HOME
          EOF

      - name: Sync Capacitor
        run: npx cap sync android

      - name: Build release APK
        run: |
          cd android
          chmod +x gradlew
          ./gradlew assembleRelease

      - name: Upload APK to Release
        uses: softprops/action-gh-release@v2
        with:
          files: android/app/build/outputs/apk/release/app-release.apk
          generate_release_notes: true
```

### 模板 B：原生 Android 项目（应用 B 型）

文件路径：`.github/workflows/release.yml`

```yaml
name: Build & Release APK

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      KEYSTORE_BASE64: ${{ secrets.KEYSTORE_BASE64 }}
      KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
      KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
      KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3

      - name: Decode keystore
        if: env.KEYSTORE_BASE64 != ''
        run: |
          echo "$KEYSTORE_BASE64" | base64 --decode > app/earthpulse.keystore

      - name: Build Release APK
        env:
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
        run: ./gradlew assembleRelease

      - name: Upload APK to Release
        uses: softprops/action-gh-release@v2
        with:
          files: app/build/outputs/apk/release/app-release.apk
          generate_release_notes: true
```

---

## 四、发布操作步骤

### 标准发版流程

```bash
# 1. 确保代码已提交
git status
git add .
git commit -m "feat: xxx"

# 2. 打标签（语义化版本）
git tag v1.4.2

# 3. 推送代码和标签
git push origin master
git push origin v1.4.2

# 4. 查看构建状态
# 打开 GitHub → Actions → 查看对应 workflow
```

### 删除错误标签并重新打标

```bash
# 删除本地标签
git tag -d v1.4.1

# 删除远程标签
git push origin :refs/tags/v1.4.1

# 重新打标签
git tag v1.4.2
git push origin v1.4.2
```

---

## 五、所需 GitHub Secrets 清单

| Secret 名称 | 说明 | 示例 / 来源 |
|------------|------|-------------|
| `SIGNING_KEY` | keystore 文件的 base64 编码 | PowerShell 生成 |
| `KEYSTORE_PASSWORD` | 密钥库密码 | 自定义 |
| `KEY_ALIAS` | 密钥别名 | 自定义，如 `release` |
| `KEY_PASSWORD` | 密钥密码 | 自定义（通常与库密码相同） |
| `KEYSTORE_BASE64` | 别名，同 SIGNING_KEY | 应用 B 项目用此名 |

---

## 六、构建失败排查顺序

1. **检查 Runner 日志** → 看第一个红色错误行
2. **环境版本** → Node / JDK / Gradle 版本是否匹配
3. **签名配置** → base64 是否有效、密码是否正确
4. **资源文件** → PNG 是否损坏、drawable 引用语法
5. **依赖缓存** → 清缓存重试（`actions/cache` 问题）
6. **网络问题** → 国内访问 GitHub 不稳定，多试几次

---

## 七、版本号规范

- **versionCode**：整数，每次发版 +1
- **versionName**：语义化版本 `主.次.修订`（如 `1.4.2`）
- **Git Tag**：`v` + versionName（如 `v1.4.2`）

```
versionCode  1  → versionName 1.0.0  → tag v1.0.0
versionCode  2  → versionName 1.1.0  → tag v1.1.0
versionCode  3  → versionName 1.3.0  → tag v1.3.0
versionCode  4  → versionName 1.4.2  → tag v1.4.2
```
