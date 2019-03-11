[uwsgi]
;virtualenv = /opt/cloudcompiler
module = cloudcompiler:app

; spawn the master and 4 processes with 8 threads each
http = 0.0.0.0:5000
;http = 127.0.0.1:8082
master = true
processes = 4
threads = 8

; allow large file uploads
limit-post = 5242880

; various other explicit defaults
post-buffering = 65536
thunder-lock = true
disable-logging = true
enable-threads = true
single-interpreter = true
lazy-apps = true
log-x-forwarded-for = true
