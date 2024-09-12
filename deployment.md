sudo apt update

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.9
python3.9 --version 

alias python=python3.9


git clone https://github.com/sainithin498/TradeSetup.git


sudo apt update
sudo apt install python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl


sudo -u postgres psql
CREATE DATABASE myproject;
ALTER USER postgres PASSWORD 'DvaraEDev@1234#';

ALTER ROLE myprojectuser SET client_encoding TO 'utf8';
ALTER ROLE vcreadonly SET timezone TO '+05:30';
\q

python3 -m venv myprojectenv
source tenv/bin/activate

pip install -r req_11_09.txt


wget -N https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /tmp/google-chrome-stable_current_amd64.deb

sudo apt install -y /tmp/google-chrome-stable_current_amd64.deb

wget -qP /home/ubuntu/     https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.137/linux64/chromedriver-linux64.zip
mv /home/ubuntu/chromedriver-linux64.zip /usr/local/bin/
unzip chromedriver-linux64.zip

chmod -R 777 workspace/


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


sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

sudo systemctl status gunicorn

sudo journalctl -u gunicorn -r

cd /etc/nginx/conf.d/
mv default.conf default-old.conf
touch default.conf
sudo nano default.conf

server {
    listen 80;
    server_name 65.1.100.163;

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

sudo nginx -t
sudo systemctl restart nginx
mkdir cron_logs in workspace dir

sudo timedatectl set-timezone Asia/Kolkata

iff error TradeSetup.sock failed (13: Permission denied) 
  /etc/nginx/nginx.conf
  change user to root




chmod -R 777 workspace/

15 09 * * MON-FRI /home/ubuntu/workspace/tenv/bin/python /home/ubuntu/workspace/TradeSetup/manage.py websocket >> /home/ubuntu/workspace/cron_logs/websocket.log 2>&1