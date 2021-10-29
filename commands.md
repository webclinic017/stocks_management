Run VFB
Xvfb :0 -ac -screen 0 2048x1536x24

<!-- VNC: -->

/usr/bin/x11vnc -ncache 10 -ncache_cr -viewpasswd remote_view_only_pass -passwd 'Kadima2020!' -display :0 -forever -shared -logappend /var/log/x11vnc.log -bg -noipv6

<!-- Run the "eyes" application for VNC verification -->

DISPLAY=:0 xeyes &

<!-- Start: -->

DISPLAY=:0 /home/ubuntu/ibc.paper/twsstart.sh

Stop:
./stocks_management/tws/ibcstop.sh 4005

<!-- Supervisor -->

sudo systemctl restart supervisor
sudo supervisorctl status kadima_project
sudo supervisorctl restart kadima_project
