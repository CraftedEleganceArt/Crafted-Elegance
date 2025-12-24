import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# १. सुरक्षिततेसाठी Secret Key
app.secret_key = 'crafted_elegance_secret_123'

# २. डेटाबेस सेटअप
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ३. डेटाबेस मॉडेलमध्ये 'category' कॉलम जोडला आहे
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="General") # नवीन कॉलम
    details = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=False)

# ४. डेटाबेस तयार करणे
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def home():
    cat = request.args.get('cat') # कॅटेगरी फिल्टर मिळवा
    search_query = request.args.get('search') # सर्च फिल्टर मिळवा
    
    if search_query:
        # जर कोणी सर्च केले असेल तर
        all_products = Product.query.filter(Product.name.contains(search_query)).all()
    elif cat:
        # जर कोणी विशिष्ट कॅटेगरी निवडली असेल तर
        all_products = Product.query.filter_by(category=cat).all()
    else:
        # काहीही फिल्टर नसल्यास सर्व उत्पादने दाखवा
        all_products = Product.query.all()
        
    return render_template('index.html', products=all_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin_user = os.environ.get('ADMIN_USER')
        admin_pass = os.environ.get('ADMIN_PASS')
        
        if username == admin_user and password == admin_pass:
            session['logged_in'] = True
            return redirect('/admin')
        else:
            return "चुकीचा युजरनेम किंवा पासवर्ड!"
    return render_template('login.html')

# ५. एडमिन रूट (कॅटेगरीसह अपडेटेड)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect('/login')
        
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category'] # कॅटेगरी फॉर्ममधून मिळवा
        details = request.form['details']
        file = request.files['image_file']
        
        if file:
            filename = file.filename
            file.save(os.path.join('static', filename))
            
            # डेटाबेसमध्ये कॅटेगरीसह माहिती भरा
            new_product = Product(
                name=name, 
                price=price, 
                category=category, # येथे category जोडा
                details=details, 
                image=filename
            )
            db.session.add(new_product)
            db.session.commit()
            
        return redirect('/admin')

    all_products = Product.query.all()
    return render_template('admin.html', products=all_products)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if not session.get('logged_in'):
        return redirect('/login')
    
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']
        product.category = request.form['category'] # कॅटेगरी अपडेट करा
        product.details = request.form['details']
        
        file = request.files['image_file']
        if file:
            filename = file.filename
            file.save(os.path.join('static', filename))
            product.image = filename
            
        db.session.commit()
        return redirect('/admin')
        
    return render_template('edit.html', product=product)

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('logged_in'):
        return redirect('/login')
    
    product_to_delete = Product.query.get_or_404(id)
    db.session.delete(product_to_delete)
    db.session.commit()
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    # हे बदलल्यामुळे सर्व्हरला योग्य पोर्ट मिळेल
    app.run(host='0.0.0.0', port=5000)