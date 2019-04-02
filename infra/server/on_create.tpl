#!/bin/bash
yum update -y
yum install docker -y
usermod -a -G docker ec2-user
systemctl enable docker
systemctl start docker
cat > /etc/systemd/system/my_app.service << EOF
[Unit]
Description=My Docker App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user
ExecStart=/bin/docker run -p 80:8000 ${repo_url}
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl enable my_app
systemctl start my_app
