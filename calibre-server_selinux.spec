# vim: sw=4:ts=4:et

%define calibreserver_ver 5.21.0
%define selinux_policyver 3.14.3-1
%define selinux_ppname calibre
%define selinux_porttype calibre_port_t
%define selinux_ports_tcp 9043 9080 9443
%define selinux_ports_udp 5353
%define selinux_dirs /home/ /opt/calibre/ /opt/home/ /var/log/calibre*.log


Name:   calibre-server_selinux
Version:	1.0
Release:	7%{?dist}
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
## generic part
for i in %{selinux_ports_tcp} XXX; do
    [ "x$i" != "xXXX" ] && semanage port -a -t %{selinux_porttype} -p tcp $i ||:
done
for i in %{selinux_ports_udp} XXX; do
    [ "x$i" != "xXXX" ] && semanage port -a -t %{selinux_porttype} -p udp $i ||:
done
## custom part
semanage fcontext -a -e '/opt/calibre(/.*)?' '/home/[^/]+/calibre(/.*)?' ||:
if /usr/sbin/selinuxenabled ; then
    /usr/sbin/load_policy
    restorecon -R %{selinux_dirs} ||:
fi;
exit 0

%postun
if [ $1 -eq 0 ]; then
    # try to remove all our custom changes
    ## generic parts
    for i in %{selinux_ports_tcp} XXX; do
        [ "x$i" != "xXXX" ] && semanage port -d -t %{selinux_porttype} -p tcp $i ||:
    done
    for i in %{selinux_ports_udp} XXX; do
        [ "x$i" != "xXXX" ] && semanage port -d -t %{selinux_porttype} -p udp $i ||:
    done
    ## custom part
    semanage fcontext -d '/home/[^/]+/calibre(/.*)?' ||:
    # then try to remove the policy module
    semodule -n -r calibre-server
    if /usr/sbin/selinuxenabled ; then
       /usr/sbin/load_policy
       /usr/sbin/restorecon -R %{selinux_dirs} ||:
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
%doc %{_defaultdocdir}/%{name}-%{version}/readme.md

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
* Mon Feb 19 2024 Frederic Krueger <fkrueger-dev-selinux_calibreserver@holics.at> 1.0-7
- updated policy for snappy_search - access

* Thu Jun 1 2023 Frederic Krueger <fkrueger-dev-selinux_calibreserver@holics.at> 1.0-5
- updated policy for tmp_t access

* Wed Feb 15 2023 Frederic Krueger <fkrueger-dev-selinux_calibreserver@holics.at> 1.0-4
- updated policy for newly added weirdness around rpm_script_t

* Mon Aug 22 2022 Frederic Krueger <fkrueger-dev-selinux_calibreserver@holics.at> 1.0-3
- added basic ipa_ passwd_file sssd_stream_connect support

* Tue Aug 31 2021 Frederic Krueger <fkrueger-dev-selinux_calibreserver@holics.at> 1.0-2
- added system_cronjob_t support

* Mon Jul 12 2021 Frederic Krueger <fkrueger-dev-selinux_calibreserver@holics.at> 1.0-1
- Initial version

