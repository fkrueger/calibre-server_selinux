#!/bin/bash


# options
CALIBREDIR="/opt/calibre"
CALIBREUSER="calibre"
CALIBREINIT=""

# commands
DOVERSIONCHECKS="1"					# when setting this to 0, calibre-server will always be reinstalled, no matter if a newer version is found or not.
DOSHA256CHECK="1"					# leave this at 1. always. unless i m too slow at updating the sha256 hashes of known calibre installer versions on $CALIBREINSTALLERVERSIONS
DOINSTALLERCACHECLEANUP="1"				# by setting this to 0, you may be able to save download time. by setting this to 1, you are saving disk space in /tmp. you decide.
DOSAFERPATCHING="1"					# never set this to 0, unless you are okay with losing ALL files in /opt/calibre/ !



### do not add anything below this line. ###

IKNOWWHATIMDOING="0"					# leave this at 0, unless you know what you are doing ;-)


# internals
CALUPD="/tmp/calibre_orig_installer.sh"
SAFERPATCH="$CALIBREDIR/calibre_safer_installer.patch"

# defaults
CALIBRESIGURL="https://code.calibre-ebook.com/signatures/"
CALIBREINSTALLERURL="https://download.calibre-ebook.com/linux-installer.sh"
CALIBREINSTALLERVERSIONSURL="https://dev.techno.holics.at/selinux_calibre-server/calibre_known-installer-versions.sha256sum.txt"
CALIBREINSTALLERVERSIONS="$CALIBREDIR/calibre_known-installer-versions.sha256sum.txt"



## func
logme() {
  TS=`date +%Y%m%d_%H%M%S`
  echo "$TS: $*"
}



logme "Starting."

## safety checks

logme ". Time to do safety checks"
if [ "x$DOSAFERPATCHING" != "x1" ]; then
  if [ "x$IKNOWWHATIMDOING" != "x1" ]; then
    echo ">>> You deactivated the safer-installer patch. This WILL delete any and all files in /opt/calibre/ ."
    echo ">>> Type in 'yes' to continue (or set IKNOWWHATIMDOING=1 to never ask you again)."
    read userinput
    if [ "x$userinput" != "xyes" ]; then
      echo "You typed '$userinput', not 'yes'. Exitting."
      exit 0
    fi
  else
    echo ""
    echo ". So you know what you're doing, ay? Let's hope so.."
    echo ""
    sleep 1
  fi
fi


## prerequisite checks
logme ". Time to do prerequisite checks"


if [ "x$CALIBREINIT" == "x" ] || [ ! -e "$CALIBREINIT" ]; then
  BINSVC=`which service`
  if [ "x$?" == "x1" ]; then
    echo "!!! Error: service binary is missing. On  Fedora, CentOS, RHEL it simply should exist, on Debian and Ubuntu, too."
    if [ -e "/etc/init.d/calibre-server" ]; then
      CALIBREINIT="/etc/init.d/calibre-server"
    else
      echo "    Default init.d script not found also. Please provide the filepath to calibre-server's init.d script in CALIBREINIT (in this file)."
      exit -1
    fi
  fi
else
  echo ". Using CALIBREINIT override at $CALIBREINIT instead of service."
fi

if [ "x$DOSAFERPATCHING" == "x1" ]; then
  BINPATCH=`which patch`
  if [ "x$?" == "x1" ]; then
    echo "!!! Error: patch binary is missing. Install it via 'yum install patch' (Fedora, CentOS, RHEL) or 'apt-get install patch' (Debian, Ubuntu)."
    exit -1
  fi
fi

BINWGET=`which wget`
if [ "x$?" == "x1" ]; then
  echo "!!! Error: wget binary is missing. Install it via 'yum install wget' (Fedora, CentOS, RHEL) or 'apt-get install wget' (Debian, Ubuntu)."
  exit -1
fi

if [ "x$DOSHA256CHECK" == "x1" ]; then
  BINSHA256SUM=`which sha256sum`
  if [ "x$?" == "x1" ]; then
    echo "!!! Error: sha256sum binary is missing. Install it via 'yum install coreutils' (Fedora, CentOS, RHEL) or 'apt-get install coreutils' (Debian, Ubuntu)."
    exit -1
  fi
fi


## main

## check if a new version exists, before doing anything else.

logme ". Doing version checking:"
if [ "x$DOVERSIONCHECKS" == "x1" ]; then
  INSTALLEDVERSION=`sudo -u $CALIBREUSER -- $CALIBREDIR/calibre-server --version | cut -d'(' -f2 | cut -d' ' -f2 | cut -d')' -f1`
  CURVERSORTIE=`echo "$INSTALLEDVERSION" | awk 'BEGIN { FS="." } {printf ("%04d%04d%04d\n", $1, $2, $3) }'`
  logme ".. Found installed version: '$INSTALLEDVERSION' (sortie: $CURVERSORTIE)"
  LATESTVERSIONSORTIE=`curl --cacert $CALIBREDIR/cert_code.calibre-ebook.com.pem.cer -q --url $CALIBRESIGURL | grep x86_64 | sed -r 's/^.*?calibre-(.*)-x86_64\..*$/\1/g' | grep '5\.21' -A 100 | awk 'BEGIN { FS="." } {printf ("%04d%04d%04d\n", $1, $2, $3) }' | sort | grep -A 100 "$CURVERSORTIE" | tail -n 1`
  logme ".. Latest version sortie found: $LATESTVERSIONSORTIE"

  if [ "x$CURVERSORTIE" == "x$LATESTVERSIONSORTIE" ]; then
    logme ". Nothing to do, because there is no newer version. Exitting."
    exit 0
  fi
fi



logme ". Starting the update."

# get current calibre linux installer
$BINWGET -O $CALUPD $CALIBREINSTALLERURL
if [ "x$?" != "x0" ]; then
  echo "!!! Error: wget call failed (calibre installer: $CALIBREINSTALLERURL). Exitting."
  exit -1
fi

if [ ! -e $CALIBREINSTALLERVERSIONS ]; then
  $BINWGET -O $CALIBREINSTALLERVERSIONS $CALIBREINSTALLERVERSIONSURL
  if [ "x$?" != "x0" ]; then
    echo "!!! Error: wget call failed (calibre versions info: $CALIBREINSTALLERVERSIONSURL). Exitting."
    exit -1
  fi
fi

if [ "x$DOSHA256CHECK" == "x1" ]; then
  TMP=`$BINSHA256SUM $CALUPD`
  grep "^$TMP\$" $CALIBREINSTALLERVERSIONS >/dev/null 2>&1
  if [ "x$?" == "x1" ]; then
    echo "!!! Error: Calibre installer has unknown sha256sum '$TMP'. Exitting."
    exit -1
  fi
fi


# patch it with our saferpatch
if [ "x$DOSAFERPATCHING" == "x1" ]; then
  $BINPATCH $CALUPD -p0 $SAFERPATCH
  RC="$?"
  if [ "x$RC" == "x1" ] ; then
    echo "!!! Error: Patch could not be applied to make the calibre installer safer. Exitting."
    exit -1
  fi
  if [ "x$RC" == "x255" ]; then
    echo "!!! Error: The linux-installer.sh does not fit $SAFERPATCH . It is highly recommended not to execute $CALUPD . Exitting."
    exit -1
  fi
  #echo "RC=$?"
fi

# if everything looked fine so far, call the patched calibre-installer"
echo -en ". Stopping calibre-server:"
if [ "x$CALIBREINIT" != "x" ]; then
  echo " via CALIBREINIT: $CALIBREINIT stop"
  $CALIBREINIT stop
else
  echo " via $BINSVC calibre-server stop"
  $BINSVC calibre-server stop
fi

logme ". Calling the calibre-installer: $CALUPD"
bash $CALUPD
logme ". Finished with RC: $?"

echo -en ". Starting calibre-server"
if [ "x$CALIBREINIT" != "x" ]; then
  echo " via CALIBREINIT: $CALIBREINIT start"
  $CALIBREINIT start
else
  echo " via $BINSVC calibre-server start"
  $BINSVC calibre-server start
fi

if [ "x$DOINSTALLERCACHECLEANUP" == "x1" ]; then
  echo ". Clearing up installer cache in /tmp/calibre-installer-cache/"
  rm -rf /tmp/calibre-installer-cache/
fi

logme "#Fin"

