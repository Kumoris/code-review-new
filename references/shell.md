# Shell 检视规则

> 来源：既有检视规则；规则与代码托管平台无关

---

## 目录

- [一、健壮性与错误处理](#一健壮性与错误处理)
  - [SH-ROBUST-001: 脚本严格模式](#sh-robust-001-脚本严格模式)
  - [SH-ROBUST-002: 路径与执行上下文独立性](#sh-robust-002-路径与执行上下文独立性)
  - [SH-ROBUST-003: 错误处理与返回值](#sh-robust-003-错误处理与返回值)
  - [SH-ROBUST-004: 资源清理](#sh-robust-004-资源清理)
  - [SH-ROBUST-005: 正则表达式陷阱](#sh-robust-005-正则表达式陷阱)
- [二、可移植性与兼容性](#二可移植性与兼容性)
  - [SH-PORT-001: Shebang（解释器声明）](#sh-port-001-shebang解释器声明)
  - [SH-PORT-002: 命令与参数的兼容性](#sh-port-002-命令与参数的兼容性)
- [三、代码风格与可读性](#三代码风格与可读性)
  - [SH-STYLE-001: 变量处理](#sh-style-001-变量处理)
  - [SH-STYLE-002: 结构与组织](#sh-style-002-结构与组织)
  - [SH-STYLE-003: 代码简洁性](#sh-style-003-代码简洁性)
  - [SH-STYLE-004: 日志规范](#sh-style-004-日志规范)
- [四、安全编码](#四安全编码)
  - [SH-SEC-001: 高危命令审查](#sh-sec-001-高危命令审查)
  - [SH-SEC-002: 依赖项获取方式审查](#sh-sec-002-依赖项获取方式审查)
  - [SH-SEC-003: 命令注入风险](#sh-sec-003-命令注入风险)
  - [SH-SEC-004: 临时文件安全](#sh-sec-004-临时文件安全)
  - [SH-SEC-005: 敏感信息防泄漏](#sh-sec-005-敏感信息防泄漏)
- [五、性能与资源管理](#五性能与资源管理)
  - [SH-PERF-001: 避免不必要的子Shell](#sh-perf-001-避免不必要的子shell)
  - [SH-PERF-002: 文件读取效率](#sh-perf-002-文件读取效率)
  - [SH-PERF-003: 命令调用开销](#sh-perf-003-命令调用开销)
- [六、静态分析与测试](#六静态分析与测试)
  - [SH-TEST-001: 静态代码检查](#sh-test-001-静态代码检查)
  - [SH-TEST-002: 测试覆盖度](#sh-test-002-测试覆盖度)

---

## 一、健壮性与错误处理

### SH-ROBUST-001: 脚本严格模式

- **检查锚点**: 脚本开头缺少 `set -euo pipefail`，缺少 `IFS=$'\n\t'`
- **反例**:
  ```bash
  #!/bin/bash
  # 无 set -euo pipefail，无 IFS 设置
  rm -rf $undefined_path
  ```
- **正例**:
  ```bash
  #!/bin/bash
  set -euo pipefail
  IFS=$'\n\t'
  ```
- **触发条件**: `.sh`文件开头缺少`set -euo pipefail`或`IFS=$'\n\t'`
- **严重程度**: major

### SH-ROBUST-002: 路径与执行上下文独立性

- **检查锚点**: 使用相对路径引用文件且未基于 `SCRIPT_DIR`，使用外部命令前未通过 `command -v` 校验
- **反例**:
  ```bash
  # 路径依赖CWD，外部命令未校验
  source ./config.sh
  jq '.key' data.json
  ```
- **正例**:
  ```bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  source "${SCRIPT_DIR}/config.sh"

  command -v jq >/dev/null 2>&1 || { echo "jq is required but not installed." >&2; exit 1; }
  jq '.key' data.json
  ```
- **触发条件**: 脚本中使用相对路径`./`引用文件，或调用外部命令前无`command -v`校验
- **严重程度**: major

### SH-ROBUST-003: 错误处理与返回值

- **检查锚点**: 关键命令返回值未检查，错误信息未重定向到 `>&2`，退出码不明确
- **反例**:
  ```bash
  mkdir /opt/app
  echo "Failed to create directory"
  exit
  ```
- **正例**:
  ```bash
  if ! mkdir /opt/app; then
    echo "Failed to create directory" >&2
    exit 1
  fi
  ```
- **触发条件**: 关键命令（mkdir/cp/mv等）返回值未检查，或错误输出未重定向到`>&2`
- **严重程度**: major

### SH-ROBUST-004: 资源清理

- **检查锚点**: 缺少 `trap` 信号捕获，临时资源无清理机制
- **反例**:
  ```bash
  #!/bin/bash
  TEMP_DIR=$(mktemp -d)
  # 无 trap，异常退出时 TEMP_DIR 不会被清理
  do_something
  rm -rf "$TEMP_DIR"
  ```
- **正例**:
  ```bash
  #!/bin/bash
  TEMP_DIR=$(mktemp -d)

  cleanup() {
    rm -rf "$TEMP_DIR"
  }
  trap cleanup EXIT ERR INT TERM

  do_something
  ```
- **触发条件**: 创建临时文件/目录后缺少`trap`信号捕获清理机制
- **严重程度**: minor

### SH-ROBUST-005: 正则表达式陷阱

- **检查锚点**: `grep`/`sed`/`awk` 间正则语法混用，缺少 `^`/`$` 边界定位，固定字符串匹配未使用 `grep -F`
- **反例**:
  ```bash
  # 边界未限定，匹配到 "myapp_old"；固定字符串未用 -F
  grep "myapp" file.txt
  grep "10.0.0.1" hosts.txt
  ```
- **正例**:
  ```bash
  # 精确边界匹配
  grep "^myapp$" file.txt
  # 固定字符串匹配使用 -F，避免 . 被当作正则通配符
  grep -F "10.0.0.1" hosts.txt
  ```
- **触发条件**: `grep`/`sed`/`awk`中正则缺少`^`/`$`边界，固定字符串未使用`grep -F`
- **严重程度**: minor

---

## 二、可移植性与兼容性

### SH-PORT-001: Shebang（解释器声明）

- **检查锚点**: 使用 `#!/bin/sh` 但脚本中包含 Bash 特有语法（`[[`, `$BASH_SOURCE`, `${var//pattern/replacement}` 等）
- **反例**:
  ```sh
  #!/bin/sh
  # 使用了 Bash 特有语法 [[ ]]
  if [[ -z "$VAR" ]]; then
    echo "empty"
  fi
  ```
- **正例**:
  ```bash
  #!/bin/bash
  if [[ -z "$VAR" ]]; then
    echo "empty"
  fi
  ```
  或严格 POSIX 兼容：
  ```sh
  #!/bin/sh
  if [ -z "$VAR" ]; then
    echo "empty"
  fi
  ```
- **触发条件**: `#!/bin/sh`声明但脚本中使用了`[[`、`$BASH_SOURCE`等Bash特有语法
- **严重程度**: major

### SH-PORT-002: 命令与参数的兼容性

- **检查锚点**: 使用非 POSIX 标准命令参数如 `sed -i`, `stat`, `date +%s`, `readlink -f`，`ps`/`top` 输出宽度未处理
- **反例**:
  ```bash
  # sed -i 在 macOS 上需要指定备份后缀
  sed -i 's/old/new/g' file.txt
  # readlink -f 在 macOS 上不可用
  REAL_PATH=$(readlink -f "$0")
  ```
- **正例**:
  ```bash
  # 兼容 macOS 和 Linux 的 sed -i
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' 's/old/new/g' file.txt
  else
    sed -i 's/old/new/g' file.txt
  fi
  # 使用 realpath 或兼容方案替代 readlink -f
  REAL_PATH=$(python3 -c "import os; print(os.path.realpath('$0'))")
  ```
- **触发条件**: 使用`sed -i`、`readlink -f`、`date +%s`等非POSIX标准命令参数
- **严重程度**: minor

---

## 三、代码风格与可读性

### SH-STYLE-001: 变量处理

- **检查锚点**: 变量引用未加双引号，全局变量未用大写，函数内变量未用 `local` 声明
- **反例**:
  ```bash
  name=$1
  result=$(grep $pattern $file)
  config_path=/etc/app.conf

  process() {
    temp_file=$(mktemp)
    cat "$1" > "$temp_file"
  }
  ```
- **正例**:
  ```bash
  name="$1"
  result=$(grep "$pattern" "$file")
  CONFIG_PATH="/etc/app.conf"

  process() {
    local temp_file
    temp_file=$(mktemp)
    cat "$1" > "$temp_file"
  }
  ```
- **触发条件**: `.sh`文件中使用未加双引号的`$VAR`变量扩展，或函数内缺少`local`声明
- **严重程度**: minor

### SH-STYLE-002: 结构与组织

- **检查锚点**: 脚本无 `main` 函数入口，核心逻辑散落在全局作用域，参数解析未使用 `getopts`
- **反例**:
  ```bash
  #!/bin/bash
  # 全部逻辑在全局作用域，参数手动解析
  if [ "$1" = "-v" ]; then
    VERBOSE=1
  fi
  do_setup
  do_work
  ```
- **正例**:
  ```bash
  #!/bin/bash
  set -euo pipefail

  main() {
    local verbose=0
    while getopts "v" opt; do
      case "$opt" in
        v) verbose=1 ;;
        *) echo "Usage: $0 [-v]" >&2; exit 1 ;;
      esac
    done

    do_setup
    do_work
  }

  main "$@"
  ```
- **触发条件**: 脚本无`main`函数入口，核心逻辑在全局作用域，参数未用`getopts`解析
- **严重程度**: suggestion

### SH-STYLE-003: 代码简洁性

- **检查锚点**: 使用反引号 `` `command` `` 替代 `$()`，使用 `[ ... ]` 替代 `[[ ... ]]`，解析 `ls` 命令输出
- **反例**:
  ```bash
  result=`date +%Y%m%d`
  if [ -f "$file" ]; then ...
  for f in $(ls *.txt); do ...
  ```
- **正例**:
  ```bash
  result=$(date +%Y%m%d)
  if [[ -f "$file" ]]; then ...
  for f in *.txt; do ...
  # 或使用 mapfile
  mapfile -t files < <(find . -name "*.txt" -type f)
  ```
- **触发条件**: 使用反引号`` `command` ``替代`$()`，或`for f in $(ls)`解析ls输出
- **严重程度**: suggestion

### SH-STYLE-004: 日志规范

- **检查锚点**: 缺少日志函数定义，日志缺少时间戳/级别/脚本名与行号，错误输出未记录到日志文件
- **反例**:
  ```bash
  echo "Starting backup..."
  echo "Error: disk full"
  ```
- **正例**:
  ```bash
  LOG_FILE="/var/log/backup.log"

  log_info()  { echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO]  [${BASH_SOURCE[0]}:${LINENO}] $*" | tee -a "$LOG_FILE"; }
  log_error() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] [${BASH_SOURCE[0]}:${LINENO}] $*" | tee -a "$LOG_FILE" >&2; }

  log_info "Starting backup..."
  log_error "Error: disk full"
  ```
- **触发条件**: 脚本中直接`echo`输出日志，缺少时间戳/级别/脚本名行号
- **严重程度**: suggestion

---

## 四、安全编码

### SH-SEC-001: 高危命令审查

- **检查锚点**: `rm -rf`, `mv`, `dd`, `chown`, `chmod` 等破坏性操作前无防御性检查，使用 `eval`
- **反例**:
  ```bash
  rm -rf "$TARGET_DIR"
  eval "$USER_CMD"
  ```
- **正例**:
  ```bash
  # 删除前校验路径非空
  if [[ -n "$TARGET_DIR" && "$TARGET_DIR" != "/" ]]; then
    rm -rf "$TARGET_DIR"
  fi
  # 避免 eval，使用更安全的替代方案
  case "$action" in
    start) start_service ;;
    stop)  stop_service  ;;
    *)     echo "Unknown action: $action" >&2; exit 1 ;;
  esac
  ```
- **触发条件**: `rm -rf`后跟变量路径，或使用`eval`执行动态命令
- **严重程度**: fatal

### SH-SEC-002: 依赖项获取方式审查

- **检查锚点**: `curl ... | sh`, `wget ... -O /usr/local/bin/tool && chmod +x` 等直接下载并执行二进制文件的模式
- **反例**:
  ```bash
  curl -fsSL https://example.com/install.sh | sh
  wget https://example.com/binary -O /usr/local/bin/tool
  chmod +x /usr/local/bin/tool
  ```
- **正例**:
  ```bash
  # 从经过审核的源码编译安装
  git clone https://verified-repo.example.com/tool.git
  cd tool
  git verify-tag v1.2.3
  make && make install
  ```
- **触发条件**: `curl ... | sh`或`wget ... -O`直接下载并执行远程脚本/二进制
- **严重程度**: fatal

### SH-SEC-003: 命令注入风险

- **检查锚点**: 命令字符串中拼接未校验/未引用的变量，外部输入未做白名单校验
- **反例**:
  ```bash
  # 用户输入直接拼入命令，可注入
  eval "ssh $USER_INPUT@$HOST"
  rm -rf "/data/$USER_INPUT"
  ```
- **正例**:
  ```bash
  # 白名单校验后再使用
  if [[ ! "$USER_INPUT" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Invalid input" >&2
    exit 1
  fi
  ssh "${USER_INPUT}@${HOST}"
  ```
- **触发条件**: `eval`/`rm -rf`/`ssh`等命令中拼接未校验的外部输入变量
- **严重程度**: fatal

### SH-SEC-004: 临时文件安全

- **检查锚点**: 在 `/tmp` 下硬编码可预测的临时文件名，未使用 `mktemp`
- **反例**:
  ```bash
  TEMP_FILE="/tmp/myapp_$$.tmp"
  echo "data" > "$TEMP_FILE"
  ```
- **正例**:
  ```bash
  TEMP_FILE=$(mktemp)
  echo "data" > "$TEMP_FILE"
  ```
- **触发条件**: 在`/tmp`下硬编码可预测的临时文件名，未使用`mktemp`
- **严重程度**: major

### SH-SEC-005: 敏感信息防泄漏

- **检查锚点**: 脚本中硬编码密码/API密钥/Token，`set -x` 输出包含敏感信息
- **反例**:
  ```bash
  DB_PASSWORD="P@ssw0rd123"
  API_KEY="sk-abc123def456"
  set -x
  curl -H "Authorization: Bearer $API_KEY" https://api.example.com
  ```
- **正例**:
  ```bash
  # 从环境变量或密钥管理服务获取
  DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"
  API_KEY="${API_KEY:?API_KEY is required}"
  # 调试时屏蔽敏感变量
  set -x
  curl -H "Authorization: Bearer ***" https://api.example.com
  set +x
  ```
- **触发条件**: 脚本中硬编码密码/API密钥/Token，或`set -x`输出包含敏感信息
- **严重程度**: fatal

---

## 五、性能与资源管理

### SH-PERF-001: 避免不必要的子Shell

- **检查锚点**: `command | while read -r line; do ... done` 管道导致循环在子Shell中执行
- **反例**:
  ```bash
  cat items.txt | while read -r item; do
    count=$((count + 1))
  done
  echo "$count"  # 输出为空，子Shell中修改的变量无法传出
  ```
- **正例**:
  ```bash
  while read -r item; do
    count=$((count + 1))
  done < <(cat items.txt)
  echo "$count"  # 正确输出计数
  ```
- **触发条件**: `command | while read`管道导致循环在子Shell中执行，变量无法传出
- **严重程度**: minor

### SH-PERF-002: 文件读取效率

- **检查锚点**: 使用 `for line in $(cat file)` 逐行读取文件
- **反例**:
  ```bash
  for line in $(cat data.txt); do
    echo "$line"
  done
  ```
- **正例**:
  ```bash
  while IFS= read -r line; do
    echo "$line"
  done < data.txt
  ```
- **触发条件**: `for line in $(cat file)`逐行读取文件，依赖IFS分词
- **严重程度**: minor

### SH-PERF-003: 命令调用开销

- **检查锚点**: 循环内反复调用外部命令（`sed`, `awk`, `grep`），字符串操作使用外部命令代替Shell内建参数扩展
- **反例**:
  ```bash
  for f in *.txt; do
    basename=$(basename "$f" .txt)
    upper=$(echo "$basename" | tr '[:lower:]' '[:upper:]')
    echo "$upper"
  done
  ```
- **正例**:
  ```bash
  for f in *.txt; do
    basename="${f%.txt}"
    upper="${basename^^}"
    echo "$upper"
  done
  ```
- **触发条件**: 循环内反复调用`sed`/`awk`/`grep`/`tr`/`basename`等外部命令
- **严重程度**: minor

---

## 六、静态分析与测试

### SH-TEST-001: 静态代码检查

- **检查锚点**: 脚本未通过 `shellcheck` 检查，CI流程中未集成 `shellcheck`
- **反例**:
  ```bash
  # 无 shellcheck 配置，无 CI 集成
  #!/bin/bash
  echo $1
  ```
- **正例**:
  ```bash
  # ShellCheck 通过，CI 集成
  #!/bin/bash
  # shellcheck enable=all
  echo "$1"
  ```
  CI 集成示例：
  ```yaml
  # .gitlab-ci.yml
  shellcheck:
    stage: test
    script:
      - shellcheck -x **/*.sh
  ```
- **触发条件**: `.sh`文件未通过`shellcheck`检查，CI流程未集成`shellcheck`
- **严重程度**: minor

### SH-TEST-002: 测试覆盖度

- **检查锚点**: 脚本仅在单一环境（如交互式终端）验证，未覆盖 cron/CI/后台等执行场景，未在不同OS/CPU架构上测试
- **反例**:
  ```bash
  # 仅在本地交互式终端手动测试过
  ./deploy.sh
  ```
- **正例**:
  ```bash
  # 测试矩阵覆盖多场景
  # - 交互式终端执行
  # - cron 定时执行
  # - CI 流水线执行
  # - 目标 OS: CentOS 7, Ubuntu 20.04, macOS
  # - 目标架构: x86_64, aarch64
  bats tests/deploy.bats
  ```
- **触发条件**: 脚本仅在交互式终端测试，未覆盖cron/CI/后台及多OS架构场景
- **严重程度**: suggestion
