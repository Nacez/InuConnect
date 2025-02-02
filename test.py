from werkzeug.security import generate_password_hash, check_password_hash

strin = "dodonea2112"


password = generate_password_hash(strin, method='pbkdf2:sha256')



print(password)