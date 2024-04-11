import hashlib

def generate_password_hash(password):
    # Генеруємо сіль
    salt = hashlib.sha256().hexdigest()[:10]
    # Хешуємо пароль разом з сіллю
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    # Повертаємо сіль та хешований пароль, розділені двокрапкою
    return salt + ':' + password_hash

def check_password_hash(saved_password, provided_password):
    # Розділяємо збережений пароль на сіль та хешований пароль
    salt, hashed_password = saved_password.split(':')
    # Перевіряємо, чи хеш від введеного пароля співпадає зі збереженим
    return hashed_password == hashlib.sha256((provided_password + salt).encode()).hexdigest()