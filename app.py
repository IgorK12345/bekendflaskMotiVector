from flask import Flask
from sqlalchemy import text
from database import init_db, db
from models import User

app = Flask(__name__)
init_db(app)

@app.route('/test-db')
def test_db():
    try:
        db.session.execute(text('SELECT 1')).scalar()
        return "✅ БД работает отлично!"
    except Exception as e:
        return f"❌ Ошибка подключения: {str(e)}"

@app.route('/')
def home():
    return "Привет! БД подключена."

if __name__ == '__main__':
    with app.app_context():
        try:
            print("Создаем таблицы...")
            db.create_all()
            print("✅ Таблицы созданы!")
        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
    
    app.run(debug=True)