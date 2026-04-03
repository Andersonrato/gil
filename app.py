# Sistema Profissional Completo - Salão (Versão Avançada)
# Inclui: WhatsApp, Financeiro avançado, Preparado para deploy

from flask import Flask, render_template_string, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = 'segredo123'

conn = sqlite3.connect('salao.db', check_same_thread=False)
cursor = conn.cursor()

# Tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    zap TEXT,
    servico TEXT,
    preco REAL,
    data TEXT,
    hora TEXT,
    profissional TEXT
)
''')

conn.commit()

# Usuário padrão
try:
    cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()
except:
    pass

# Página principal
home_page = '''
<!DOCTYPE html>
<html>
<head>
<link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.css' rel='stylesheet' />
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.js'></script>
<style>
body { font-family: Arial; background:#f4f6f9; }
#calendar { max-width: 900px; margin: 40px auto; }
.top { text-align:center; }
button { padding:5px; margin-top:5px; }
</style>
</head>
<body>

<h2 class="top">Agenda Profissional</h2>
<div class="top">
<a href="/financeiro">Financeiro</a> |
<a href="/logout">Sair</a>
</div>

<div id='calendar'></div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    var calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        selectable: true,

        dateClick: function(info) {
            window.location.href = '/novo?data=' + info.dateStr;
        },

        eventClick: function(info) {
            window.location.href = '/detalhes/' + info.event.id;
        },

        events: '/eventos'
    });

    calendar.render();
});
</script>

</body>
</html>
'''

# Página detalhes com WhatsApp
@app.route('/detalhes/<int:id>')
def detalhes(id):
    cursor.execute("SELECT * FROM agendamentos WHERE id=?", (id,))
    a = cursor.fetchone()

    link = f"https://wa.me/55{a[2]}?text=Olá {a[1]}, lembrando seu horário de {a[3]} dia {a[5]} às {a[6]}"

    return f'''
    <h2>{a[1]}</h2>
    <p>{a[3]} - R$ {a[4]}</p>
    <p>{a[5]} {a[6]}</p>
    <p>Profissional: {a[7]}</p>

    <a href="{link}" target="_blank"><button>Enviar WhatsApp</button></a><br><br>
    <a href="/editar/{id}">Editar</a>
    '''

# Financeiro avançado
@app.route('/financeiro')
def financeiro():
    cursor.execute("SELECT SUM(preco) FROM agendamentos")
    total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT servico, SUM(preco) FROM agendamentos GROUP BY servico")
    servicos = cursor.fetchall()

    html = f"<h2>Total: R$ {total}</h2>"
    for s in servicos:
        html += f"<p>{s[0]}: R$ {s[1]}</p>"

    return html

# Eventos calendário
@app.route('/eventos')
def eventos():
    cursor.execute("SELECT * FROM agendamentos")
    dados = cursor.fetchall()

    eventos = []
    for a in dados:
        eventos.append({
            "id": a[0],
            "title": f"{a[1]} - {a[3]}",
            "start": f"{a[5]}T{a[6]}"
        })

    return jsonify(eventos)

# Novo agendamento
@app.route('/novo', methods=['GET','POST'])
def novo():
    if request.method=='POST':
        cursor.execute("INSERT INTO agendamentos (nome,zap,servico,preco,data,hora,profissional) VALUES (?,?,?,?,?,?,?)", (
            request.form['nome'], request.form['zap'], request.form['servico'], request.form['preco'], request.form['data'], request.form['hora'], request.form['profissional']))
        conn.commit()
        return redirect('/home')

    return '''
    <form method="post">
    Nome:<input name="nome"><br>
    Zap:<input name="zap"><br>
    Serviço:<input name="servico"><br>
    Preço:<input name="preco"><br>
    Profissional:<input name="profissional"><br>
    Data:<input type="date" name="data"><br>
    Hora:<input type="time" name="hora"><br>
    <button>Salvar</button>
    </form>
    '''

# Editar
@app.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    if request.method=='POST':
        cursor.execute("UPDATE agendamentos SET nome=?,zap=?,servico=?,preco=?,data=?,hora=?,profissional=? WHERE id=?", (
            request.form['nome'], request.form['zap'], request.form['servico'], request.form['preco'], request.form['data'], request.form['hora'], request.form['profissional'], id))
        conn.commit()
        return redirect('/home')

    cursor.execute("SELECT * FROM agendamentos WHERE id=?", (id,))
    a = cursor.fetchone()

    return f'''
    <form method="post">
    Nome:<input name="nome" value="{a[1]}"><br>
    Zap:<input name="zap" value="{a[2]}"><br>
    Serviço:<input name="servico" value="{a[3]}"><br>
    Preço:<input name="preco" value="{a[4]}"><br>
    Profissional:<input name="profissional" value="{a[7]}"><br>
    Data:<input type="date" name="data" value="{a[5]}"><br>
    Hora:<input type="time" name="hora" value="{a[6]}"><br>
    <button>Salvar</button>
    </form>
    '''

# Login
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        s = request.form['senha']
        cursor.execute("SELECT * FROM usuarios WHERE username=? AND senha=?", (u,s))
        if cursor.fetchone():
            session['user']=u
            return redirect('/home')

    return '''<form method="post">Usuário:<input name="username">Senha:<input type="password" name="senha"><button>Entrar</button></form>'''

@app.route('/home')
def home():
    return render_template_string(home_page)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Rodar
if __name__=='__main__':
    app.run(debug=True)
