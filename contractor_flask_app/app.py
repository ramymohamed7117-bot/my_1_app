from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contractor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.relationship('Role')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role and self.role.code == 'admin'


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    projects = db.relationship('Project', backref='client', cascade='all, delete-orphan')
    transactions = db.relationship('FinanceTransaction', backref='client', cascade='all, delete-orphan')


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    expected_end_date = db.Column(db.Date)
    contract_value = db.Column(db.Float, default=0)
    estimated_cost = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default='in_progress')
    progress_percent = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    phases = db.relationship('ProjectPhase', backref='project', cascade='all, delete-orphan')
    progress_logs = db.relationship('ProjectProgressLog', backref='project', cascade='all, delete-orphan')
    transactions = db.relationship('FinanceTransaction', backref='project', cascade='all, delete-orphan')
    inventory_movements = db.relationship('InventoryMovement', backref='project', cascade='all, delete-orphan')

    def recalculate_progress(self):
        if not self.phases:
            self.progress_percent = 0
            return 0
        total = 0
        for phase in self.phases:
            total += (phase.weight_percent or 0) * (phase.progress_percent or 0) / 100
        self.progress_percent = round(total, 2)
        return self.progress_percent


class ProjectPhase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    phase_name = db.Column(db.String(150), nullable=False)
    weight_percent = db.Column(db.Float, default=0)
    progress_percent = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default='not_started')
    notes = db.Column(db.Text)


class ProjectProgressLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    log_date = db.Column(db.Date, default=date.today)
    planned_percent = db.Column(db.Float, default=0)
    actual_percent = db.Column(db.Float, default=0)
    completed_work_desc = db.Column(db.Text)
    remaining_work_desc = db.Column(db.Text)
    delay_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FinanceTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.Date, default=date.today)
    transaction_type = db.Column(db.String(20), nullable=False)  # income / expense
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_code = db.Column(db.String(50), unique=True, nullable=False)
    material_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100))
    unit = db.Column(db.String(50), default='وحدة')
    minimum_stock = db.Column(db.Float, default=0)
    current_stock = db.Column(db.Float, default=0)
    average_cost = db.Column(db.Float, default=0)

    movements = db.relationship('InventoryMovement', backref='material', cascade='all, delete-orphan')


class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(200))
    notes = db.Column(db.Text)

    movements = db.relationship('InventoryMovement', backref='warehouse', cascade='all, delete-orphan')


class InventoryMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    movement_type = db.Column(db.String(20), nullable=False)  # in / out / adjustment
    quantity = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, default=0)
    total_cost = db.Column(db.Float, default=0)
    movement_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('غير مسموح لك بهذه العملية', 'danger')
            return redirect(url_for('dashboard'))
        return func(*args, **kwargs)
    return wrapper


def init_db():
    db.create_all()

    admin_role = Role.query.filter_by(code='admin').first()
    user_role = Role.query.filter_by(code='user').first()
    if not admin_role:
        admin_role = Role(name='مدير', code='admin')
        db.session.add(admin_role)
    if not user_role:
        user_role = Role(name='مستخدم', code='user')
        db.session.add(user_role)
    db.session.commit()

    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(full_name='مدير النظام', username='admin', role_id=admin_role.id)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    if Client.query.count() == 0:
        client1 = Client(client_code='CL-001', name='شركة النور للمقاولات', phone='01000000001', address='القاهرة')
        client2 = Client(client_code='CL-002', name='مؤسسة الهدى', phone='01000000002', address='الجيزة')
        db.session.add_all([client1, client2])
        db.session.commit()

        project1 = Project(project_code='PR-001', name='برج إداري', client_id=client1.id, location='التجمع', contract_value=2500000, estimated_cost=1800000, status='in_progress', start_date=date(2026, 1, 1), expected_end_date=date(2026, 12, 31))
        project2 = Project(project_code='PR-002', name='مجمع سكني', client_id=client2.id, location='6 أكتوبر', contract_value=4000000, estimated_cost=3200000, status='planned', start_date=date(2026, 2, 1), expected_end_date=date(2026, 11, 30))
        db.session.add_all([project1, project2])
        db.session.commit()

        phases = [
            ProjectPhase(project_id=project1.id, phase_name='الحفر', weight_percent=10, progress_percent=100, status='completed'),
            ProjectPhase(project_id=project1.id, phase_name='القواعد', weight_percent=20, progress_percent=80, status='in_progress'),
            ProjectPhase(project_id=project1.id, phase_name='الهيكل', weight_percent=30, progress_percent=40, status='in_progress'),
            ProjectPhase(project_id=project1.id, phase_name='التشطيبات', weight_percent=40, progress_percent=0, status='not_started'),
        ]
        db.session.add_all(phases)
        db.session.commit()
        project1.recalculate_progress()

        logs = [
            ProjectProgressLog(project_id=project1.id, log_date=date(2026, 1, 10), planned_percent=15, actual_percent=10, completed_work_desc='الانتهاء من أعمال الحفر', remaining_work_desc='بدء القواعد'),
            ProjectProgressLog(project_id=project1.id, log_date=date(2026, 2, 10), planned_percent=30, actual_percent=26, completed_work_desc='صب جزء كبير من القواعد', remaining_work_desc='استكمال القواعد والبدء في الأعمدة'),
            ProjectProgressLog(project_id=project1.id, log_date=date(2026, 3, 10), planned_percent=40, actual_percent=38, completed_work_desc='بدء الهيكل الخرساني', remaining_work_desc='استكمال الهيكل'),
        ]
        db.session.add_all(logs)

        transactions = [
            FinanceTransaction(transaction_type='income', client_id=client1.id, project_id=project1.id, amount=800000, payment_method='تحويل بنكي', description='دفعة مقدمة', transaction_date=date(2026, 1, 5)),
            FinanceTransaction(transaction_type='expense', project_id=project1.id, amount=250000, payment_method='نقدي', description='مواد خرسانية', transaction_date=date(2026, 1, 15)),
            FinanceTransaction(transaction_type='expense', project_id=project1.id, amount=120000, payment_method='تحويل بنكي', description='أجور عمالة', transaction_date=date(2026, 2, 1)),
        ]
        db.session.add_all(transactions)

        warehouse = Warehouse(name='المخزن الرئيسي', location='القاهرة')
        db.session.add(warehouse)
        db.session.commit()

        cement = Material(material_code='MT-001', material_name='أسمنت', category='خرسانة', unit='طن', minimum_stock=20, current_stock=100, average_cost=3200)
        steel = Material(material_code='MT-002', material_name='حديد تسليح', category='حديد', unit='طن', minimum_stock=10, current_stock=40, average_cost=35000)
        db.session.add_all([cement, steel])
        db.session.commit()

        moves = [
            InventoryMovement(warehouse_id=warehouse.id, material_id=cement.id, project_id=project1.id, movement_type='out', quantity=15, unit_cost=3200, total_cost=48000, movement_date=date(2026, 1, 18), notes='صرف للمشروع PR-001'),
            InventoryMovement(warehouse_id=warehouse.id, material_id=steel.id, project_id=project1.id, movement_type='out', quantity=5, unit_cost=35000, total_cost=175000, movement_date=date(2026, 2, 5), notes='حديد تسليح للمشروع PR-001'),
        ]
        db.session.add_all(moves)
        cement.current_stock -= 15
        steel.current_stock -= 5
        db.session.commit()

    for project in Project.query.all():
        project.recalculate_progress()
    db.session.commit()


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active_user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('بيانات الدخول غير صحيحة', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.all()
    clients_count = Client.query.count()
    projects_count = len(projects)
    in_progress_count = Project.query.filter_by(status='in_progress').count()
    completed_count = Project.query.filter_by(status='completed').count()
    total_income = db.session.query(db.func.coalesce(db.func.sum(FinanceTransaction.amount), 0)).filter_by(transaction_type='income').scalar()
    total_expense = db.session.query(db.func.coalesce(db.func.sum(FinanceTransaction.amount), 0)).filter_by(transaction_type='expense').scalar()

    project_labels = [p.name for p in projects]
    project_progress = [p.progress_percent for p in projects]

    monthly_data = {}
    for item in ProjectProgressLog.query.order_by(ProjectProgressLog.log_date).all():
        key = item.log_date.strftime('%Y-%m')
        monthly_data.setdefault(key, []).append(item.actual_percent)
    monthly_labels = list(monthly_data.keys())
    monthly_progress = [round(sum(vals) / len(vals), 2) for vals in monthly_data.values()]

    return render_template(
        'dashboard.html',
        clients_count=clients_count,
        projects_count=projects_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        total_income=total_income,
        total_expense=total_expense,
        net_profit=total_income - total_expense,
        project_labels=project_labels,
        project_progress=project_progress,
        monthly_labels=monthly_labels,
        monthly_progress=monthly_progress,
        low_stock=Material.query.filter(Material.current_stock <= Material.minimum_stock).all(),
    )


@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients():
    if request.method == 'POST':
        client = Client(
            client_code=request.form['client_code'],
            name=request.form['name'],
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            notes=request.form.get('notes'),
        )
        db.session.add(client)
        db.session.commit()
        flash('تم إضافة العميل بنجاح', 'success')
        return redirect(url_for('clients'))
    all_clients = Client.query.order_by(Client.id.desc()).all()
    return render_template('clients.html', clients=all_clients)


@app.route('/clients/<int:client_id>')
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    total_project_value = sum(p.contract_value or 0 for p in client.projects)
    total_income = sum(t.amount for t in client.transactions if t.transaction_type == 'income')
    total_expense = sum(t.amount for t in client.transactions if t.transaction_type == 'expense')
    return render_template('client_detail.html', client=client, total_project_value=total_project_value, total_income=total_income, total_expense=total_expense)


@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if request.method == 'POST':
        project = Project(
            project_code=request.form['project_code'],
            name=request.form['name'],
            client_id=int(request.form['client_id']),
            location=request.form.get('location'),
            description=request.form.get('description'),
            contract_value=float(request.form.get('contract_value') or 0),
            estimated_cost=float(request.form.get('estimated_cost') or 0),
            status=request.form.get('status') or 'planned',
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None,
            expected_end_date=datetime.strptime(request.form['expected_end_date'], '%Y-%m-%d').date() if request.form.get('expected_end_date') else None,
        )
        db.session.add(project)
        db.session.commit()
        flash('تم إضافة المشروع بنجاح', 'success')
        return redirect(url_for('projects'))

    all_projects = Project.query.order_by(Project.id.desc()).all()
    all_clients = Client.query.order_by(Client.name).all()
    return render_template('projects.html', projects=all_projects, clients=all_clients)


@app.route('/projects/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'phase':
            phase = ProjectPhase(
                project_id=project.id,
                phase_name=request.form['phase_name'],
                weight_percent=float(request.form.get('weight_percent') or 0),
                progress_percent=float(request.form.get('progress_percent') or 0),
                status=request.form.get('status') or 'not_started',
                notes=request.form.get('notes'),
            )
            db.session.add(phase)
            db.session.commit()
            project.recalculate_progress()
            db.session.commit()
            flash('تمت إضافة المرحلة', 'success')
        elif form_type == 'progress_log':
            log = ProjectProgressLog(
                project_id=project.id,
                log_date=datetime.strptime(request.form['log_date'], '%Y-%m-%d').date() if request.form.get('log_date') else date.today(),
                planned_percent=float(request.form.get('planned_percent') or 0),
                actual_percent=float(request.form.get('actual_percent') or 0),
                completed_work_desc=request.form.get('completed_work_desc'),
                remaining_work_desc=request.form.get('remaining_work_desc'),
                delay_reason=request.form.get('delay_reason'),
            )
            db.session.add(log)
            db.session.commit()
            flash('تم تسجيل متابعة المشروع', 'success')
        return redirect(url_for('project_detail', project_id=project.id))

    project.recalculate_progress()
    db.session.commit()
    total_expenses = sum(t.amount for t in project.transactions if t.transaction_type == 'expense')
    total_income = sum(t.amount for t in project.transactions if t.transaction_type == 'income')
    phase_labels = [phase.phase_name for phase in project.phases]
    phase_progress = [phase.progress_percent for phase in project.phases]
    return render_template('project_detail.html', project=project, total_expenses=total_expenses, total_income=total_income, phase_labels=phase_labels, phase_progress=phase_progress)


@app.route('/finance', methods=['GET', 'POST'])
@login_required
def finance():
    if request.method == 'POST':
        transaction = FinanceTransaction(
            transaction_date=datetime.strptime(request.form['transaction_date'], '%Y-%m-%d').date() if request.form.get('transaction_date') else date.today(),
            transaction_type=request.form['transaction_type'],
            client_id=int(request.form['client_id']) if request.form.get('client_id') else None,
            project_id=int(request.form['project_id']) if request.form.get('project_id') else None,
            amount=float(request.form['amount']),
            payment_method=request.form.get('payment_method'),
            description=request.form.get('description'),
        )
        db.session.add(transaction)
        db.session.commit()
        flash('تم تسجيل المعاملة المالية', 'success')
        return redirect(url_for('finance'))

    transactions = FinanceTransaction.query.order_by(FinanceTransaction.transaction_date.desc()).all()
    clients = Client.query.order_by(Client.name).all()
    projects = Project.query.order_by(Project.name).all()
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expense = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    return render_template('finance.html', transactions=transactions, clients=clients, projects=projects, total_income=total_income, total_expense=total_expense, net_profit=total_income - total_expense)


@app.route('/materials', methods=['GET', 'POST'])
@login_required
def materials():
    if request.method == 'POST':
        material = Material(
            material_code=request.form['material_code'],
            material_name=request.form['material_name'],
            category=request.form.get('category'),
            unit=request.form.get('unit') or 'وحدة',
            minimum_stock=float(request.form.get('minimum_stock') or 0),
            current_stock=float(request.form.get('current_stock') or 0),
            average_cost=float(request.form.get('average_cost') or 0),
        )
        db.session.add(material)
        db.session.commit()
        flash('تم إضافة الخامة', 'success')
        return redirect(url_for('materials'))

    all_materials = Material.query.order_by(Material.id.desc()).all()
    return render_template('materials.html', materials=all_materials)


@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        material = Material.query.get(int(request.form['material_id']))
        quantity = float(request.form['quantity'])
        unit_cost = float(request.form.get('unit_cost') or 0)
        movement_type = request.form['movement_type']

        movement = InventoryMovement(
            warehouse_id=int(request.form['warehouse_id']),
            material_id=material.id,
            project_id=int(request.form['project_id']) if request.form.get('project_id') else None,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost,
            movement_date=datetime.strptime(request.form['movement_date'], '%Y-%m-%d').date() if request.form.get('movement_date') else date.today(),
            notes=request.form.get('notes'),
        )
        if movement_type == 'in':
            material.current_stock += quantity
        elif movement_type == 'out':
            material.current_stock -= quantity
        else:
            material.current_stock = quantity
        db.session.add(movement)
        db.session.commit()
        flash('تم تسجيل حركة المخزن', 'success')
        return redirect(url_for('inventory'))

    movements = InventoryMovement.query.order_by(InventoryMovement.movement_date.desc()).all()
    materials = Material.query.order_by(Material.material_name).all()
    warehouses = Warehouse.query.order_by(Warehouse.name).all()
    projects = Project.query.order_by(Project.name).all()
    return render_template('inventory.html', movements=movements, materials=materials, warehouses=warehouses, projects=projects)


@app.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    if request.method == 'POST':
        user = User(
            full_name=request.form['full_name'],
            username=request.form['username'],
            role_id=int(request.form['role_id'])
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('تم إضافة المستخدم', 'success')
        return redirect(url_for('users'))

    all_users = User.query.order_by(User.id.desc()).all()
    roles = Role.query.order_by(Role.name).all()
    return render_template('users.html', users=all_users, roles=roles)


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
