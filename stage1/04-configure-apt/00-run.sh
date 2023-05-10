#!/bin/bash -e

install -m 644 files/cellsim.list "${ROOTFS_DIR}/etc/apt/sources.list.d/"

on_chroot apt-key add - < files/gpg.key
on_chroot << EOF
apt-get update
apt-get dist-upgrade -y
EOF
