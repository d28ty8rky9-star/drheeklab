"""Passwords are never saved in plaintext or audit records."""
import hashlib
import hmac
import secrets
import time

ITERATIONS = 600_000

class Auth:
    def __init__(self, storage):
        self.storage = storage
        self.failures = 0
        self.blocked_until = 0.0

    @property
    def configured(self):
        return self.storage.db.execute("SELECT 1 FROM users WHERE id=1").fetchone() is not None

    @staticmethod
    def validate(password):
        if len(password) < 8:
            raise ValueError("Use uma senha com pelo menos oito caracteres.")

    def create(self, password):
        if self.configured:
            raise ValueError("A senha já foi cadastrada.")
        self._save(password, "cadastro de senha")

    def verify(self, password):
        if time.monotonic() < self.blocked_until:
            raise ValueError("Muitas tentativas. Aguarde 30 segundos.")
        row = self.storage.db.execute("SELECT * FROM users WHERE id=1").fetchone()
        if not row:
            return False
        computed = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(row["salt"]), row["iterations"]).hex()
        valid = hmac.compare_digest(computed, row["password_hash"])
        if valid:
            self.failures = 0
        else:
            self.failures += 1
            if self.failures >= 5:
                self.blocked_until = time.monotonic() + 30
                self.failures = 0
        return valid

    def change(self, old, new):
        if not self.verify(old):
            raise ValueError("Senha atual incorreta.")
        self._save(new, "alteração de senha")

    def _save(self, password, operation):
        self.validate(password)
        salt = secrets.token_bytes(32)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS).hex()
        with self.storage.db:
            self.storage.db.execute("INSERT INTO users VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET salt=excluded.salt,password_hash=excluded.password_hash,iterations=excluded.iterations",
                                    (salt.hex(), hashed, ITERATIONS))
            self.storage.audit(operation, "usuário principal")
