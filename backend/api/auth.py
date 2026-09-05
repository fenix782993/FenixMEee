import hashlib, secrets, re, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.core.db import get_db
from backend.core.security import create_token, hash_password, verify_password
from backend.core.config import settings
from backend.models import User, PhoneVerification, EmailVerification
from backend.schemas.auth import RegisterIn, LoginIn, TokenOut, PhoneRequestIn, PhoneVerifyIn, CompleteProfileIn, EmailRequestIn, EmailVerifyIn, CompleteEmailProfileIn

router = APIRouter(prefix='/auth', tags=['auth'])
PHONE_RE = re.compile(r'^\+[1-9]\d{6,14}$')

def clean_username(value: str) -> str: return value.strip().lower()
def normalize_phone(value: str) -> str:
    value=value.strip().replace(' ','').replace('-','').replace('(','').replace(')','')
    if value.startswith('00'): value='+'+value[2:]
    if not PHONE_RE.fullmatch(value): raise HTTPException(422,'Введите номер в международном формате, например +491701234567')
    return value

def clean_email(value: str) -> str: return value.strip().lower()
def code_hash(code: str) -> str: return hashlib.sha256((settings.otp_pepper+':'+code).encode()).hexdigest()

def configured_email() -> bool:
    return bool(settings.brevo_api_key and settings.mail_from) or bool(settings.smtp_host and settings.smtp_user and settings.smtp_password and settings.mail_from)

async def send_email_code(email: str, code: str) -> None:
    subject='Код подтверждения — Fenix Messenger'
    html=f'''<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto"><h2>Fenix Messenger</h2><p>Ваш код подтверждения:</p><div style="font-size:32px;font-weight:700;letter-spacing:8px">{code}</div><p>Код действует 5 минут.</p><p style="color:#777">Если вы не запрашивали код, просто проигнорируйте это письмо.</p></div>'''
    if settings.brevo_api_key and settings.mail_from:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            r=await client.post('https://api.brevo.com/v3/smtp/email',headers={'api-key':settings.brevo_api_key,'accept':'application/json','content-type':'application/json'},json={'sender':{'email':settings.mail_from,'name':settings.mail_from_name},'to':[{'email':email}], 'subject':subject,'htmlContent':html})
        if r.status_code>=400: raise HTTPException(502,'Не удалось отправить код на email. Проверьте настройки Brevo.')
        return
    if settings.smtp_host and settings.smtp_user and settings.smtp_password and settings.mail_from:
        msg=EmailMessage(); msg['Subject']=subject; msg['From']=settings.mail_from; msg['To']=email; msg.set_content(f'Fenix Messenger\n\nВаш код: {code}\nКод действует 5 минут.')
        msg.add_alternative(html,subtype='html')
        with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=15) as server:
            if settings.smtp_use_tls: server.starttls()
            server.login(settings.smtp_user,settings.smtp_password); server.send_message(msg)
        return
    print(f'[FENIX EMAIL OTP DEV] {email}: {code}',flush=True)

@router.post('/email/request')
async def email_request(data: EmailRequestIn, db: Session=Depends(get_db)):
    email=clean_email(str(data.email)); existing=db.scalar(select(User).where(User.email==email))
    if data.purpose=='register' and existing: raise HTTPException(409,'Этот email уже зарегистрирован. Выберите вход.')
    if data.purpose=='login' and not existing: raise HTTPException(404,'Аккаунт с таким email не найден. Сначала зарегистрируйтесь.')
    now=datetime.now(timezone.utc)
    recent=db.scalar(select(EmailVerification).where(EmailVerification.email==email,EmailVerification.purpose==data.purpose,EmailVerification.used==False,EmailVerification.created_at>now-timedelta(seconds=45)).order_by(EmailVerification.id.desc()))
    if recent: raise HTTPException(429,'Новый код можно запросить через несколько секунд.')
    code=f'{secrets.randbelow(1_000_000):06d}'
    db.add(EmailVerification(email=email,purpose=data.purpose,code_hash=code_hash(code),expires_at=now+timedelta(minutes=5))); db.commit()
    await send_email_code(email,code)
    return {'ok':True,'email':email,'expires_in':300,'delivery':'email' if configured_email() else 'development_log'}

@router.post('/email/verify')
def email_verify(data: EmailVerifyIn, db: Session=Depends(get_db)):
    email=clean_email(str(data.email)); now=datetime.now(timezone.utc)
    record=db.scalar(select(EmailVerification).where(EmailVerification.email==email,EmailVerification.purpose==data.purpose,EmailVerification.used==False).order_by(EmailVerification.id.desc()))
    if not record or record.expires_at.replace(tzinfo=timezone.utc)<now: raise HTTPException(400,'Код истёк. Запросите новый код.')
    if record.attempts>=5: raise HTTPException(429,'Слишком много попыток. Запросите новый код.')
    if not secrets.compare_digest(record.code_hash,code_hash(data.code.strip())):
        record.attempts+=1; db.commit(); raise HTTPException(400,'Неверный код подтверждения.')
    record.used=True; db.commit(); user=db.scalar(select(User).where(User.email==email))
    if data.purpose=='login':
        if not user: raise HTTPException(404,'Аккаунт не найден.')
        user.online=True; db.commit(); return {'status':'authenticated',**TokenOut(access_token=create_token(user.id)).model_dump()}
    from jose import jwt
    payload={'sub':email,'typ':'email_signup','iat':int(now.timestamp()),'exp':int((now+timedelta(minutes=15)).timestamp())}
    return {'status':'verified','signup_token':jwt.encode(payload,settings.jwt_secret,algorithm=settings.jwt_algorithm),'email':email}

@router.post('/email/complete',response_model=TokenOut)
def email_complete(data: CompleteEmailProfileIn, signup_token:str, db:Session=Depends(get_db)):
    from jose import jwt
    try:
        payload=jwt.decode(signup_token,settings.jwt_secret,algorithms=[settings.jwt_algorithm])
        if payload.get('typ')!='email_signup': raise ValueError()
        email=clean_email(str(payload['sub']))
    except Exception: raise HTTPException(401,'Сессия регистрации истекла. Запросите код заново.')
    username=clean_username(data.username)
    if len(username)<5: raise HTTPException(422,'Юзернейм должен содержать минимум 5 символов')
    if db.scalar(select(User).where(User.username==username)): raise HTTPException(409,'Этот юзернейм уже занят')
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,'Этот email уже зарегистрирован')
    is_first=db.scalar(select(func.count(User.id)))==0
    user=User(username=username,display_name=data.display_name.strip(),password_hash=hash_password(secrets.token_urlsafe(32)),email=email,avatar=data.avatar,online=True,role='owner' if is_first else 'user')
    db.add(user); db.commit(); db.refresh(user); return TokenOut(access_token=create_token(user.id))

# Legacy phone/password routes kept for compatibility.
@router.post('/phone/request')
async def phone_request(data: PhoneRequestIn, db: Session=Depends(get_db)):
    phone=normalize_phone(data.phone); existing=db.scalar(select(User).where(User.phone==phone))
    if data.purpose=='register' and existing: raise HTTPException(409,'Этот номер уже зарегистрирован. Выберите вход.')
    if data.purpose=='login' and not existing: raise HTTPException(404,'Аккаунт с таким номером не найден. Сначала зарегистрируйтесь.')
    now=datetime.now(timezone.utc); code=f'{secrets.randbelow(1_000_000):06d}'
    db.add(PhoneVerification(phone=phone,purpose=data.purpose,code_hash=code_hash(code),expires_at=now+timedelta(minutes=5))); db.commit()
    if settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_verify_service_sid:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            r=await client.post(f'https://verify.twilio.com/v2/Services/{settings.twilio_verify_service_sid}/Verifications',data={'To':phone,'Channel':'sms'},auth=(settings.twilio_account_sid,settings.twilio_auth_token))
        if r.status_code>=400: raise HTTPException(502,'Не удалось отправить SMS-код.')
        delivery='sms'
    else: print(f'[FENIX SMS OTP DEV] {phone}: {code}',flush=True); delivery='development_log'
    return {'ok':True,'phone':phone,'expires_in':300,'delivery':delivery}

@router.post('/phone/verify')
def phone_verify(data:PhoneVerifyIn,db:Session=Depends(get_db)):
    phone=normalize_phone(data.phone); now=datetime.now(timezone.utc)
    record=db.scalar(select(PhoneVerification).where(PhoneVerification.phone==phone,PhoneVerification.purpose==data.purpose,PhoneVerification.used==False).order_by(PhoneVerification.id.desc()))
    if not record or record.expires_at.replace(tzinfo=timezone.utc)<now: raise HTTPException(400,'Код истёк. Запросите новый код.')
    if not secrets.compare_digest(record.code_hash,code_hash(data.code.strip())): record.attempts+=1; db.commit(); raise HTTPException(400,'Неверный код подтверждения.')
    record.used=True; db.commit(); user=db.scalar(select(User).where(User.phone==phone))
    if data.purpose=='login':
        if not user: raise HTTPException(404,'Аккаунт не найден.')
        user.online=True; db.commit(); return {'status':'authenticated',**TokenOut(access_token=create_token(user.id)).model_dump()}
    from jose import jwt
    return {'status':'verified','signup_token':jwt.encode({'sub':phone,'typ':'phone_signup','iat':int(now.timestamp()),'exp':int((now+timedelta(minutes=15)).timestamp())},settings.jwt_secret,algorithm=settings.jwt_algorithm),'phone':phone}

@router.post('/phone/complete',response_model=TokenOut)
def phone_complete(data:CompleteProfileIn,signup_token:str,db:Session=Depends(get_db)):
    from jose import jwt
    try:
        payload=jwt.decode(signup_token,settings.jwt_secret,algorithms=[settings.jwt_algorithm]); phone=normalize_phone(str(payload['sub']))
        if payload.get('typ')!='phone_signup': raise ValueError()
    except Exception: raise HTTPException(401,'Сессия регистрации истекла. Запросите SMS-код заново.')
    username=clean_username(data.username)
    if db.scalar(select(User).where(User.username==username)): raise HTTPException(409,'Этот юзернейм уже занят')
    is_first=db.scalar(select(func.count(User.id)))==0
    user=User(username=username,display_name=data.display_name.strip(),password_hash=hash_password(secrets.token_urlsafe(32)),phone=phone,avatar=data.avatar,online=True,role='owner' if is_first else 'user')
    db.add(user); db.commit(); db.refresh(user); return TokenOut(access_token=create_token(user.id))

@router.post('/register',response_model=TokenOut,status_code=201)
def register(data:RegisterIn,db:Session=Depends(get_db)):
    username=clean_username(data.username)
    if db.scalar(select(User).where(User.username==username)): raise HTTPException(409,'Пользователь с таким юзернеймом уже существует')
    is_first=db.scalar(select(func.count(User.id)))==0
    user=User(username=username,display_name=data.display_name.strip(),password_hash=hash_password(data.password),online=True,role='owner' if is_first else 'user'); db.add(user); db.commit(); db.refresh(user); return TokenOut(access_token=create_token(user.id))

@router.post('/login',response_model=TokenOut)
def login(data:LoginIn,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.username==clean_username(data.username)))
    if user is None or not verify_password(data.password,user.password_hash): raise HTTPException(401,'Неверный юзернейм или пароль')
    user.online=True; db.commit(); return TokenOut(access_token=create_token(user.id))

@router.get('/me')
def auth_me(u=Depends(current_user)): return u
@router.post('/logout')
def logout(u=Depends(current_user),db:Session=Depends(get_db)): u.online=False; db.commit(); return {'ok':True}
