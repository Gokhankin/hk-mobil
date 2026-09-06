import os
import pyodbc
from flask import Flask, render_template, jsonify, request, make_response

app = Flask(__name__)

import sys

# Ensure central config is importable
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sedna_cloud_dir = os.path.join(parent_dir, 'sedna_cloud_backup')
if sedna_cloud_dir not in sys.path:
    sys.path.insert(0, sedna_cloud_dir)

try:
    from config import get_db_connection_string
    CONN_STR = get_db_connection_string()
except Exception:
    CONN_STR = os.getenv("SEDNA_DB_CONN_STR", "DRIVER={ODBC Driver 18 for SQL Server};SERVER=192.168.0.41,1433;DATABASE=SednaAdakoy;UID=gokhan;PWD=Ad!!2025!!;TrustServerCertificate=yes;")

_global_conn = None

def get_connection():
    global _global_conn
    if _global_conn is not None:
        try:
            cursor = _global_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return _global_conn
        except Exception:
            try:
                _global_conn.close()
            except Exception:
                pass
            _global_conn = None
            
    _global_conn = pyodbc.connect(CONN_STR, timeout=5)
    return _global_conn

@app.route('/')
def home():
    res = make_response(render_template('hk_mobile.html'))
    res.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Expires'] = '0'
    return res

@app.route('/api/hk/data')
def get_data():
    try:
        import queries_hk as queries
        conn = get_connection()
        df = queries.get_hk_status(conn)
        guest_stats = queries.get_guest_stats(conn)
        bos_kirli_cnt = len(df[df['BOS_KIRLI'] == 1]) if 'BOS_KIRLI' in df.columns else 0
        guest_stats['bos_kirli'] = {'oda': int(bos_kirli_cnt)}
        room_changes = queries.get_room_changes(conn)
        late_checkouts = queries.get_late_checkouts(conn)
        items = df.to_dict(orient='records')
        return jsonify({
            "connected": True,
            "items": items,
            "guest_stats": guest_stats,
            "room_changes": room_changes,
            "late_checkouts": late_checkouts
        })
    except Exception as e:
        return jsonify({
            "connected": False,
            "error": str(e),
            "items": [],
            "room_changes": [],
            "late_checkouts": [],
            "guest_stats": {
                "arrivals": {"oda": 0, "pax": 0},
                "departures": {"oda": 0, "pax": 0},
                "inhouse": {"oda": 0, "pax": 0},
                "coci": {"oda": 0, "pax": 0},
                "bos_kirli": {"oda": 0}
            }
        })

@app.route('/api/hk/rc_history')
def get_rc_history():
    try:
        import queries_hk as queries
        target_date = request.args.get('date') # Format: YYYY-MM-DD
        conn = get_connection()
        rc_list = queries.get_room_changes(conn, target_date)
        late_list = queries.get_late_checkouts(conn, target_date)
        return jsonify({
            "success": True,
            "date": target_date,
            "room_changes": rc_list,
            "late_checkouts": late_list
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
