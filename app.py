from flask import Flask, render_template, request, redirect, session
import sqlite3

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
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            squad TEXT NOT NULL,
            r1_placement INTEGER, r1_kills INTEGER,
            r2_placement INTEGER, r2_kills INTEGER,
            r3_placement INTEGER, r3_kills INTEGER,
            r4_placement INTEGER, r4_kills INTEGER,
            r5_placement INTEGER, r5_kills INTEGER
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
    c.execute("SELECT * FROM results")
    raw_results = c.fetchall()
    conn.close()

    results = []
    for r in raw_results:
        squad = r[1]
        total_kills = r[3] + r[5] + r[7] + r[9] + r[11]
        total_points = (
            placement_points.get(r[2], 0) + r[3]*5 +
            placement_points.get(r[4], 0) + r[5]*5 +
            placement_points.get(r[6], 0) + r[7]*5 +
            placement_points.get(r[8], 0) + r[9]*5 +
            placement_points.get(r[10], 0) + r[11]*5
        )
        results.append((squad, '-', total_kills, total_points))

    results_sorted = sorted(results, key=lambda x: x[3], reverse=True)

    return render_template('index.html', ongoing=ongoing, upcoming=upcoming, results=results_sorted)

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
    c.execute("SELECT * FROM results")
    results = c.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', tournaments=tournaments, results=results, placement_points=placement_points)

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

# Add Full Result (5 rounds)
@app.route('/add_result', methods=['POST'])
def add_result():
    if not session.get('admin'):
        return redirect('/login')
    squad = request.form['squad']
    try:
        data = []
        for i in range(1, 6):
            placement = int(request.form.get(f'r{i}_placement', 0))
            kills = int(request.form.get(f'r{i}_kills', 0))
            data.extend([placement, kills])

        conn = sqlite3.connect('tournaments.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO results (
                squad, 
                r1_placement, r1_kills,
                r2_placement, r2_kills,
                r3_placement, r3_kills,
                r4_placement, r4_kills,
                r5_placement, r5_kills
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (squad, *data))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    except Exception as e:
        return f"Error: {e}"

# Delete Result
@app.route('/delete_result/<int:id>')
def delete_result(id):
    if not session.get('admin'):
        return redirect('/login')
    conn = sqlite3.connect('tournaments.db')
    c = conn.cursor()
    c.execute("DELETE FROM results WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
