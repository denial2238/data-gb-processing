from flask import Flask, Blueprint

# Create a blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "Hello, Flask!"

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = '12345678'  # Replace with a secure secret key

    # Register blueprints or routes here
    app.register_blueprint(main)

    return app
