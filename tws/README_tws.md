# Based on instruction from: https://dimon.ca/how-to-setup-ibc-and-tws-on-headless-ubuntu-in-10-minutes/

# Stand alone TWS:
https://www.interactivebrokers.com/en/index.php?f=15875


## After installing X11VNC and the TWS
/usr/bin/x11vnc -ncache 10 -ncache_cr -viewpasswd remote_view_only_pass -passwd '!Q2w3e4r%T' -display :0 -forever -shared -logappend /var/log/x11vnc.log -bg -noipv6

DISPLAY=:0 /home/alf_naboo_id/ibc.paper/twsstart.sh

To Stop:
./ibcstop.sh 4005
