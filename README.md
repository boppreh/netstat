netstat
=======

Detects changes in network connection quality and notifies the user.

Using simple `ping` commands to specific hosts it detects availability, speed
and packet loss problems in the local network, internet connection, dns server
and regular internet use (currently google search).

Whenever a status change is detected (new problem appeared or old problem
disappeared) it notifies the user with a tray balloon.
