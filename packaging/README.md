# Packaging sch_cake for RHEL 8 (kernel 4.18)

CAKE is upstream since kernel 4.19; RHEL 8 ships **4.18**, so it must be built
out-of-tree from this backport tree. Two delivery options.

> **Do not use `torvalds/linux` `sch_cake.c`** — mainline needs APIs absent in
> 4.18 (`net/gso.h`, `qdisc_drop_reason`, `get_random_u16`, `iph_totlen`, ...)
> and will not compile. This tree carries the compat shims that do.

## Option A (preferred): prebuilt kmod RPM

Build a binary-module RPM on a host whose kernel matches the target nodes. The
HPCM management VM is `4.18.0-553.el8_10` — identical to the scheduler nodes —
so it is the correct builder, and the build doubles as the 4.18 compile check.

```bash
git clone -b packaging/rhel8-kmod https://github.com/tiiuae/sch_cake
cd sch_cake
./packaging/build-kmod-rpm.sh            # KVER defaults to uname -r (mgmt VM == node kernel)
# -> prints path to kmod-sch_cake-*.rpm and the cm commands to serve/install it
```

Serve via a custom HPCM repo and install with `cm`:
```bash
mkdir -p /opt/clmgr/repos/other/te-custom-rhel8
cp ~/rpmbuild/RPMS/x86_64/kmod-sch_cake-*.rpm /opt/clmgr/repos/other/te-custom-rhel8/
cm repo add --custom te-custom-rhel8 /opt/clmgr/repos/other/te-custom-rhel8
cm repo group add rhel8.10_service te-custom-rhel8
cm node dnf -n t01pdscsch01 --repo-group rhel8.10_service install -y kmod-sch_cake
```

Properties:
- Deterministic — the exact `.ko` you tested is what installs.
- No toolchain/dkms needed on nodes.
- `Requires: kernel-uname-r = <kver>` — dnf refuses a mismatched kernel.
- **Kernel-coupled**: rebuild after a kernel bump (re-run the build helper).

## Option B (fallback): DKMS source RPM / source install

Auto-rebuilds on kernel updates, at the cost of a per-node toolchain and
rebuild-on-install that can fail per-node.

```bash
VER=$(git rev-parse --short HEAD)
sed "s/__VER__/$VER/" packaging/dkms.conf > dkms.conf
cp -a . /usr/src/sch_cake-$VER
dkms add -m sch_cake -v $VER && dkms build -m sch_cake -v $VER && dkms install -m sch_cake -v $VER
```

## Verify (either option), on the node

```bash
modprobe sch_cake
tc qdisc add dev lo root cake bandwidth 1gbit hosts nat ack-filter \
  && tc qdisc del dev lo root && echo CAKE_OK
```

If `modprobe` fails with a signature error, SecureBoot module signing is
enforced — sign `sch_cake.ko` with an enrolled MOK before it will load.

## Files

| File | Purpose |
|------|---------|
| `kmod-sch_cake.spec`  | RPM spec (Option A) — builds + packages the binary module |
| `build-kmod-rpm.sh`   | One-shot helper: smoke-test compile + rpmbuild + next steps |
| `dkms.conf`           | DKMS config (Option B) — source rebuild delivery |
