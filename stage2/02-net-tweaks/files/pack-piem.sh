#!/bin/bash

PACKAGE_NAME="piem"
VERSION="1.3"
BUILD_NAME=$PACKAGE_NAME"_"$VERSION

if [ -d $BUILD_NAME ]; then
    rm -rf $BUILD_NAME
fi

mkdir $BUILD_NAME
mkdir $BUILD_NAME/DEBIAN

cat << EOF > $BUILD_NAME/DEBIAN/control
Package: $PACKAGE_NAME
Version: $VERSION
Section: net
Priority: optional
Architecture: all
Depends: python2.7, hostapd, wpasupplicant
Maintainer: Jeromy Fu<jianfu@cisco.com>
Description: Pi Network Emulator
 Wrapper of a bunch of tc commands to allow
 adding adding rate limit, packet loss, delay
 for specific ip address on uplink/downlink
EOF

cat << EOF > $BUILD_NAME/DEBIAN/postinst
#!/bin/bash
echo "This version requires netem with specified loss sequence model support"
echo "Please setup the network bridge first"
echo "And then change the ingress and egress settings in \"/etc/piem/config.json\""
echo "enable piem service by running \"sudo systemctl enable piem\""
echo "start piem service by running \"sudo systemctl start piem\""
EOF
chmod +x $BUILD_NAME/DEBIAN/postinst

mkdir -p $BUILD_NAME/etc/piem
cp piem-config.json $BUILD_NAME/etc/piem/config.json
cp unstable-wifi.cfg $BUILD_NAME/etc/piem/unstable-wifi.cfg

mkdir -p $BUILD_NAME/etc/network
cp interfaces.wlan $BUILD_NAME/etc/network/interfaces.wlan
cp interfaces.eth $BUILD_NAME/etc/network/interfaces.eth

mkdir -p $BUILD_NAME/etc/hostapd
cp hostapd.conf $BUILD_NAME/etc/hostapd/hostapd.conf

mkdir -p $BUILD_NAME/etc/wpa_supplicant
cp wpa_supplicant.conf $BUILD_NAME/etc/wpa_supplicant/wpa_supplicant.conf

mkdir -p $BUILD_NAME/lib/systemd/system
cp piem.service $BUILD_NAME/lib/systemd/system/

mkdir $BUILD_NAME/sbin
cp emulator.py $BUILD_NAME/sbin/
cp dynem.py $BUILD_NAME/sbin/
cp bridge_switch.sh $BUILD_NAME/sbin/
cp fw.sh $BUILD_NAME/sbin/

chown root:root -R $BUILD_NAME
dpkg -b $BUILD_NAME
