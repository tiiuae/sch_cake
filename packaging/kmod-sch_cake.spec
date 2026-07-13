#
# kmod-sch_cake.spec — prebuilt CAKE qdisc module for RHEL 8
#
# Builds sch_cake.ko FROM THIS TREE against a target kernel and packages the
# binary module. Intended to be built on a host whose kernel-devel matches the
# deployment nodes (e.g. the HPCM management VM, which is the same
# 4.18.0-553.el8_10 kernel as the scheduler nodes).
#
# Required defines:
#   kver    target kernel uname-r, e.g. 4.18.0-553.el8_10.x86_64
#   srcdir  absolute path to a checkout of this repo (contains sch_cake.c, Kbuild)
#
# Build:
#   rpmbuild -bb packaging/kmod-sch_cake.spec \
#     --define "kver 4.18.0-553.el8_10.x86_64" \
#     --define "srcdir $(pwd)"
#
# The resulting RPM installs the module into /lib/modules/<kver>/extra and runs
# depmod. It Requires the exact kernel so dnf will refuse a mismatched kernel.

%global debug_package %{nil}
%{!?kver: %global kver %(uname -r)}
%{!?srcdir: %global srcdir %(pwd)}

# derive a version tag from the source commit if available, else date
%global cakever %(cd %{srcdir} 2>/dev/null && git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d)

Name:           kmod-sch_cake
Version:        0.0.%{cakever}
Release:        1%{?dist}
Summary:        CAKE (sch_cake) qdisc backport module for kernel %{kver}
License:        GPL-2.0-or-later
URL:            https://github.com/tiiuae/sch_cake
BuildArch:      x86_64

BuildRequires:  gcc, make, kernel-devel = %(echo %{kver} | sed 's/\.x86_64$//')
BuildRequires:  elfutils-libelf-devel

# Bind the package to the exact kernel it was compiled against.
Requires:       kernel-uname-r = %{kver}
Requires(post): kmod
Requires(postun): kmod
Provides:       kmod-sch_cake = %{version}-%{release}

%description
Out-of-tree build of the CAKE (Common Applications Kept Enhanced) qdisc,
based on the tiiuae/sch_cake backport (upstream since kernel 4.19; this
provides it for RHEL 8's 4.18 kernel). Delivers per-host fair-queueing and
bufferbloat-controlled egress shaping, including NAT-aware host isolation.

Built specifically for kernel %{kver}.

%prep
# Build from an external source tree (srcdir); nothing to unpack here.
rm -rf %{_builddir}/sch_cake-build
cp -a %{srcdir} %{_builddir}/sch_cake-build

%build
cd %{_builddir}/sch_cake-build
# Build against the TARGET kernel (not the builder's running kernel).
make -C /usr/src/kernels/%{kver} M=$(pwd) modules
# Fail early if the module did not build.
test -f sch_cake.ko

%install
cd %{_builddir}/sch_cake-build
install -d %{buildroot}/lib/modules/%{kver}/extra
install -m 0644 sch_cake.ko %{buildroot}/lib/modules/%{kver}/extra/sch_cake.ko

%post
depmod -a %{kver} || :

%postun
depmod -a %{kver} || :

%files
/lib/modules/%{kver}/extra/sch_cake.ko

%changelog
* Mon Jul 13 2026 TII AIRC Ops - 0.0.0-1
- Initial kmod packaging of the CAKE backport for RHEL 8 (4.18.0-553).
