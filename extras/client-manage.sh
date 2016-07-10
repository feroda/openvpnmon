#!/bin/bash

# It is very important that this script exits on failure
# -e option it is here to provide this feature
# but be careful to write right execution steps
set -e

IPTABLES=`which iptables`
OPENVPN_BASE_DIR="/etc/openvpn"
AUTOMATONS_NETWORK_NAME="acs"

if [[ -z $IPTABLES ]]; then
    echo "iptables not found. Need to install it or add to \$PATH" 1>&2
fi
if [[ -z $OPENVPN_BASE_DIR ]]; then
    echo "\$OPENVPN_BASE_DIR var not set." 1>&2
fi

#--- configuration ends here ---#

function iptables_remove_rule() {
    pars=""
    if [ "$1" != "NOPAR" ]; then
        pars=$pars" --in-interface $1";
    fi
    if [ "$2" != "NOPAR" ]; then
        pars=$pars" --out-interface $2";
    fi
    if [ "$3" != "NOPAR" ]; then
        pars=$pars" --src $3";
    fi
    if [ "$4" != "NOPAR" ]; then
        pars=$pars" --dst $4";
    fi
    if [ "$5" != "NOPAR" ]; then
        pars=$pars" -j $5";
    fi
    $IPTABLES -D FORWARD $pars
}

case "$1" in

    enable)
        CLIENT=$2 #client common name
        NETWORK=$3 #example: acs
        VPN_IP=$4 #example: 10.0.0.5
        VPN_NETMASK=$5 #example: 255.255.255.0

        if [ $NETWORK = $AUTOMATONS_NETWORK_NAME ]; then
            CCD_DIR=$OPENVPN_BASE_DIR/ccd-ewons
            if [ ! -e $CCD_DIR/$CLIENT ]; then
                mkdir -p $CCD_DIR
                baseaddr="$(echo $VPN_IP | cut -d. -f1-3)"
                lsv="$(echo $VPN_IP | cut -d. -f4)"
                # Edge cases (255) never happens. For valid IPs passed here take a look at
                # http://openvpn.net/index.php/open-source/documentation/howto.html#policy
                VPN_IP_P2P="$baseaddr.$(( $lsv + 1 ))"
                echo "ifconfig-push $VPN_IP $VPN_IP_P2P" >> $CCD_DIR/$CLIENT;
                #Add name to DNS
                echo "$VPN_IP $CLIENT $CLIENT" >> $OPENVPN_BASE_DIR/ewon_hosts;
                echo killall -HUP dnsmasq
            fi
        else
            CCD_DIR=$OPENVPN_BASE_DIR/ccd
            if [ ! -e $CCD_DIR/$CLIENT ]; then
                mkdir -p $CCD_DIR
                echo "ifconfig-push $VPN_IP $VPN_NETMASK" >> $CCD_DIR/$CLIENT;
            fi
        fi

        # Adds new IP to Munin monitoring system
        # mon_ip VPN_IP
        echo $@;
        ;;

    access-allow)
        INIFACE=$2
        INIP=$3
        OUTIFACE=$4
        OUTIP=$5

        # Test for iptables to work
        $IPTABLES -L INPUT 1

        echo $@;
        echo $IPTABLES -A FORWARD --in-interface $INIFACE --src $INIP --out-interface $OUTIFACE --dst $OUTIP -p tcp --destination-port 80 -j ACCEPT
        echo $IPTABLES -A FORWARD --in-interface $OUTIFACE --src $OUTIP --out-interface $INIFACE --dst $INIP -p tcp --source-port 80 -j ACCEPT
        # Remove the rule that prevents the customer to access any new destination
        # add it again as last rule
        echo $IPTABLES -D FORWARD --in-interface $INIFACE --src $INIP -j DROP
        echo $IPTABLES -A FORWARD --in-interface $INIFACE --src $INIP -j DROP

        ;;

    access-flush)
        INIFACE=$2
        INIP=$3

        # Test for iptables to work
        $IPTABLES -L INPUT 1

        $IPTABLES -L block -n -v | grep $INIP | awk '{ print $6" "$7" "$8" "$9" "$3 }'| while read line; do
            cmdline=${line//\*/NOPAR}
            iptables_remove_rule $cmdline;
        done
        ;;
    *)
        echo "Usage <enable,access-allow,access-block> [...]";
        ;;
esac
