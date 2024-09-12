[Unit]
Description=gunicorn service
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/workspace/TradeSetup
ExecStart=/home/ubuntu/workspace/tenv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/home/ubuntu/workspace/TradeSetup/TradeSetup.sock \
          TradeSetup.wsgi:application

[Install]
WantedBy=multi-user.target

server {
    listen 80;
    server_name 15.206.151.193;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/ubuntu/workspace/TradeSetup;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix://home/ubuntu/workspace/TradeSetup/TradeSetup.sock;
    }
    location /static {
        alias /home/ubuntu/workspace/TradeSetup/static;
    }
}
