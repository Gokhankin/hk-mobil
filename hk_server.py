import os
import pyodbc
from flask import Flask, render_template, jsonify, request, make_response

app = Flask(__name__)

# Environment Secret Loader (.env)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)
except ImportError:
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

# Database Connection Secret String loaded from environment
CONN_STR = os.getenv(
    "CONN_STR",
    f"DRIVER={os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')};"
    f"SERVER={os.getenv('DB_SERVER', '192.168.0.41,1433')};"
    f"DATABASE={os.getenv('DB_NAME', 'SednaAdakoy')};"
    f"UID={os.getenv('DB_USER', 'gokhan')};"
    f"PWD={os.getenv('DB_PASS', 'Ad!!2025!!')};"
    "TrustServerCertificate=yes;"
)

def get_connection():
    return pyodbc.connect(CONN_STR)

@app.route('/')
def home():
    res = make_response(render_template('hk_mobile.html'))
    res.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Expires'] = '0'
    return res

@app.route('/api/hk/data')
def get_data():
    conn = None
    try:
        import queries_hk as queries
        conn = get_connection()
        df = queries.get_hk_status(conn)
        guest_stats = queries.get_guest_stats(conn)
        items = df.to_dict(orient='records')
        return jsonify({
            "connected": True,
            "items": items,
            "guest_stats": guest_stats
        })
    except Exception as e:
        return jsonify({
            "connected": False,
            "error": str(e),
            "items": [],
            "guest_stats": {
                "arrivals": {"oda": 0, "pax": 0},
                "departures": {"oda": 0, "pax": 0},
                "inhouse": {"oda": 0, "pax": 0}
            }
        })
    finally:
        if conn:
            conn.close()

@app.route('/api/hk/maids')
def get_maids():
    try:
        import queries_hk as queries
        conn = get_connection()
        maids = queries.get_maids(conn)
        conn.close()
        return jsonify(maids)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hk/update', methods=['POST'])
def update_hk():
    try:
        import queries_hk as queries
        data = request.json
        room = data.get('room')
        status = data.get('status')
        maid = data.get('maid')
        if not room or status is None:
            return jsonify({"error": "Eksik parametre"}), 400
            
        conn = get_connection()
        queries.set_hk_status(conn, room, int(status), maid)
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hk/update_evening', methods=['POST'])
def update_evening():
    try:
        import queries_hk as queries
        data = request.json
        room = data.get('room')
        status = data.get('status')
        maid = data.get('maid')
        if not room or status is None:
            return jsonify({"error": "Eksik parametre"}), 400
        conn = get_connection()
        queries.set_evening_status(conn, room, int(status), maid)
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)