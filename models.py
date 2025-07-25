from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(100), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    public_id = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Invoice {self.branch}-{self.model_name}>'

MODELS = sorted([
    'RS68A820B1/MR', 'RS68A8205/MR', 'RS68A8108I/MR', 'RS68A8100S9/MR',
    'RB34C671E9S/MR', 'RB34C7E2E81/MR', 'RB34C632E9S/MR', 'RB34C6B0E1Z/MR',
    'RB34C6B0E2Z/MR', 'RT40A3010SA/MR', 'WD21B6400KV/AS', 'WD25DB895BZ/AS',
    'WW11BB944GB/AS', 'WW11BB544DA/AS', 'WW90T534DA1AS', 'WW80T534DA1AS',
    'WW90CGC0EDABAS', 'WW90T4040CX1AS', 'WW80T4020CX1AS', 'WW70T4020CX1AS',
    'WA19CG6886BVAS', 'WA19CG6745BVAS', 'RT34CG3000VMR', 'RT33D3000BVMR',
    'RT40D63110QVMR', 'RT40D63110BVMR', 'RT40D63118VMR', 'WA11DG5410DBAS',
    'WA11DG5410BWAS', 'MG40DG5524ATGY', 'MS32DG4504ATGY', 'MG32DG4524AGGY',
    'MS23K3614AW/GY', 'VC20M2510WB/GT', 'VCC4540S36/EGT', 'WA14F5S4UWAUAS'
])
