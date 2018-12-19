#!/bin/bash

PACKAGE_NAME="piem"
VERSION="0.1-1"
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
Depends: python2.7
Maintainer: Jeromy Fu<jianfu@cisco.com>
Description: Pi Network Emulator
 Wrapper of a bunch of tc commands to allow
 adding adding rate limit, packet loss, delay
 for specific ip address on uplink/downlink
EOF

cat << EOF > $BUILD_NAME/DEBIAN/postinst
#!/bin/bash
echo "Please setup the network bridge first"
echo "And then change the ingress and egress settings in \"/etc/piem/config.json\""
echo "enable piem service by running \"sudo systemctl enable piem\""
echo "start piem service by running \"sudo systemctl start piem\""
EOF
chmod +x $BUILD_NAME/DEBIAN/postinst

mkdir -p $BUILD_NAME/etc/piem
cp piem-config.json $BUILD_NAME/etc/piem/config.json

mkdir -p $BUILD_NAME/lib/systemd/system
cp piem.service $BUILD_NAME/lib/systemd/system/

mkdir $BUILD_NAME/sbin
cp emulator.py $BUILD_NAME/sbin/

chown root:root -R $BUILD_NAME
dpkg -b $BUILD_NAME
