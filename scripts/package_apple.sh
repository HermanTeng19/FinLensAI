#!/usr/bin/env bash
# ==============================================================================
# FinLens AI — Apple Distribution Packaging & Archiving Tool
# ==============================================================================
# Automates the Apple release pipeline for FinLens AI:
# 1. Project regeneration with updated bundle identifiers and entitlements (XcodeGen)
# 2. Production Release Archiving for macOS (.xcarchive & .app bundle & .zip)
# 3. Production Release Archiving for iOS (.xcarchive & .ipa payload)
# 4. App Sandbox, Hardened Runtime, and Entitlements Verification
# 5. Cryptographic SHA256 Checksum generation
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
APPLE_DIR="${ROOT_DIR}/apple"
PROJECT_DIR="${APPLE_DIR}/FinLens"
XCODEPROJ="${PROJECT_DIR}/FinLens.xcodeproj"
DIST_DIR="${ROOT_DIR}/dist/apple"

PLATFORM="all"
CONFIGURATION="Release"
CLEAN_BUILD=false
APP_VERSION="1.0.0"

print_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -p, --platform       Target platform: all | macos | ios (default: all)"
    echo "  -c, --configuration  Build configuration: Release | Debug (default: Release)"
    echo "      --clean          Clean previous build and archive artifacts before packaging"
    echo "  -h, --help           Display this help message"
    echo ""
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -p|--platform) PLATFORM="$2"; shift 2 ;;
        -c|--configuration) CONFIGURATION="$2"; shift 2 ;;
        --clean) CLEAN_BUILD=true; shift ;;
        -h|--help) print_usage; exit 0 ;;
        *) echo "Unknown parameter passed: $1"; print_usage; exit 1 ;;
    esac
done

echo "======================================================================"
echo "          FinLens AI — Apple Distribution & Packaging Tool"
echo "======================================================================"
echo "Platform:      ${PLATFORM}"
echo "Configuration: ${CONFIGURATION}"
echo "Version:       ${APP_VERSION}"
echo "Output Dir:    ${DIST_DIR}"
echo ""

# ------------------------------------------------------------------------------
# 1. Preflight Validations
# ------------------------------------------------------------------------------
echo "==> [1/5] Verifying Build Tools & Dependencies..."
if ! command -v xcodebuild &>/dev/null; then
    echo "Error: xcodebuild is not installed or not in PATH."
    exit 1
fi

if ! command -v xcodegen &>/dev/null; then
    echo "Warning: xcodegen not found in PATH. Using existing .xcodeproj..."
else
    echo "--> Regenerating Xcode project with xcodegen..."
    (cd "${PROJECT_DIR}" && xcodegen generate --quiet)
    echo "✓ Xcode project updated successfully."
fi

if [ "${CLEAN_BUILD}" = true ]; then
    echo "--> Cleaning previous distribution directory: ${DIST_DIR}..."
    rm -rf "${DIST_DIR}"
fi

mkdir -p "${DIST_DIR}/archives"
mkdir -p "${DIST_DIR}/macos"
mkdir -p "${DIST_DIR}/ios"

# ------------------------------------------------------------------------------
# 2. Package macOS Application
# ------------------------------------------------------------------------------
package_macos() {
    echo ""
    echo "==> [2/5] Archiving & Packaging macOS Application..."
    local ARCHIVE_PATH="${DIST_DIR}/archives/FinLens_macOS.xcarchive"
    local MACOS_APP_OUT="${DIST_DIR}/macos/FinLens.app"
    local MACOS_ZIP_OUT="${DIST_DIR}/FinLens-macOS-v${APP_VERSION}.zip"

    echo "--> Running xcodebuild archive for FinLens_macOS (${CONFIGURATION})..."
    xcodebuild archive \
        -project "${XCODEPROJ}" \
        -scheme FinLens_macOS \
        -configuration "${CONFIGURATION}" \
        -destination 'platform=macOS' \
        -archivePath "${ARCHIVE_PATH}" \
        CODE_SIGN_IDENTITY="-" \
        CODE_SIGNING_REQUIRED=NO \
        CODE_SIGNING_ALLOWED=YES \
        -quiet

    echo "✓ macOS xcarchive created at: ${ARCHIVE_PATH}"

    echo "--> Extracting macOS App Bundle..."
    rm -rf "${MACOS_APP_OUT}"
    cp -R "${ARCHIVE_PATH}/Products/Applications/FinLens.app" "${DIST_DIR}/macos/"

    echo "--> Verifying App Sandbox & Hardened Runtime Signatures..."
    codesign --force --deep --sign - --options runtime \
        --entitlements "${PROJECT_DIR}/Resources/FinLens_macOS.entitlements" \
        "${MACOS_APP_OUT}"

    codesign --verify --deep --strict --verbose=1 "${MACOS_APP_OUT}"

    echo "--> Creating distributable zip archive: ${MACOS_ZIP_OUT}..."
    (cd "${DIST_DIR}/macos" && zip -q -r -y "${MACOS_ZIP_OUT}" "FinLens.app")
    echo "✓ macOS Application packaged successfully."
}

# ------------------------------------------------------------------------------
# 3. Package iOS Application
# ------------------------------------------------------------------------------
package_ios() {
    echo ""
    echo "==> [3/5] Archiving & Packaging iOS Application..."
    local ARCHIVE_PATH="${DIST_DIR}/archives/FinLens_iOS.xcarchive"
    local IOS_PAYLOAD_DIR="${DIST_DIR}/ios/Payload"
    local IOS_IPA_OUT="${DIST_DIR}/FinLens-iOS-v${APP_VERSION}.ipa"

    echo "--> Running xcodebuild archive for FinLens_iOS (${CONFIGURATION})..."
    xcodebuild archive \
        -project "${XCODEPROJ}" \
        -scheme FinLens_iOS \
        -configuration "${CONFIGURATION}" \
        -destination 'generic/platform=iOS' \
        -archivePath "${ARCHIVE_PATH}" \
        CODE_SIGN_IDENTITY="" \
        CODE_SIGNING_REQUIRED=NO \
        CODE_SIGNING_ALLOWED=NO \
        -quiet

    echo "✓ iOS xcarchive created at: ${ARCHIVE_PATH}"

    echo "--> Assembling iOS IPA Container (Payload Structure)..."
    rm -rf "${IOS_PAYLOAD_DIR}"
    mkdir -p "${IOS_PAYLOAD_DIR}"
    cp -R "${ARCHIVE_PATH}/Products/Applications/FinLens.app" "${IOS_PAYLOAD_DIR}/"

    echo "--> Creating distributable IPA package: ${IOS_IPA_OUT}..."
    (cd "${DIST_DIR}/ios" && zip -q -r -y "${IOS_IPA_OUT}" "Payload")
    echo "✓ iOS Application (.ipa) packaged successfully."
}

if [[ "${PLATFORM}" == "all" || "${PLATFORM}" == "macos" ]]; then
    package_macos
fi

if [[ "${PLATFORM}" == "all" || "${PLATFORM}" == "ios" ]]; then
    package_ios
fi

# ------------------------------------------------------------------------------
# 4. Generate Cryptographic Checksums
# ------------------------------------------------------------------------------
echo ""
echo "==> [4/5] Generating SHA256 Checksums..."
CHECKSUM_FILE="${DIST_DIR}/SHA256SUMS.txt"
rm -f "${CHECKSUM_FILE}"

cd "${DIST_DIR}"
for file in *.zip *.ipa; do
    if [ -f "${file}" ]; then
        shasum -a 256 "${file}" >> "${CHECKSUM_FILE}"
    fi
done
echo "✓ Checksums generated in: ${CHECKSUM_FILE}"

# ------------------------------------------------------------------------------
# 5. Packaging Summary
# ------------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "          🎉 APPLE DISTRIBUTION PACKAGING COMPLETED 🎉"
echo "======================================================================"
echo "Generated Artifacts:"
for artifact in "${DIST_DIR}"/*.zip "${DIST_DIR}"/*.ipa; do
    if [ -f "${artifact}" ]; then
        SIZE=$(du -h "${artifact}" | awk '{print $1}')
        SHA=$(shasum -a 256 "${artifact}" | awk '{print $1}')
        echo "  • $(basename "${artifact}") (${SIZE})"
        echo "    SHA256: ${SHA}"
    fi
done
echo ""
echo "Archives:"
echo "  • macOS: ${DIST_DIR}/archives/FinLens_macOS.xcarchive"
echo "  • iOS:   ${DIST_DIR}/archives/FinLens_iOS.xcarchive"
echo "Export Options Templates: ${APPLE_DIR}/ExportOptions/"
echo "======================================================================"
