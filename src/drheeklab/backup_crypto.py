"""Versioned envelope using standard scrypt and authenticated AES-256-GCM.

Passwords and derived keys are never persisted. Authentication completes before
the plaintext ZIP can be parsed. Temporary plaintext requires a protected disk.
"""
from pathlib import Path
import os
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC=b'DHLBENC1'
HEADER_SIZE=len(MAGIC)+16+12
BLOCK=1024*1024

def is_encrypted(path):
    with Path(path).open('rb') as stream:return stream.read(len(MAGIC))==MAGIC

def validate_password(password):
    if not isinstance(password,str) or not 12<=len(password)<=1024:
        raise ValueError('Use uma senha de backup de 12 a 1.024 caracteres. Guarde-a separadamente: não há recuperação sem ela.')

def key(password,salt):
    validate_password(password)
    return Scrypt(salt=salt,length=32,n=2**15,r=8,p=1).derive(password.encode('utf-8'))

def encrypt_file(source,destination,password):
    salt=os.urandom(16);nonce=os.urandom(12);header=MAGIC+salt+nonce
    encryptor=Cipher(algorithms.AES(key(password,salt)),modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(header)
    created=False
    try:
        with Path(source).open('rb') as plain,Path(destination).open('xb') as output:
            created=True
            output.write(header)
            for block in iter(lambda:plain.read(BLOCK),b''):output.write(encryptor.update(block))
            output.write(encryptor.finalize());output.write(encryptor.tag)
            output.flush();os.fsync(output.fileno())
    except Exception:
        if created:Path(destination).unlink(missing_ok=True)
        raise

def decrypt_file(source,destination,password):
    validate_password(password)
    created=False
    try:
        with Path(source).open('rb') as encrypted:
            header=encrypted.read(HEADER_SIZE)
            size=Path(source).stat().st_size
            if len(header)!=HEADER_SIZE or not header.startswith(MAGIC) or size<HEADER_SIZE+16:
                raise ValueError('Backup criptografado incompleto ou formato incompatível.')
            encrypted.seek(-16,os.SEEK_END);tag=encrypted.read(16);encrypted.seek(HEADER_SIZE)
            decryptor=Cipher(algorithms.AES(key(password,header[8:24])),modes.GCM(header[24:],tag)).decryptor()
            decryptor.authenticate_additional_data(header)
            remaining=size-HEADER_SIZE-16
            with Path(destination).open('xb') as output:
                created=True
                while remaining:
                    block=encrypted.read(min(BLOCK,remaining))
                    if not block:raise ValueError('Backup criptografado truncado.')
                    output.write(decryptor.update(block));remaining-=len(block)
                output.write(decryptor.finalize())
    except InvalidTag:
        if created:Path(destination).unlink(missing_ok=True)
        raise ValueError('Senha de backup incorreta ou arquivo alterado; restauração não iniciada.') from None
    except Exception:
        if created:Path(destination).unlink(missing_ok=True)
        raise
