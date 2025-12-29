#!/bin/bash

# OWASP10 파일 서비스 설치 스크립트

echo "=== OWASP10 취약한 파일 서비스 설치 ==="
echo ""

# Python3와 pip 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    exit 1
fi

echo "✓ Python3 확인 완료"

# 의존성 설치
echo "📦 Flask 설치 중..."
pip3 install -r requirements.txt

# systemd 서비스 파일 생성
SERVICE_FILE="/etc/systemd/system/owasp-fileservice.service"
CURRENT_DIR=$(pwd)

echo "📝 systemd 서비스 파일 생성 중..."

sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=OWASP10 Vulnerable File Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$PATH"
ExecStart=/usr/bin/python3 $CURRENT_DIR/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# systemd 리로드 및 서비스 활성화
echo "🔄 systemd 리로드 중..."
sudo systemctl daemon-reload

echo "✅ 서비스 활성화 중..."
sudo systemctl enable owasp-fileservice.service

echo ""
echo "=== 설치 완료 ==="
echo ""
echo "서비스 제어 명령어:"
echo "  시작: sudo systemctl start owasp-fileservice"
echo "  중지: sudo systemctl stop owasp-fileservice"
echo "  상태: sudo systemctl status owasp-fileservice"
echo "  로그: sudo journalctl -u owasp-fileservice -f"
echo ""
echo "서비스는 http://0.0.0.0:8080 에서 실행됩니다."

