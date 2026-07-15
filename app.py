import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

PER_PAGE = 5
DB_PATH = '/tmp/people.db' if os.environ.get('RENDER') else 'people.db'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS persons
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  position TEXT NOT NULL)''')

    if c.execute("SELECT COUNT(*) FROM persons").fetchone()[0] == 0:
        sample_data = []
        names = []
        positions = []

        for i in range(20):
            sample_data.append((f'{names[i % 20]}{i + 1}号', positions[i % 10]))

        c.executemany("INSERT INTO persons (name, position) VALUES (?, ?)", sample_data)
        conn.commit()
    conn.close()


init_db()


def get_db():
    return sqlite3.connect(DB_PATH)


@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM persons")
    total_count = c.fetchone()[0]
    conn.close()

    total_pages = (total_count + PER_PAGE - 1) // PER_PAGE if total_count > 0 else 1

    # 页码边界检查
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * PER_PAGE

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM persons LIMIT ? OFFSET ?", (PER_PAGE, offset))
    persons = c.fetchall()
    conn.close()

    return render_template('index.html',
                           persons=persons,
                           page=page,
                           total_pages=total_pages,
                           total_count=total_count)


@app.route('/add', methods=['POST'])
def add_person():
    name = request.form.get('name', '').strip()
    position = request.form.get('position', '').strip()

    if not name or not position:
        flash('❌ 姓名和职位都不能为空！', 'error')
        return redirect(url_for('index'))

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO persons (name, position) VALUES (?, ?)", (name, position))
        conn.commit()
        conn.close()
        flash(f'✅ 成功添加：{name} - {position}', 'success')
    except Exception as e:
        flash(f'❌ 添加失败：{str(e)}', 'error')

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM persons")
    total = c.fetchone()[0]
    conn.close()
    last_page = (total + PER_PAGE - 1) // PER_PAGE

    return redirect(url_for('index', page=last_page))


@app.route('/delete/<int:person_id>')
def delete_person(person_id):
    page = request.args.get('page', 1, type=int)

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT name FROM persons WHERE id = ?", (person_id,))
        person = c.fetchone()

        if person:
            c.execute("DELETE FROM persons WHERE id = ?", (person_id,))
            conn.commit()
            flash(f'✅ 已删除：{person[0]}', 'success')
        else:
            flash('❌ 该人员不存在！', 'error')
        conn.close()
    except Exception as e:
        flash(f'❌ 删除失败：{str(e)}', 'error')

    # 删除后重新计算总页数，如果当前页超出范围则回退
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM persons")
    total_count = c.fetchone()[0]
    conn.close()

    total_pages = (total_count + PER_PAGE - 1) // PER_PAGE if total_count > 0 else 1

    if page > total_pages:
        page = max(total_pages, 1)

    return redirect(url_for('index', page=page))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)