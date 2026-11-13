#!/usr/bin/env bash
# ==============================================================================
# GameScout AI — Yerel Geliştirme Araçları ve Uygulama Kurulum Betiği (macOS ARM64)
#
# Bu betik, sistem genelinde (global) değişiklik veya `sudo` gerektirmeden eksik
# geliştirme araçlarını `.orchestra/tools/` dizinine indirir ve ön yüz / arka uç
# uygulamalarının bağımlılık ile doğrulama adımlarını çalıştırır.
#
# Kullanım:
#   bash scripts/setup_dev_tools.sh --check
#   bash scripts/setup_dev_tools.sh --install-tools
#   bash scripts/setup_dev_tools.sh --setup-apps
# ==============================================================================

set -euo pipefail

# Çalışma alanı kök dizinini belirle (mutlak yol)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TOOLS_ROOT="${WORKSPACE_ROOT}/.orchestra/tools"
TOOLS_BIN="${TOOLS_ROOT}/bin"
NODE_ROOT="${TOOLS_ROOT}/node"
NODE_BIN="${NODE_ROOT}/bin"

FRONTEND_DIR="${WORKSPACE_ROOT}/GameScout-AI-Fronted"
BACKEND_DIR="${WORKSPACE_ROOT}/GameScout-AI-Backend"

NODE_VERSION="v22.14.0"
NODE_TARBALL="node-${NODE_VERSION}-darwin-arm64.tar.gz"
NODE_URL="https://nodejs.org/dist/${NODE_VERSION}/${NODE_TARBALL}"

PHP_STATIC_URL="https://dl.static-php.dev/static-php-cli/common/php-8.3.17-cli-macos-aarch64.tar.gz"
COMPOSER_URL="https://getcomposer.org/download/latest-stable/composer.phar"
OLLAMA_URL="https://ollama.com/download/ollama-darwin.tgz"
OLLAMA_MODEL="qwen2.5:3b"
OLLAMA_MODELS_DIR="${TOOLS_ROOT}/ollama/models"

# Yerel araç dizinlerini PATH'in başına ekle ve Ollama çalışma alanı ortamını ayarla
export PATH="${TOOLS_BIN}:${NODE_BIN}:/opt/homebrew/bin:${PATH}"
export OLLAMA_HOST="127.0.0.1:11434"
export OLLAMA_MODELS="${OLLAMA_MODELS_DIR}"

log_info() {
  printf "[BİLGİ] %s\n" "$1"
}

log_warn() {
  printf "[UYARI] %s\n" "$1" >&2
}

log_error() {
  printf "[HATA] %s\n" "$1" >&2
}

usage() {
  cat <<EOF
Kullanım: bash scripts/setup_dev_tools.sh [SEÇENEK]

Seçenekler:
  --check          Araçların (node, npm, php, composer, psql, python3, sqlite3, ollama)
                   mevcudiyetini çevrimdışı kontrol eder ve 0 koduyla çıkar.
  --install-tools  Eksik taşınabilir araçları (.orchestra/tools/) indirir ve kurar.
  --install-ollama Taşınabilir macOS Ollama ikilisini (.orchestra/tools/bin/ollama) kurar,
                   arka planda 'ollama serve' başlatır ve '${OLLAMA_MODEL}' modelini indirir.
  --setup-apps     Araçlar hazırsa Frontend ve Backend kurulum/test adımlarını çalıştırır.
  --serve-backend  Backend API sunucusunu 127.0.0.1:8000 üzerinde başlatır.
  --serve-frontend Frontend Vite geliştirme sunucusunu 127.0.0.1:5173 üzerinde başlatır.
  --serve          Varsa Ollama (127.0.0.1:11434), Backend (127.0.0.1:8000) ve
                   Frontend (127.0.0.1:5173) sunucularını tek komutla başlatır.
  --help, -h       Bu yardım metnini gösterir.
EOF
}

check_single_tool() {
  local tool_name="$1"
  local version_flag="${2:---version}"
  if command -v "${tool_name}" >/dev/null 2>&1; then
    local tool_path
    tool_path="$(command -v "${tool_name}")"
    local tool_ver
    tool_ver="$("${tool_name}" "${version_flag}" 2>&1 | head -n 1 || true)"
    printf "  [MEVCUT] %-10s -> %s (%s)\n" "${tool_name}" "${tool_path}" "${tool_ver}"
    return 0
  else
    printf "  [EKSİK]  %-10s -> bulunamadı\n" "${tool_name}"
    return 1
  fi
}

run_check() {
  log_info "Çalışma alanı: ${WORKSPACE_ROOT}"
  log_info "Yerel araç yolu (PATH öneki): ${TOOLS_BIN}:${NODE_BIN}"
  printf "\n--- Geliştirme Araçları Durumu ---\n"
  check_single_tool "node" "--version" || true
  check_single_tool "npm" "--version" || true
  check_single_tool "php" "--version" || true
  check_single_tool "composer" "--version" || true
  check_single_tool "psql" "--version" || true
  check_single_tool "python3" "--version" || true
  check_single_tool "sqlite3" "-version" || true
  check_single_tool "ollama" "--version" || true
  printf "%s\n" "----------------------------------"
  return 0
}

install_node_if_missing() {
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    log_info "Node.js ve npm zaten mevcut: $(command -v node)"
    return 0
  fi

  log_info "Node.js (${NODE_VERSION} darwin-arm64) indiriliyor: ${NODE_URL}"
  mkdir -p "${NODE_ROOT}" "${TOOLS_ROOT}/tmp"
  local archive_path="${TOOLS_ROOT}/tmp/${NODE_TARBALL}"

  curl -fL --retry 3 --connect-timeout 15 -o "${archive_path}" "${NODE_URL}"
  tar -xzf "${archive_path}" -C "${NODE_ROOT}" --strip-components=1
  rm -f "${archive_path}"

  if [[ ! -x "${NODE_BIN}/node" ]]; then
    log_error "Node.js kurulumu doğrulanamadı: ${NODE_BIN}/node bulunamadı."
    return 1
  fi
  log_info "Node.js başarıyla kuruldu: $("${NODE_BIN}/node" --version)"
}

install_php_if_missing() {
  if command -v php >/dev/null 2>&1; then
    log_info "PHP zaten mevcut: $(command -v php)"
    return 0
  fi

  mkdir -p "${TOOLS_BIN}" "${TOOLS_ROOT}/tmp"

  if [[ -x "/opt/homebrew/bin/php" ]]; then
    log_info "Homebrew PHP bulundu (/opt/homebrew/bin/php), sembolik bağ oluşturuluyor..."
    ln -sf "/opt/homebrew/bin/php" "${TOOLS_BIN}/php"
    return 0
  fi

  log_info "Taşınabilir PHP 8.3 CLI (macos-aarch64) indiriliyor: ${PHP_STATIC_URL}"
  local archive_path="${TOOLS_ROOT}/tmp/php-static-macos-aarch64.tar.gz"

  if curl -fL --retry 3 --connect-timeout 15 -o "${archive_path}" "${PHP_STATIC_URL}"; then
    tar -xzf "${archive_path}" -C "${TOOLS_BIN}"
    rm -f "${archive_path}"
    chmod +x "${TOOLS_BIN}/php"
  else
    log_error "Taşınabilir PHP indirilemedi. Lütfen internet bağlantınızı kontrol edin veya Homebrew ile 'brew install php' çalıştırın."
    return 1
  fi

  if [[ ! -x "${TOOLS_BIN}/php" ]]; then
    log_error "PHP kurulumu doğrulanamadı: ${TOOLS_BIN}/php bulunamadı."
    return 1
  fi
  log_info "PHP başarıyla kuruldu: $("${TOOLS_BIN}/php" --version | head -n 1)"
}

install_composer_if_missing() {
  if command -v composer >/dev/null 2>&1; then
    log_info "Composer zaten mevcut: $(command -v composer)"
    return 0
  fi

  if ! command -v php >/dev/null 2>&1; then
    log_error "Composer kurulumu için önce PHP gereklidir."
    return 1
  fi

  mkdir -p "${TOOLS_BIN}"
  log_info "Composer indiriliyor: ${COMPOSER_URL}"
  curl -fL --retry 3 --connect-timeout 15 -o "${TOOLS_BIN}/composer" "${COMPOSER_URL}"
  chmod +x "${TOOLS_BIN}/composer"

  if [[ ! -x "${TOOLS_BIN}/composer" ]]; then
    log_error "Composer kurulumu doğrulanamadı: ${TOOLS_BIN}/composer çalıştırılamıyor."
    return 1
  fi
  log_info "Composer başarıyla kuruldu: $("${TOOLS_BIN}/composer" --version | head -n 1)"
}

run_install_tools() {
  mkdir -p "${TOOLS_BIN}" "${NODE_ROOT}" "${TOOLS_ROOT}/tmp"
  install_node_if_missing
  install_php_if_missing
  install_composer_if_missing
  rmdir "${TOOLS_ROOT}/tmp" 2>/dev/null || true
  log_info "Tüm taşınabilir geliştirme araçları hazır."
  run_check
}

is_port_listening() {
  local port="$1"
  python3 -c "import socket; s = socket.create_connection(('127.0.0.1', ${port}), 1.0); s.close()" >/dev/null 2>&1
}

run_install_ollama() {
  mkdir -p "${TOOLS_BIN}" "${OLLAMA_MODELS_DIR}" "${TOOLS_ROOT}/tmp"

  if ! command -v ollama >/dev/null 2>&1; then
    log_info "Taşınabilir macOS Ollama indiriliyor: ${OLLAMA_URL}"
    local archive_path="${TOOLS_ROOT}/tmp/ollama-darwin.tgz"
    curl -fL --retry 3 --connect-timeout 15 -o "${archive_path}" "${OLLAMA_URL}"
    tar -xzf "${archive_path}" -C "${TOOLS_BIN}"
    rm -f "${archive_path}"
    chmod +x "${TOOLS_BIN}/ollama"
  else
    log_info "Ollama zaten mevcut: $(command -v ollama)"
  fi

  if ! command -v ollama >/dev/null 2>&1; then
    log_error "Ollama kurulumu doğrulanamadı: ${TOOLS_BIN}/ollama bulunamadı."
    return 1
  fi

  if ! is_port_listening 11434; then
    log_info "Ollama servisi (127.0.0.1:11434) arka planda başlatılıyor..."
    nohup ollama serve >"${TOOLS_ROOT}/ollama-serve.log" 2>&1 &
    local tries=0
    while ! is_port_listening 11434 && [[ ${tries} -lt 20 ]]; do
      sleep 0.5
      tries=$((tries + 1))
    done
  fi

  if ! is_port_listening 11434; then
    log_error "Ollama servisi 127.0.0.1:11434 üzerinde başlatılamadı."
    return 1
  fi

  log_info "Yerel yapay zeka modeli indiriliyor: ${OLLAMA_MODEL}"
  ollama pull "${OLLAMA_MODEL}"
  log_info "Ollama ve '${OLLAMA_MODEL}' modeli hazır."
}

setup_frontend() {
  log_info "Frontend kurulumu ve doğrulaması başlatılıyor (${FRONTEND_DIR})..."
  if ! command -v npm >/dev/null 2>&1; then
    log_error "npm bulunamadı. Önce 'bash scripts/setup_dev_tools.sh --install-tools' çalıştırın."
    return 1
  fi

  (
    cd "${FRONTEND_DIR}"
    npm install
    npm run typecheck
    npm run build
  )
  log_info "Frontend kurulumu, tip denetimi ve üretim derlemesi tamamlandı."
}

setup_backend() {
  log_info "Backend kurulumu ve doğrulaması başlatılıyor (${BACKEND_DIR})..."
  if ! command -v php >/dev/null 2>&1 || ! command -v composer >/dev/null 2>&1; then
    log_error "php veya composer bulunamadı. Önce 'bash scripts/setup_dev_tools.sh --install-tools' çalıştırın."
    return 1
  fi

  (
    cd "${BACKEND_DIR}"
    composer install --no-interaction
    composer dump-autoload --no-interaction

    if [[ ! -f ".env" && -f ".env.example" ]]; then
      cp ".env.example" ".env"
      log_info ".env.example dosyasından .env oluşturuldu."
    fi

    # APP_KEY boş ise geçerli 32-bayt base64 anahtar üret
    if [[ -f ".env" ]] && grep -qE "^APP_KEY=$" ".env"; then
      generated_key="$(php -r 'echo "base64:" . base64_encode(random_bytes(32));')"
      sed -i.bak "s|^APP_KEY=$|APP_KEY=${generated_key}|" ".env"
      rm -f ".env.bak"
      log_info ".env içinde 32-bayt APP_KEY oluşturuldu."
    fi

    # 127.0.0.1:5432 üzerinde PostgreSQL erişilebilir değilse yerel SQLite'a geç
    if ! python3 -c 'import socket; s = socket.create_connection(("127.0.0.1", 5432), 1.0); s.close()' >/dev/null 2>&1; then
      log_warn "127.0.0.1:5432 üzerinde PostgreSQL erişilebilir değil; yerel SQLite (database/database.sqlite) yapılandırılıyor."
      mkdir -p "database"
      touch "database/database.sqlite"
      if [[ -f ".env" ]]; then
        if grep -qE "^DB_CONNECTION=" ".env"; then
          sed -i.bak "s|^DB_CONNECTION=.*|DB_CONNECTION=sqlite|" ".env"
        else
          printf "\nDB_CONNECTION=sqlite\n" >> ".env"
        fi
        sed -i.bak "s|^DB_DATABASE=gamescout$|DB_DATABASE=${BACKEND_DIR}/database/database.sqlite|" ".env"
        rm -f ".env.bak"
      fi
    fi

    if [[ -f "artisan" ]]; then
      php artisan migrate --force --seed
    fi

    composer test
  )
  log_info "Backend kurulumu, veritabanı taşıma (migrate --seed) ve testleri tamamlandı."
}

run_setup_apps() {
  setup_frontend
  setup_backend
}

serve_backend() {
  log_info "Backend API sunucusu başlatılıyor (http://127.0.0.1:8000)..."
  cd "${BACKEND_DIR}"
  exec "${TOOLS_BIN}/php" artisan serve --host=127.0.0.1 --port=8000
}

serve_frontend() {
  log_info "Frontend geliştirme sunucusu başlatılıyor (http://127.0.0.1:5173)..."
  cd "${FRONTEND_DIR}"
  exec "${NODE_BIN}/npm" run dev -- --host 127.0.0.1 --port 5173
}

BACKEND_PID=""
OLLAMA_PID=""

cleanup_serve() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    log_info "Backend sunucusu (PID ${BACKEND_PID}) durduruluyor..."
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${OLLAMA_PID}" ]] && kill -0 "${OLLAMA_PID}" >/dev/null 2>&1; then
    log_info "Ollama sunucusu (PID ${OLLAMA_PID}) durduruluyor..."
    kill "${OLLAMA_PID}" >/dev/null 2>&1 || true
    wait "${OLLAMA_PID}" 2>/dev/null || true
  fi
}

serve_all() {
  if command -v ollama >/dev/null 2>&1 && ! is_port_listening 11434; then
    mkdir -p "${OLLAMA_MODELS_DIR}"
    log_info "Ollama (http://127.0.0.1:11434) arka planda başlatılıyor..."
    ollama serve >"${TOOLS_ROOT}/ollama-serve.log" 2>&1 &
    OLLAMA_PID=$!
  fi

  log_info "Backend (http://127.0.0.1:8000) arka planda başlatılıyor..."
  (
    cd "${BACKEND_DIR}"
    exec "${TOOLS_BIN}/php" artisan serve --host=127.0.0.1 --port=8000
  ) &
  BACKEND_PID=$!

  trap cleanup_serve INT TERM EXIT

  log_info "Frontend (http://127.0.0.1:5173) ön planda başlatılıyor (durdurmak için Ctrl+C)..."
  cd "${FRONTEND_DIR}"
  "${NODE_BIN}/npm" run dev -- --host 127.0.0.1 --port 5173
}

main() {
  if [[ $# -eq 0 ]]; then
    usage
    exit 0
  fi

  case "$1" in
    --check)
      run_check
      exit 0
      ;;
    --install-tools)
      run_install_tools
      ;;
    --install-ollama)
      run_install_ollama
      ;;
    --setup-apps)
      run_setup_apps
      ;;
    --serve-backend)
      serve_backend
      ;;
    --serve-frontend)
      serve_frontend
      ;;
    --serve)
      serve_all
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      log_error "Bilinmeyen seçenek: $1"
      usage
      exit 1
      ;;
  esac
}

main "$@"
