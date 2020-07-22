#!/bin/bash -e
install -v -m 644 files/interfaces.wlan         "${ROOTFS_DIR}/etc/network/interfaces.wlan"
install -v -m 644 files/interfaces.eth          "${ROOTFS_DIR}/etc/network/interfaces.eth"
install -v -m 644 files/interfaces.wlan         "${ROOTFS_DIR}/etc/network/interfaces"

install -v -m 755 files/bridge_switch.sh        "${ROOTFS_DIR}/sbin/bridge_switch.sh"
install -v -m 755 files/emulator.py             "${ROOTFS_DIR}/sbin/emulator.py"
install -v -d                                   "${ROOTFS_DIR}/etc/piem"
install -v -m 644 files/piem-config.json        "${ROOTFS_DIR}/etc/piem/config.json"
install -v -m 644 files/piem.service            "${ROOTFS_DIR}/etc/systemd/system/"

install -v -m 600 files/hostapd.conf            "${ROOTFS_DIR}/etc/hostapd/hostapd.conf"

install -v -d					"${ROOTFS_DIR}/etc/systemd/system/dhcpcd.service.d"
install -v -m 644 files/wait.conf		"${ROOTFS_DIR}/etc/systemd/system/dhcpcd.service.d/"

install -v -d					"${ROOTFS_DIR}/etc/wpa_supplicant"
install -v -m 600 files/wpa_supplicant.conf	"${ROOTFS_DIR}/etc/wpa_supplicant/wpa_supplicant.conf"

on_chroot << EOF
systemctl enable piem
EOF



#install -v -m 644 files/sch_netem.ko             "${ROOTFS_DIR}/etc/sch_netem.ko"

# need better way to do this uname -r not working
#on_chroot << EOF
#rm -f /sbin/tc
#ls -l /lib/modules/
#mv /lib/modules/4.19.66-v7+/kernel/net/sched/sch_netem.ko /lib/modules/4.19.66-v7+/kernel/net/sched/sch_netem.ko.bak
#mv /etc/sch_netem.ko /lib/modules/4.19.66-v7+/kernel/net/sched/sch_netem.ko
#EOF

#install -v -m 755 files/tc                       "${ROOTFS_DIR}/sbin/tc"



#if [ -v WPA_COUNTRY ]; then
#	echo "country=${WPA_COUNTRY}" >> "${ROOTFS_DIR}/etc/wpa_supplicant/wpa_supplicant.conf"
#fi
#
#if [ -v WPA_ESSID ] && [ -v WPA_PASSWORD ]; then
#on_chroot <<EOF
#set -o pipefail
#wpa_passphrase "${WPA_ESSID}" "${WPA_PASSWORD}" | tee -a "/etc/wpa_supplicant/wpa_supplicant.conf"
#EOF
#elif [ -v WPA_ESSID ]; then
#cat >> "${ROOTFS_DIR}/etc/wpa_supplicant/wpa_supplicant.conf" << EOL
#
#network={
#	ssid="${WPA_ESSID}"
#	key_mgmt=NONE
#}
#EOL
#fi

# Disable wifi on 5GHz models
mkdir -p "${ROOTFS_DIR}/var/lib/systemd/rfkill/"
echo 1 > "${ROOTFS_DIR}/var/lib/systemd/rfkill/platform-3f300000.mmcnr:wlan"
echo 1 > "${ROOTFS_DIR}/var/lib/systemd/rfkill/platform-fe300000.mmcnr:wlan"
