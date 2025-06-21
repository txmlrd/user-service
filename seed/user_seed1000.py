import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))
from app import create_app, db
from app.models.user import User
from app.extensions import bcrypt
import uuid

app = create_app()

# Data Teachers dengan UUID yang sudah ditentukan
teachers_data = [
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440101',
        'name': 'Ahmad Susanto',
        'email': 'ahmad.susanto@school.edu',
        'password': 'teacher123',
        'phone': '081234567801'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440102',
        'name': 'Siti Nurhaliza',
        'email': 'siti.nurhaliza@school.edu',
        'password': 'teacher123',
        'phone': '081234567802'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440103',
        'name': 'Budi Santoso',
        'email': 'budi.santoso@school.edu',
        'password': 'teacher123',
        'phone': '081234567803'
    }
]

# Data Students dengan UUID yang sudah ditentukan
students_data = [
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440201',
        'name': 'Alice Johnson',
        'email': 'alice.johnson@student.edu',
        'password': 'student123',
        'phone': '081234567901'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440202',
        'name': 'Bob Smith',
        'email': 'bob.smith@student.edu',
        'password': 'student123',
        'phone': '081234567902'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440203',
        'name': 'Charlie Brown',
        'email': 'charlie.brown@student.edu',
        'password': 'student123',
        'phone': '081234567903'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440204',
        'name': 'Diana Prince',
        'email': 'diana.prince@student.edu',
        'password': 'student123',
        'phone': '081234567904'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440205',
        'name': 'Edward Norton',
        'email': 'edward.norton@student.edu',
        'password': 'student123',
        'phone': '081234567905'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440206',
        'name': 'Fiona Green',
        'email': 'fiona.green@student.edu',
        'password': 'student123',
        'phone': '081234567906'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440207',
        'name': 'George Washington',
        'email': 'george.washington@student.edu',
        'password': 'student123',
        'phone': '081234567907'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440208',
        'name': 'Hannah Montana',
        'email': 'hannah.montana@student.edu',
        'password': 'student123',
        'phone': '081234567908'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440209',
        'name': 'Ivan Petrov',
        'email': 'ivan.petrov@student.edu',
        'password': 'student123',
        'phone': '081234567909'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440210',
        'name': 'Julia Roberts',
        'email': 'julia.roberts@student.edu',
        'password': 'student123',
        'phone': '081234567910'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440211',
        'name': 'Kevin Hart',
        'email': 'kevin.hart@student.edu',
        'password': 'student123',
        'phone': '081234567911'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440212',
        'name': 'Linda Hamilton',
        'email': 'linda.hamilton@student.edu',
        'password': 'student123',
        'phone': '081234567912'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440213',
        'name': 'Michael Jordan',
        'email': 'michael.jordan@student.edu',
        'password': 'student123',
        'phone': '081234567913'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440214',
        'name': 'Nancy Drew',
        'email': 'nancy.drew@student.edu',
        'password': 'student123',
        'phone': '081234567914'
    },
    {
        'uuid': '550e8400-e29b-41d4-a716-446655440215',
        'name': 'Oscar Wilde',
        'email': 'oscar.wilde@student.edu',
        'password': 'student123',
        'phone': '081234567915'
    }
]

# Tambahan student (UUID static, total menjadi 1000 student)
for i in range(216, 316):  # dari student216 sampai student1215
    students_data.append({
        'uuid': f'550e8400-e29b-41d4-a716-44665544{str(i).zfill(4)}',
        'name': f'Student{i} Test',
        'email': f'student{i}@student.edu',
        'password': 'student123',
        'phone': f'0812345{str(10000 + i)[-5:]}'
    })



with app.app_context():
    print("🏫 Memulai proses seeding Teachers dan Students...")

    # Seed Teachers
    print("\n👨‍🏫 Seeding Teachers...")
    for teacher_data in teachers_data:
        existing_teacher = User.query.filter_by(email=teacher_data['email']).first()
        if existing_teacher:
            print(f"⚠️ Teacher dengan email '{teacher_data['email']}' sudah ada.")
        else:
            new_teacher = User(
                uuid=teacher_data['uuid'],
                name=teacher_data['name'],
                email=teacher_data['email'],
                password=bcrypt.generate_password_hash(teacher_data['password']).decode('utf-8'),
                role_id=2,  # Assuming role_id 2 is for teachers
                is_verified=True,
                phone=teacher_data['phone']
            )
            db.session.add(new_teacher)
            print(f"✅ Teacher '{teacher_data['name']}' berhasil dibuat.")

    # Seed Students
    print("\n👨‍🎓 Seeding Students...")
    for student_data in students_data:
        existing_student = User.query.filter_by(email=student_data['email']).first()
        if existing_student:
            print(f"⚠️ Student dengan email '{student_data['email']}' sudah ada.")
        else:
            new_student = User(
                uuid=student_data['uuid'],
                name=student_data['name'],
                email=student_data['email'],
                password=bcrypt.generate_password_hash(student_data['password']).decode('utf-8'),
                role_id=3,  # Assuming role_id 3 is for students
                is_verified=True,
                phone=student_data['phone']
            )
            db.session.add(new_student)
            print(f"✅ Student '{student_data['name']}' berhasil dibuat.")

    # Commit semua perubahan
    try:
        db.session.commit()
        print("\n🎉 Semua data Teachers dan Students berhasil disimpan ke database!")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error saat menyimpan data: {e}")

    print("\n📊 Summary:")
    print(f"   Teachers: {len(teachers_data)} records")
    print(f"   Students: {len(students_data)} records")
    print("   Total: {} records".format(len(teachers_data) + len(students_data)))