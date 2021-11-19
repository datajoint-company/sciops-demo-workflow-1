#!/bin/bash
# Need to build and install: https://docs.aws.amazon.com/efs/latest/ug/overview-amazon-efs-utils.html
# Remember to run this script with sudo
mount -t efs -o tls,accesspoint=fsap-0bc63e40c6bffd915 fs-5271d529: /mnt/sciops