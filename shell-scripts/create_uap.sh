[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash
# Unblock all devices (wlan0 if eth0 is connected). Sometimes they are soft-blocked because of WLAN - LAN switching
rfkill unblock all
# Create the virtual device
echo '>>> Create the virtual device uap0'
/sbin/iw dev wlan0 interface add uap0 type __ap
ip link set uap0 up
ip addr add 192.168.4.1/24 broadcast 192.168.4.255 dev uap0
ifup uap0
# Fetch wifi channel
CHANNEL=`iwlist wlan0 channel | grep Current | sed 's/.*Channel \([0-9]*\).*/\1/g'`
# if no network connected
if [[ -z "$CHANNEL" ]]; then
   echo "Info: Currently not connected to a network."
   CHANNEL="1"
fi
# prevent using 5Ghz (uap0: IEEE 802.11 Hardware does not support configured channel)
#HWMODE=g 2,4GHz
#HWMODE=a 5 GHz
if [[ "$CHANNEL" -gt "13" ]]; then
   echo "Info: A 5GHz (Channel: $CHANNEL) WiFi is connected."
   HWMODE="g"
   CHANNEL="1"
else
   echo "Info: Select 2,4GHz (Channel: $CHANNEL) for AccessPoint"
   HWMODE="g"
fi
export CHANNEL && export HWMODE
# Create the config for hostapd
cat /etc/hostapd/hostapd.conf.tmpl | envsubst > /etc/hostapd/hostapd.conf
