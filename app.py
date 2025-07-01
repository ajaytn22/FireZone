from flask import Flask, render_template, request, redirect, session
import sqlite3
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'supersecretkey'

placement_points = {
    1: 50, 2: 45, 3: 40, 4: 35, 5: 30, 6: 25,
    7: 20, 8: 15, 9: 10, 10: 5, 11: 3, 12: 0
}

# DB Setup
def init_db():
    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            link TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS round_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            squad TEXT NOT NULL,
            round_no INTEGER NOT NULL CHECK(round_no BETWEEN 1 AND 5),
            placement INTEGER NOT NULL,
            kills INTEGER NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# Homepage
@app.route('/')
def index():
    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()
    c.execute("SELECT name, link FROM tournaments WHERE status='Ongoing'")
    ongoing = c.fetchall()
    c.execute("SELECT name, link FROM tournaments WHERE status='Upcoming'")
    upcoming = c.fetchall()

    # Get round-wise results
    c.execute("SELECT squad, round_no, placement, kills FROM round_results")
    rows = c.fetchall()
    conn.close()

    results_by_round = defaultdict(list)
    for squad, round_no, placement, kills in rows:
        results_by_round[round_no].append({
            'squad': squad,
            'placement': placement,
            'kills': kills,
            'points': placement_points.get(placement, 0) + kills * 5
        })

    return render_template(
        'index.html',
        ongoing=ongoing,
        upcoming=upcoming,
        results_by_round=results_by_round
    )


# Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['admin'] = True
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# Admin Dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect('/login')

    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tournaments")
    tournaments = c.fetchall()

    # Fetch round results
    c.execute("SELECT id, squad, round_no, placement, kills FROM round_results")
    data = c.fetchall()
    conn.close()

    results_by_round = defaultdict(list)
    for row in data:
        round_no = row[2]
        result = {
            'id': row[0],
            'squad': row[1],
            'placement': row[3],
            'kills': row[4],
            'points': placement_points.get(row[3], 0) + row[4] * 5
        }
        results_by_round[round_no].append(result)

    return render_template('admin_dashboard.html', tournaments=tournaments, results_by_round=results_by_round, placement_points=placement_points)

# Add Tournament
@app.route('/add', methods=['POST'])
def add():
    if not session.get('admin'):
        return redirect('/login')
    name = request.form['name']
    link = request.form['link']
    status = request.form['status']
    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()
    c.execute("INSERT INTO tournaments (name, link, status) VALUES (?, ?, ?)", (name, link, status))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Delete Tournament
@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'):
        return redirect('/login')
    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()
    c.execute("DELETE FROM tournaments WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Add Single Round Result
@app.route('/add_result', methods=['POST'])
def add_result():
    if not session.get('admin'):
        return redirect('/login')
    squad = request.form['squad']
    round_no = int(request.form['round_no'])
    placement = int(request.form['placement'])
    kills = int(request.form['kills'])

    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO round_results (squad, round_no, placement, kills)
        VALUES (?, ?, ?, ?)
    ''', (squad, round_no, placement, kills))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Delete Result
@app.route('/delete_result/<int:id>')
def delete_result(id):
    if not session.get('admin'):
        return redirect('/login')
    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()
    c.execute("DELETE FROM round_results WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')


@app.route('/edit_result/<int:id>', methods=['GET', 'POST'])
def edit_result(id):
    if not session.get('admin'):
        return redirect('/login')

    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()

    if request.method == 'POST':
        squad = request.form['squad']
        round_no = int(request.form['round_no'])
        placement = int(request.form['placement'])
        kills = int(request.form['kills'])
        c.execute('''
            UPDATE round_results
            SET squad=?, round_no=?, placement=?, kills=?
            WHERE id=?
        ''', (squad, round_no, placement, kills, id))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    # GET request: Fetch existing result
    c.execute("SELECT id, squad, round_no, placement, kills FROM round_results WHERE id=?", (id,))
    result = c.fetchone()
    conn.close()

    if result:
        result_dict = {
            'id': result[0],
            'squad': result[1],
            'round_no': result[2],
            'placement': result[3],
            'kills': result[4]
        }
        return render_template('edit_result.html', result=result_dict)
    else:
        return "Result not found", 404

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
