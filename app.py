from flask import Flask, request, send_file, render_template, Response
import os
import random

app = Flask(__name__)

# 의도적으로 debug=True로 설정 (A10: Server-Side Request Forgery + Insufficient Logging & Monitoring)
app.config['DEBUG'] = True

# 프로젝트 디렉토리 기준 경로
import pathlib
BASE_DIR = pathlib.Path(__file__).parent.resolve()
UPLOAD_ROOT = f"{BASE_DIR}/backup/uploads/"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    의도적인 취약점: A10 - Server-Side Request Forgery (SSRF)
    에러 메시지에 내부 경로 정보 노출
    """
    try:
        # 업로드 요청 시 임시 파일명으로 서버에 저장 
        tmp_filename = f"tmp_{random.randint(100000, 999999)}"
        save_path = os.path.join(UPLOAD_ROOT, tmp_filename)
        
        # 의도적으로 항상 실패 (읽기 전용 모드)
        # 실제 파일을 쓰려고 시도하지만 실패
        raise OSError(28, "No space left on device")
        
    except OSError as e:
        ##########  A10 취약점 -> 에러 메시지에 내부 경로 노출
        error_message = f"Error: {save_path} upload failed\n"
        return Response(error_message, status=500, mimetype='text/plain')

@app.route('/download')
def download():
    """
    의도적인 취약점: A01 - Path Traversal (Broken Access Control)
    path 파라미터에 대한 검증이 없어 임의의 파일 접근 가능
    """
    path = request.args.get('path', '')
    
    if not path:
        return Response("Error: Missing 'path' parameter\nUsage: /download?path=<filepath>\n", status=400, mimetype='text/plain')
    
    try:
        ##########  A01 취약점 -> path traversal 취약점 (경로 검증 없음)
        # 사용자가 ../../../etc/passwd 같은 경로로 시스템 파일 접근 가능
        
        # 파일이 존재하는지 확인
        if os.path.exists(path):
            # 파일인 경우 다운로드
            if os.path.isfile(path):
                return send_file(path, as_attachment=True, download_name=os.path.basename(path))
            else:
                return Response(f"Error: {path} is a directory, not a file\n", status=400, mimetype='text/plain')
        else:
            return Response(f"Error: File not found at path: {path}\n", status=404, mimetype='text/plain')
            
    except Exception as e:
        return Response(f"Error accessing file: {str(e)}\n", status=500, mimetype='text/plain')

if __name__ == '__main__':
    # 내부에서만 바인딩 (외부에서는 filtered)
    app.run(host='127.0.0.1', port=8080, debug=True)

