from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def get_id(self):
        return str(self.id)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(200), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    supervisor = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cloudinary_url = db.Column(db.String(500), nullable=False)
    cloudinary_public_id = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Invoice {self.branch}-{self.model_name}>'

MODELS = sorted([
    'RS68A8820B1/MR', 'RS68A8820S9/MR', 'RS66A8100B1/MR', 'RS66A8100S9/MR',
    'RB34C671ES9/MR', 'RB34C672EB1/MR', 'RB34C632ES9/MR', 'RB34C6B0E12/MR',
    'RB34C6B0E22/MR', 'RT40A3010SA/MR', 'WD21B6400KV/AS', 'WD25DB8995BZAS',
    'WW11B944DGB/AS', 'WW11B534DAB/AS', 'WW90T534DAN1AS', 'WW90CGCOEDABAS',
    'WW90T4040CX1AS', 'WW80T534DAN1AS', 'WW80CGCOEDABAS', 'WW80T4040CX1AS',
    'WW80T4020CX1AS', 'WW70T4020CX1AS', 'WA19CG6886BVAS', 'WA19CG6745BVAS',
    'RT33DG3000QVMR', 'RT33DG3000BVMR', 'RT40DG3110QVMR', 'RT40DG3110BVMR',
    'RT40DG3111QVMR', 'RT40DG3111BVMR', 'MS32DG4504ATGY', 'MG32DG4524AGGY',
    'MS23K3614AW/GY', 'VC20M2510WB/GT', 'VCC4540S36/EGT', 'WA14F5S4UWAUAS',
    'WA11DG5410BDAS','WA11DG5410BWAS'
])
