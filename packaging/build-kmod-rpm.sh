#!/usr/bin/env bash
# build-kmod-rpm.sh — build the kmod-sch_cake RPM from this checkout.
#
# Run on a builder whose kernel-devel matches the TARGET kernel (e.g. the HPCM
# management VM, which shares 4.18.0-553.el8_10 with the scheduler nodes).
#
#   ./packaging/build-kmod-rpm.sh [KVER]
#
# KVER defaults to the running kernel (uname -r). On the mgmt VM that is
# already 4.18.0-553.el8_10.x86_64 == the node kernel, so no arg is needed.
#
# Output: prints the path to the built kmod-sch_cake-*.rpm.
set -euo pipefail

KVER="${1:-$(uname -r)}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[build] target kernel : $KVER"
echo "[build] source tree   : $REPO_ROOT"

# --- preconditions ---
command -v rpmbuild >/dev/null || { echo "FATAL: rpmbuild not installed" >&2; exit 1; }
KDEV="/usr/src/kernels/$KVER"
[ -d "$KDEV" ] || {
  echo "FATAL: kernel-devel for $KVER not found at $KDEV" >&2
  echo "       install it (matching the target node kernel) and retry." >&2
  exit 1
}

# --- quick standalone compile as an early smoke-test (fail fast, clear error) ---
echo "[build] smoke-test compile against $KVER ..."
make -C "$KDEV" M="$REPO_ROOT" modules
test -f "$REPO_ROOT/sch_cake.ko" || { echo "FATAL: sch_cake.ko not produced" >&2; exit 1; }
echo "[build] smoke-test OK: $(modinfo "$REPO_ROOT/sch_cake.ko" | awk '/^description|^vermagic/{print}')"
make -C "$KDEV" M="$REPO_ROOT" clean >/dev/null 2>&1 || true

# --- build the RPM ---
echo "[build] rpmbuild ..."
rpmbuild -bb "$REPO_ROOT/packaging/kmod-sch_cake.spec" \
  --define "kver $KVER" \
  --define "srcdir $REPO_ROOT"

RPM=$(ls -t "${HOME}/rpmbuild/RPMS/x86_64/kmod-sch_cake-"*.rpm 2>/dev/null | head -1 || true)
[ -n "$RPM" ] || { echo "FATAL: RPM not found under ~/rpmbuild/RPMS/x86_64" >&2; exit 1; }

echo
echo "[build] DONE"
echo "RPM: $RPM"
echo "contents:"
rpm -qpl "$RPM"
echo
echo "Next (on HPCM mgmt VM):"
echo "  mkdir -p /opt/clmgr/repos/other/te-custom-rhel8"
echo "  cp '$RPM' /opt/clmgr/repos/other/te-custom-rhel8/"
echo "  cm repo add --custom te-custom-rhel8 /opt/clmgr/repos/other/te-custom-rhel8"
echo "  cm repo group add rhel8.10_service te-custom-rhel8"
echo "  cm node dnf -n t01pdscsch01 --repo-group rhel8.10_service install -y kmod-sch_cake"
