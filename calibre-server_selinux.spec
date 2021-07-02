# vim: sw=4:ts=4:et

%define relabel_files() \
A=`getenforce` \
setenforce 0 \
restorecon -R /home/ /opt/calibre/ /opt/home/ /var/log/calibre*.log \
setenforce $A

%define calibreserver_ver 5.21.0
%define selinux_policyver 3.14.3-1

Name:   calibre-server_selinux
Version:	1.0
Release:	1%{?dist}
Summary:	SELinux policy module for calibre-server (based on the default installer)
BuildRequires: policycoreutils, selinux-policy-devel
Requires:	selinux-policy, selinux-policy-targeted

Group:	System Environment/Base		
License:	GPLv2+
URL:		https://dev.techno.holics.at/calibre-server_selinux/
Source0:	calibre-server.te
Source1:	calibre-server.fc
Source2:	calibre-server.if
#Source3:	calibre-server_selinux.8
Source4:        calibre-server_selinux-readme.md
Source5:        calibre-server.logrotate
Source6:        calibre-updater.logrotate
Source7:        calibre-server.cron
Source8:        calibre-updater.cron
Source9:        calibre-update.sh
Source10:       cert_code.calibre-ebook.com.pem_20210619.cer
Source11:       calibre_safer_installer_20210619.patch
Source12:       calibre-server.service
Source13:	calibre-server.env

Requires: policycoreutils, libselinux-utils
Requires(post): selinux-policy-base >= %{selinux_policyver}, policycoreutils
Requires(postun): policycoreutils
BuildArch: noarch

%description
This package installs and sets up the SELinux policy security module for calibre-server (under /opt/calibre/ and library at /opt/home/calibre/Calibre Library/).

%install
install -d %{buildroot}/etc/selinux/targeted/contexts/users/
install -d %{buildroot}%{_defaultdocdir}/%{name}-%{version}/
install -m 644 %{SOURCE4} %{buildroot}%{_defaultdocdir}/%{name}-%{version}/readme.md
install -d %{buildroot}%{_datadir}/selinux/packages
install -m 644 %{_builddir}/%{name}-%{version}-%{release}.%{_arch}/calibre-server.pp %{buildroot}%{_datadir}/selinux/packages
install -d %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -m 644 %{SOURCE2} %{buildroot}%{_datadir}/selinux/devel/include/contrib/
#install -d %{buildroot}%{_mandir}/man8/
#install -m 600 %{SOURCE3} %{buildroot}%{_mandir}/man8/calibre-server_selinux.8
install -d %{buildroot}/etc/cron.d/
install -m 644 %{SOURCE7} %{buildroot}/etc/cron.d/calibre-server
install -m 644 %{SOURCE8} %{buildroot}/etc/cron.d/calibre-updater
install -d %{buildroot}/etc/logrotate.d/
install -m 644 %{SOURCE5} %{buildroot}/etc/logrotate.d/calibre-server
install -m 644 %{SOURCE6} %{buildroot}/etc/logrotate.d/calibre-updater
install -d %{buildroot}/etc/sysconfig/
install -m 644 %{SOURCE13} %{buildroot}/etc/sysconfig/calibre-server
install -d %{buildroot}/lib/systemd/system/
install -m 644 %{SOURCE12} %{buildroot}/lib/systemd/system/calibre-server.service
install -d %{buildroot}/opt/calibre/
install -m 644 %{SOURCE11} %{buildroot}/opt/calibre/calibre_safer_installer.patch
install -m 755 %{SOURCE9} %{buildroot}/opt/calibre/calibre-update.sh
install -m 644 %{SOURCE10} %{buildroot}/opt/calibre/cert_code.calibre-ebook.com.pem.cer				# XXX this is a selfsigned cert, so we have to provide it here.
install -d %{buildroot}/opt/home/calibre/
install -d %{buildroot}/opt/home/calibre/Calibre\ Library/
install -d %{buildroot}/opt/home/calibre/tmp/



%package -n calibre-server-utils
Summary:        Utilities for running a headless Calibre Content Server under /opt/calibre/ , needed to calibre-server_selinux
Requires: coreutils, curl, patch, wget

%description -n calibre-server-utils
This package contains a systemd unit file for calibre-server, logrotate files for /var/log/calibre-server.log and calibre-update.log, cron-files for auto-calibre-server restart every hour and the calibre-update once a day.
The updater named calibre-update.sh only updates when new version are available and tries to make it a little safer than wget -O- | sudo -- bash (installer version checking) and patches the installer to not delete all data in calibre-server installation directory (/opt/calibre/ here).



%build
TMPB="%{_builddir}/%{name}-%{version}-%{release}.%{_arch}/"
mkdir -p "$TMPB"
cp %{SOURCE0} %{SOURCE1} %{SOURCE2} "$TMPB"
cd "$TMPB"
make -f /usr/share/selinux/devel/Makefile

%post
# install policy modules
semodule -n -i %{_datadir}/selinux/packages/calibre-server.pp
# then add port definitions and context mirroring (not yet working) for /opt/calibre/ to /home/calibre/ - stuff for /opt/calibre/
for i in 9080 9043 9443; do
    semanage port -a -t calibre_port_t -p tcp $i ||:
done
semanage port -a -t calibre_port_t -p udp 5353 ||:
semanage fcontext -a -e '/opt/calibre(/.*)?' '/home/[^/]+/calibre(/.*)?' ||:

if /usr/sbin/selinuxenabled ; then
    /usr/sbin/load_policy
    %relabel_files

fi;
exit 0

%postun
if [ $1 -eq 0 ]; then
    # try to remove all port definitions and context-mirroring.
    for i in 9043 9080 9443; do
        semanage port -d -t calibre_port_t -p tcp $i ||:
    done
    semanage port -d -t calibre_port_t -p udp 5353 ||:
    semanage fcontext -d '/home/[^/]+/calibre(/.*)?' ||:
    # then try to remove the policy module
    semodule -n -r calibre-server
    if /usr/sbin/selinuxenabled ; then
       /usr/sbin/load_policy
       %relabel_files

    fi;
fi;
exit 0

%post -n calibre-server-utils
if [ $1 -eq 0 ]; then
    systemctl daemon-reload
    service crond reload
fi

%postun -n calibre-server-utils
if [ $1 -eq 0 ]; then
    systemctl daemon-reload
    service crond reload
fi


%files
%attr(0600,root,root) %{_datadir}/selinux/packages/calibre-server.pp
%{_datadir}/selinux/devel/include/contrib/calibre-server.if
#%{_mandir}/man8/calibre-server_selinux.8.*
%{_defaultdocdir}/%{name}-%{version}/readme.md

%files -n calibre-server-utils
%attr(0644,root,root) /etc/cron.d/calibre-server
%attr(0644,root,root) /etc/cron.d/calibre-updater
%attr(0644,root,root) /etc/logrotate.d/calibre-server
%attr(0644,root,root) /etc/logrotate.d/calibre-updater
%attr(0644,root,root) /etc/sysconfig/calibre-server
%attr(0644,root,root) /lib/systemd/system/calibre-server.service
%attr(0644,calibre,calibre) /opt/calibre/calibre_safer_installer.patch
%attr(0755,calibre,calibre) /opt/calibre/calibre-update.sh
%attr(0644,calibre,calibre) /opt/calibre/cert_code.calibre-ebook.com.pem.cer
%attr(0644,root,root) %{_defaultdocdir}/%{name}-%{version}/readme.md

%changelog
* Mon Jun 20 2021 Frederic Krueger <fkrueger-dev-selinux_calibreserver@holics.at> 1.0-1
- Initial version

