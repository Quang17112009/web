from flask import Flask, request, jsonify, render_template
import json
import os
import secrets # Dùng để tạo chuỗi ngẫu nhiên, bảo mật hơn
import datetime # Dùng để thêm thông tin ngày hết hạn

app = Flask(__name__)

# Tên file chứa các key hợp lệ
VALID_KEYS_FILE = 'valid_keys.json'
# Tên file cho trang admin (chỉ cần HTML tĩnh)
ADMIN_PAGE = 'admin.html'

# --- Hàm quản lý file key ---
def load_valid_keys():
    """Tải danh sách key hợp lệ từ file JSON."""
    if os.path.exists(VALID_KEYS_FILE):
        with open(VALID_KEYS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # Trả về rỗng nếu file bị lỗi định dạng JSON
    return {} # Trả về dictionary rỗng nếu file không tồn tại

def save_valid_keys(keys):
    """Lưu danh sách key hợp lệ vào file JSON."""
    with open(VALID_KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

# --- Endpoint cho trang đăng nhập (frontend) ---
@app.route('/')
def index():
    """Hiển thị trang đăng nhập chính."""
    # Giả định file index.html nằm trong thư mục 'templates' hoặc cùng cấp với app.py
    return render_template('index.html')

# --- Endpoint để xác thực key từ frontend ---
@app.route('/verify-key', methods=['POST'])
def verify_key():
    """Kiểm tra tính hợp lệ của key người dùng gửi lên."""
    data = request.json
    entered_key = data.get('key')

    if not entered_key:
        return jsonify({'isValid': False, 'message': 'Key không được để trống.'}), 400

    valid_keys = load_valid_keys()

    if entered_key in valid_keys:
        key_info = valid_keys[entered_key]
        if key_info.get('status') == 'active':
            # Kiểm tra ngày hết hạn
            expires_str = key_info.get('expires')
            if expires_str:
                expires_date = datetime.datetime.strptime(expires_str, '%Y-%m-%d').date()
                if datetime.date.today() > expires_date:
                    return jsonify({'isValid': False, 'message': 'Key đã hết hạn.'})

            # Có thể thêm logic: đánh dấu key đã sử dụng, giới hạn lượt dùng, v.v.
            return jsonify({'isValid': True, 'message': 'Key hợp lệ!'})
        else:
            return jsonify({'isValid': False, 'message': 'Key không hoạt động hoặc đã bị vô hiệu hóa.'})
    else:
        return jsonify({'isValid': False, 'message': 'Key không tồn tại.'})

# --- Endpoint cho trang admin để tạo key ---
@app.route('/admin')
def admin_page():
    """Hiển thị trang admin (để tạo key)."""
    # Bạn có thể bảo vệ trang này bằng mật khẩu hoặc các phương thức xác thực khác
    return render_template('admin.html') # Giả định admin.html nằm trong thư mục 'templates'

@app.route('/generate-key', methods=['POST'])
def generate_key():
    """Tạo một key mới và lưu vào danh sách key hợp lệ."""
    data = request.json
    # Lấy thời gian hết hạn từ request, mặc định là 30 ngày tới
    duration_days = int(data.get('duration_days', 30))
    key_prefix = data.get('prefix', 'ABYSS-')

    new_key = key_prefix + secrets.token_urlsafe(16).upper() # Tạo key ngẫu nhiên 16 ký tự hoa
    
    expires_date = datetime.date.today() + datetime.timedelta(days=duration_days)
    expires_str = expires_date.strftime('%Y-%m-%d')

    keys = load_valid_keys()
    if new_key in keys: # Đảm bảo key là duy nhất (tránh trùng lặp hiếm khi xảy ra)
        return jsonify({'success': False, 'message': 'Key trùng lặp, vui lòng thử lại.'}), 500

    keys[new_key] = {
        'status': 'active',
        'created_at': datetime.date.today().strftime('%Y-%m-%d'),
        'expires': expires_str,
        'duration_days': duration_days
    }
    save_valid_keys(keys)
    
    return jsonify({'success': True, 'key': new_key, 'expires': expires_str})

# --- Endpoint để lấy danh sách key (cho trang admin) ---
@app.route('/get-keys', methods=['GET'])
def get_keys():
    """Trả về danh sách tất cả các key hiện có."""
    keys = load_valid_keys()
    return jsonify(keys)

# --- Endpoint để vô hiệu hóa/kích hoạt key (cho trang admin) ---
@app.route('/toggle-key-status', methods=['POST'])
def toggle_key_status():
    data = request.json
    key_to_toggle = data.get('key')
    
    keys = load_valid_keys()
    if key_to_toggle in keys:
        current_status = keys[key_to_toggle]['status']
        new_status = 'inactive' if current_status == 'active' else 'active'
        keys[key_to_toggle]['status'] = new_status
        save_valid_keys(keys)
        return jsonify({'success': True, 'message': f'Đã chuyển trạng thái key {key_to_toggle} sang {new_status}.', 'new_status': new_status})
    return jsonify({'success': False, 'message': 'Key không tồn tại.'}), 404


if __name__ == '__main__':
    # Đặt thư mục 'templates' nếu bạn sử dụng render_template
    # app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app.run(debug=True, port=5000)
