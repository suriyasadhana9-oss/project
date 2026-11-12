from flask import Flask
from extensions import db, bcrypt, login_manager
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'textile_export_secret_key_12345')
    
    # Database configuration: support PostgreSQL, Vercel Serverless /tmp, or local SQLite
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    elif os.environ.get('VERCEL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/site.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from datetime import datetime
    @app.context_processor
    def inject_now():
        return {'datetime': datetime}

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    from routes import main
    app.register_blueprint(main)
    
    with app.app_context():
        from models import Order, Production, Shipment, Invoice
        db.create_all()
        # Seed default users if none exist (essential for clean Vercel deployments)
        try:
            if not User.query.first():
                admin_pw = bcrypt.generate_password_hash('password123').decode('utf-8')
                admin = User(username='admin', password=admin_pw, role='Admin')
                staff_pw = bcrypt.generate_password_hash('staff123').decode('utf-8')
                staff = User(username='staff', password=staff_pw, role='Staff')
                db.session.add_all([admin, staff])
                db.session.commit()
        except Exception:
            db.session.rollback()
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
