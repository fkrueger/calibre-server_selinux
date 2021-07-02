# FIRST SETUP
This selinux policy module can be used in two modes:
* more secure: calibre and its data runs in /opt/calibre/ and respectively /opt/home/calibre/; tmp files go into locked down calibre-only /opt/home/calibre/tmp/
* much less secure: calibre runs in /home/calibre/ and respectively /home/<user>/Calibre Library; tmp files go into systemwide /tmp/

## Setup for a "more secure" environment
1. Setup directories:
<pre><code>
    mkdir -p /opt/home/calibre/{.cache,.config,tmp,Calibre Library}/ /opt/calibre/
</code></pre>
To use calibre-only temp files:
<pre><code>
    mkdir -p /opt/home/calibre/tmp
</code></pre>
Alternatively you can put these in /opt/calibre/tmp/ .

2. Create environment file to include in Initscript / SystemD unit file, that points to the temp directory Calibre should use:
<pre><code>
cat&lt;&lt;EOF >/etc/sysconfig/calibre-server
TEMP="/opt/home/calibre/tmp"
EOF
</code></pre>

## Setup for "much less secure" default environment
  Nothing to do.

## SystemD integration for calibre-server
Example SystemD unit file:
<pre><code>
cat&lt;&lt;EOF > /etc/systemd/system/calibre-server.service
[Unit]
Description=Calibre server headless edition
#After=remote-fs.target
After=network-online.target time-sync.target
Wants=network-online.target

[Service]
Type=simple
User=calibre
#Restart=yes
TimeoutSec=5min
IgnoreSIGPIPE=no
KillMode=process
GuessMainPID=no
RemainAfterExit=yes
#SuccessExitStatus=5 6
EnvironmentFile=/etc/sysconfig/calibre-server
WorkingDirectory=/opt/home/calibre/Calibre Library/
ExecStart=/opt/calibre/calibre-server --port=9080 --log=/var/log/calibre-server.log "/opt/home/calibre/Calibre Library/"

WantedBy=multi-user.target

EOF
</code></pre>
Remember to adapt the WorkingDirectory and ExecStart parameter, if your Calibre Library is not in /opt/home/calibre/Calibre Library/.

.. and activate the new SystemD unit file by reloading the daemon:
<pre><code>
 systemctl daemon-reload
</code></pre>
3. Reset SElinux contexts on the affected directories (can be used as debug, too, i.e. if something that should work doesn't work)
<pre><code>
 restorecon -vR /opt/ /home/
</code></pre>
4. Restart calibre-server
<pre><code>
 service calibre-server restart
</code></pre>
5. Test your calibre-server by heading your browser to: http://your.hostname:9080/
Calibre should be shown to you.

You can now be done with this.

### Additional things
6. Or you can alternatively hide your calibre-server from direct internet access by setting up a reverse proxy (Apache or NginX) in front of it.

For Apache your (presumably) <virtualhost> configuration would have to be extended like so:
<pre><code>
cat&lt;&lt;EOF >> yourconf.conf
     AllowEncodedSlashes     On
     ProxyPass               "/"     "http://127.0.0.1:9080/"
     ProxyPassReverse        "/"     "http://127.0.0.1:9080/"
EOF
</code></pre>
7. If you also want to password-protect the calibre instance, you can also add this to your virtualhost configuration.
<pre><code>
cat&lt;&lt;EOF >> yourconf.conf
       <Proxy *>
          Allow from all
          AuthType Basic
          AuthName "Calibre-auth"
          AuthUserFile /etc/httpd/.htpasswd.users
          Require user calibre
        </Proxy>
EOF
</code></pre>

Remember to create a user in /etc/httpd/.htpasswd.users by using the htpasswd command:
> htpasswd /etc/httpd/.htpasswd.users calibre

__Congrats, you now should have a better secured calibre-server instance running with SElinux and HTTP Basic authentication behind a reverse proxy!__

## CAVEATS
__Do not put anything of value in /opt/calibre/ !__

The default update script under https://download.calibre-ebook.com/linux-installer.sh will happily delete /opt/calibre/ completely and start from scratch, even if it means killing the installer itself.

It is a mean script of the type "let's hope noone ever roots my webserver and adds stuff to the installer script.. or edits calibre files manually".

Creating an rpm, deb, etc. would have been much better.. or if everything else fails, at least they could have used npm.

Thus for now, be very wary of using thge original calibre-update script on any machine, you still want to use lateron.

### Slightly safer calibre-update.sh script
The following script __MIGHT__ do things a little more safely.

This file should be at /opt/calibre/calibre-update.sh after installing the SElinux module.

### Patch file needed for said update script
This file should be at /opt/calibre/calibre_safer_installer.patch after installing the SElinux module.

# Cheers!

