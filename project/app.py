from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import heapq, os, datetime, zipfile
from collections import Counter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'compressed'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# -------------------- Models --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(120))
    original_size = db.Column(db.Integer)
    compressed_size = db.Column(db.Integer)
    compression_ratio = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

with app.app_context():
    db.create_all()

# -------------------- Huffman Compression --------------------
class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(data):
    freq = Counter(data)
    heap = [HuffmanNode(char, freq[char]) for char in freq]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left, merged.right = left, right
        heapq.heappush(heap, merged)
    return heap[0]

def build_codes(node, prefix="", codes=None):
    if codes is None:
        codes = {}
    if node:
        if node.char is not None:
            codes[node.char] = prefix or "0"
        build_codes(node.left, prefix + "0", codes)
        build_codes(node.right, prefix + "1", codes)
    return codes

def save_huffman_tree_image(codes, filepath):
    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)

    sorted_items = sorted(codes.items(), key=lambda x: str(x[1]))
    labels = [f"'{k}': {v}" for k, v in sorted_items]
    y = range(len(labels))
    ax.barh(y, [len(str(v)) for k, v in sorted_items], color='skyblue')
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Code Length')
    fig.tight_layout()
    canvas.print_figure(filepath)

# -------------------- Routes --------------------
@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/about')
def about(): 
    return render_template('about.html')

@app.route('/applications')
def applications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('applications.html')

@app.route('/resources')
def resources(): 
    return render_template('resources.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['logged_in'] = True
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = generate_password_hash(data.get('password'))
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already exists'})
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    session['logged_in'] = True
    return jsonify({'success': True})

@app.route('/check_login')
def check_login():
    response = jsonify(logged_in=session.get('logged_in', False))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    uploads = History.query.filter_by(user_id=user_id).order_by(History.timestamp.desc()).all()
    return render_template('dashboard.html', uploads=uploads)

@app.route('/compress/<file_type>', methods=['POST'])
def compress(file_type):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    try:
        file = request.files['file']
        ext = os.path.splitext(file.filename)[1]
        filename = f"{datetime.datetime.now().timestamp()}{ext}"
        raw_data = file.read()
        original_size = len(raw_data)

        if ext.lower() in ['.txt', '.csv', '.log']:
            try:
                raw_text = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                return jsonify({'success': False, 'message': 'Text file decoding failed.'}), 400
            symbols = raw_text
        elif ext.lower() == '.zip':
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(zip_path, 'wb') as f:
                f.write(raw_data)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extracted_path = os.path.join(app.config['UPLOAD_FOLDER'], f"extracted_{datetime.datetime.now().timestamp()}")
                os.makedirs(extracted_path, exist_ok=True)
                zip_ref.extractall(extracted_path)
                symbols = ""
                for root_dir, _, files in os.walk(extracted_path):
                    for file_name in files:
                        file_path = os.path.join(root_dir, file_name)
                        with open(file_path, 'rb') as file_in_zip:
                            symbols += file_in_zip.read().decode(errors='ignore')
        else:
            symbols = list(raw_data)

        root = build_huffman_tree(symbols)
        codes = build_codes(root)
        compressed_bits = ''.join(codes[symbol] for symbol in symbols)

        compressed_bytes = bytearray()
        for i in range(0, len(compressed_bits), 8):
            byte = compressed_bits[i:i+8]
            compressed_bytes.append(int(byte.ljust(8, '0'), 2))
        compressed_size = len(compressed_bytes)

        compressed_filename = f"{datetime.datetime.now().timestamp()}_compressed{ext}"
        compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], compressed_filename)
        with open(compressed_path, 'wb') as f:
            f.write(compressed_bytes)

        tree_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}_tree.png")
        save_huffman_tree_image(codes, tree_path)

        history = History(user_id=session['user_id'], filename=file.filename,
                          original_size=original_size, compressed_size=compressed_size,
                          compression_ratio=(compressed_size / original_size) * 100)
        db.session.add(history)
        db.session.commit()

        return jsonify({
            'success': True,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'ratio': (compressed_size / original_size) * 100,
            'tree_image': f"/download/{os.path.basename(tree_path)}",
            'compressed_file': f"/download/{os.path.basename(compressed_path)}"
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
