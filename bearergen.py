import jwt
import datetime

# Secret key for encoding and decoding JWTs
SECRET_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MTczMTQyMTc2NywiaWF0IjoxNzMxNDE4MTY3LCJzY29wZSI6InJlYWQ6bWVzc2FnZXMgd3JpdGU6bWVzc2FnZXMifQ.-G-21a6tBgvSm2hC4ug-HRbxuRdoiUBdtdD-Y8qRZbo'

def generate_bearer_token(user_id, expiration_minutes=60):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes),
        'iat': datetime.datetime.utcnow(),
        'scope': 'read:messages write:messages'
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

if __name__ == "__main__":
    user_id = 123  # Example user ID
    token = generate_bearer_token(user_id)
    print(f'Bearer Token: {token}')
