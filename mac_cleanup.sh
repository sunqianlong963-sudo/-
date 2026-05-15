#!/bin/bash

# Mac 系统全面清理脚本
# 运行方式：chmod +x mac_cleanup.sh && ./mac_cleanup.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_section() { echo -e "\n${BLUE}==== $1 ====${NC}"; }
print_ok()      { echo -e "${GREEN}[✓]${NC} $1"; }
print_skip()    { echo -e "${YELLOW}[−]${NC} $1（跳过：$2）"; }
print_size()    { echo -e "    释放空间：${GREEN}$1${NC}"; }

du_mb() {
    if [ -d "$1" ] || [ -f "$1" ]; then
        du -sh "$1" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

total_before=$(df / | tail -1 | awk '{print $4}')

echo -e "${GREEN}"
echo "╔══════════════════════════════════╗"
echo "║      Mac 系统全面清理工具        ║"
echo "╚══════════════════════════════════╝"
echo -e "${NC}"

# ──────────────────────────────────────
# 1. 系统缓存 & 临时文件
# ──────────────────────────────────────
print_section "系统缓存 & 临时文件"

CACHES=(
    "$HOME/Library/Caches"
    "/Library/Caches"
    "/System/Library/Caches"
)
for dir in "${CACHES[@]}"; do
    if [ -d "$dir" ]; then
        sz=$(du_mb "$dir")
        rm -rf "${dir:?}"/* 2>/dev/null && print_ok "清理 $dir" && print_size "$sz" || true
    fi
done

# 临时文件
TMP_DIRS=("/tmp" "/private/tmp" "/private/var/tmp")
for dir in "${TMP_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        sz=$(du_mb "$dir")
        find "$dir" -mindepth 1 -maxdepth 1 -mtime +1 -exec rm -rf {} + 2>/dev/null && \
            print_ok "清理 $dir 中超过1天的临时文件" && print_size "$sz" || true
    fi
done

# ──────────────────────────────────────
# 2. 系统日志
# ──────────────────────────────────────
print_section "系统日志"

LOG_DIRS=(
    "$HOME/Library/Logs"
    "/Library/Logs"
    "/var/log"
)
for dir in "${LOG_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        sz=$(du_mb "$dir")
        find "$dir" -name "*.log" -mtime +7 -exec rm -f {} + 2>/dev/null && \
            find "$dir" -name "*.log.gz" -mtime +7 -exec rm -f {} + 2>/dev/null && \
            print_ok "清理 $dir 中超过7天的日志" && print_size "$sz" || true
    fi
done

# 崩溃报告
CRASH_DIRS=(
    "$HOME/Library/Logs/DiagnosticReports"
    "/Library/Logs/DiagnosticReports"
)
for dir in "${CRASH_DIRS[@]}"; do
    if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
        sz=$(du_mb "$dir")
        rm -rf "${dir:?}"/* 2>/dev/null && print_ok "清理崩溃报告 $dir" && print_size "$sz" || true
    fi
done

# ──────────────────────────────────────
# 3. 废纸篓
# ──────────────────────────────────────
print_section "废纸篓"

TRASH_DIRS=(
    "$HOME/.Trash"
)
# 查找挂载卷的废纸篓
while IFS= read -r vol; do
    trash="$vol/.Trashes/$UID"
    [ -d "$trash" ] && TRASH_DIRS+=("$trash")
done < <(ls /Volumes 2>/dev/null | awk '{print "/Volumes/"$0}')

for dir in "${TRASH_DIRS[@]}"; do
    if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
        sz=$(du_mb "$dir")
        rm -rf "${dir:?}"/* 2>/dev/null && print_ok "清空废纸篓 $dir" && print_size "$sz" || true
    fi
done

# ──────────────────────────────────────
# 4. Homebrew
# ──────────────────────────────────────
print_section "Homebrew"

if command -v brew &>/dev/null; then
    echo "  正在更新 Homebrew..."
    brew update --quiet 2>/dev/null && print_ok "brew update" || true

    echo "  正在清理过期包和缓存..."
    brew cleanup --prune=all 2>/dev/null && print_ok "brew cleanup --prune=all" || true

    echo "  正在移除孤立依赖..."
    brew autoremove 2>/dev/null && print_ok "brew autoremove" || true

    BREW_CACHE=$(brew --cache 2>/dev/null)
    if [ -d "$BREW_CACHE" ]; then
        sz=$(du_mb "$BREW_CACHE")
        rm -rf "${BREW_CACHE:?}"/* 2>/dev/null && print_ok "清理 Homebrew 缓存目录" && print_size "$sz" || true
    fi
else
    print_skip "Homebrew" "未安装"
fi

# ──────────────────────────────────────
# 5. npm / Node.js
# ──────────────────────────────────────
print_section "npm / Node.js"

if command -v npm &>/dev/null; then
    NPM_CACHE=$(npm config get cache 2>/dev/null)
    if [ -d "$NPM_CACHE" ]; then
        sz=$(du_mb "$NPM_CACHE")
        npm cache clean --force 2>/dev/null && print_ok "npm cache clean" && print_size "$sz" || true
    fi
else
    print_skip "npm" "未安装"
fi

if command -v yarn &>/dev/null; then
    YARN_CACHE=$(yarn cache dir 2>/dev/null)
    if [ -d "$YARN_CACHE" ]; then
        sz=$(du_mb "$YARN_CACHE")
        yarn cache clean 2>/dev/null && print_ok "yarn cache clean" && print_size "$sz" || true
    fi
else
    print_skip "yarn" "未安装"
fi

if command -v pnpm &>/dev/null; then
    sz=$(pnpm store path 2>/dev/null | xargs du_mb 2>/dev/null || echo "?")
    pnpm store prune 2>/dev/null && print_ok "pnpm store prune" && print_size "$sz" || true
else
    print_skip "pnpm" "未安装"
fi

# ──────────────────────────────────────
# 6. Python / pip
# ──────────────────────────────────────
print_section "Python / pip"

PIP_CACHE="$HOME/Library/Caches/pip"
if [ -d "$PIP_CACHE" ]; then
    sz=$(du_mb "$PIP_CACHE")
    if command -v pip3 &>/dev/null; then
        pip3 cache purge 2>/dev/null && print_ok "pip3 cache purge" && print_size "$sz" || true
    elif command -v pip &>/dev/null; then
        pip cache purge 2>/dev/null && print_ok "pip cache purge" && print_size "$sz" || true
    else
        rm -rf "${PIP_CACHE:?}"/* 2>/dev/null && print_ok "清理 pip 缓存目录" && print_size "$sz" || true
    fi
else
    print_skip "pip 缓存" "目录不存在"
fi

# Pyenv / virtualenv 缓存
PYENV_CACHE="$HOME/.pyenv/cache"
if [ -d "$PYENV_CACHE" ] && [ "$(ls -A "$PYENV_CACHE" 2>/dev/null)" ]; then
    sz=$(du_mb "$PYENV_CACHE")
    rm -rf "${PYENV_CACHE:?}"/* 2>/dev/null && print_ok "清理 pyenv 下载缓存" && print_size "$sz" || true
fi

# ──────────────────────────────────────
# 7. Maven / Gradle / Java
# ──────────────────────────────────────
print_section "Maven / Gradle / Java"

MAVEN_REPO="$HOME/.m2/repository"
if [ -d "$MAVEN_REPO" ]; then
    sz=$(du_mb "$MAVEN_REPO")
    find "$MAVEN_REPO" -name "*.lastUpdated" -exec rm -f {} + 2>/dev/null && \
        print_ok "清理 Maven .lastUpdated 文件" && print_size "$sz" || true
else
    print_skip "Maven" "~/.m2 不存在"
fi

GRADLE_CACHE="$HOME/.gradle/caches"
if [ -d "$GRADLE_CACHE" ]; then
    sz=$(du_mb "$GRADLE_CACHE")
    find "$GRADLE_CACHE" -mindepth 1 -maxdepth 1 -mtime +30 -exec rm -rf {} + 2>/dev/null && \
        print_ok "清理30天前的 Gradle 缓存" && print_size "$sz" || true
else
    print_skip "Gradle" "~/.gradle/caches 不存在"
fi

# ──────────────────────────────────────
# 8. Docker
# ──────────────────────────────────────
print_section "Docker"

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    echo "  正在清理 Docker（停止的容器、悬空镜像、未使用网络和卷）..."
    docker system prune -f 2>/dev/null && print_ok "docker system prune" || true
    docker volume prune -f 2>/dev/null && print_ok "docker volume prune" || true
else
    print_skip "Docker" "未安装或 Docker 守护进程未运行"
fi

# ──────────────────────────────────────
# 9. Xcode / iOS 开发
# ──────────────────────────────────────
print_section "Xcode / iOS 开发"

XCODE_DIRS=(
    "$HOME/Library/Developer/Xcode/DerivedData"
    "$HOME/Library/Developer/Xcode/Archives"
    "$HOME/Library/Developer/Xcode/iOS DeviceSupport"
    "$HOME/Library/Developer/CoreSimulator/Caches"
)
for dir in "${XCODE_DIRS[@]}"; do
    if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
        sz=$(du_mb "$dir")
        rm -rf "${dir:?}"/* 2>/dev/null && print_ok "清理 $dir" && print_size "$sz" || true
    else
        print_skip "$dir" "不存在或为空"
    fi
done

# CocoaPods 缓存
PODS_CACHE="$HOME/Library/Caches/CocoaPods"
if [ -d "$PODS_CACHE" ]; then
    sz=$(du_mb "$PODS_CACHE")
    rm -rf "${PODS_CACHE:?}"/* 2>/dev/null && print_ok "清理 CocoaPods 缓存" && print_size "$sz" || true
fi

# ──────────────────────────────────────
# 10. Go 模块缓存
# ──────────────────────────────────────
print_section "Go"

if command -v go &>/dev/null; then
    GO_CACHE=$(go env GOCACHE 2>/dev/null)
    if [ -d "$GO_CACHE" ]; then
        sz=$(du_mb "$GO_CACHE")
        go clean -cache 2>/dev/null && print_ok "go clean -cache" && print_size "$sz" || true
    fi
    GO_MOD_CACHE=$(go env GOMODCACHE 2>/dev/null)
    if [ -d "$GO_MOD_CACHE" ]; then
        sz=$(du_mb "$GO_MOD_CACHE")
        go clean -modcache 2>/dev/null && print_ok "go clean -modcache" && print_size "$sz" || true
    fi
else
    print_skip "Go" "未安装"
fi

# ──────────────────────────────────────
# 11. Rust / Cargo
# ──────────────────────────────────────
print_section "Rust / Cargo"

CARGO_REGISTRY="$HOME/.cargo/registry"
CARGO_GIT="$HOME/.cargo/git"
for dir in "$CARGO_REGISTRY" "$CARGO_GIT"; do
    if [ -d "$dir" ]; then
        sz=$(du_mb "$dir")
        rm -rf "${dir:?}" 2>/dev/null && print_ok "清理 $dir" && print_size "$sz" || true
    fi
done
if ! [ -d "$CARGO_REGISTRY" ] && ! [ -d "$CARGO_GIT" ]; then
    print_skip "Cargo 缓存" "目录不存在"
fi

# ──────────────────────────────────────
# 12. DNS 缓存刷新
# ──────────────────────────────────────
print_section "DNS 缓存"

sudo dscacheutil -flushcache 2>/dev/null && \
    sudo killall -HUP mDNSResponder 2>/dev/null && \
    print_ok "DNS 缓存已刷新" || print_skip "DNS 缓存" "需要 sudo 权限"

# ──────────────────────────────────────
# 汇总
# ──────────────────────────────────────
total_after=$(df / | tail -1 | awk '{print $4}')
freed=$(( (total_after - total_before) / 2048 ))  # KB → MB

echo -e "\n${GREEN}╔══════════════════════════════════╗"
echo    "║           清理完成！             ║"
printf  "║  约释放磁盘空间：%-6s MB       ║\n" "$freed"
echo    "╚══════════════════════════════════╝"
echo -e "${NC}"
echo "建议：重启 Mac 后效果更佳。"
