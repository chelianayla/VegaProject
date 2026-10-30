"""Menambahkan viewer ke database secara interaktif."""

from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from backend.vega.db import SessionLocal
from backend.vega.models import User
from backend.vega.schemas import UserCreate
from backend.vega.security import hash_password


def main() -> int:
    print("Tambah viewer baru ke database yang dikonfigurasi dalam .env.")

    username = input("Username baru: ").strip()
    full_name = input("Nama lengkap: ").strip()
    email = input("Email (opsional, Enter untuk kosong): ").strip() or None

    password = getpass(
        "Password (min. 12 karakter, huruf besar/kecil, angka, simbol): "
    )
    confirmation = getpass("Ulangi password: ")

    if password != confirmation:
        print("Password tidak cocok. Tidak ada perubahan.")
        return 1

    try:
        payload = UserCreate(
            username=username,
            full_name=full_name,
            email=email,
            role="VIEWER",
            password=password,
        )
    except ValidationError as exc:
        for error in exc.errors(include_input=False):
            field = ".".join(map(str, error["loc"]))
            print(f"{field}: {error['msg']}")
        return 1

    try:
        with SessionLocal.begin() as session:
            existing = session.scalar(
                select(User.id).where(
                    func.lower(User.username) == payload.username.lower()
                )
            )

            if existing is not None:
                print("Username sudah dipakai. Akun yang ada tidak diubah.")
                return 1

            session.add(
                User(
                    username=payload.username,
                    full_name=payload.full_name,
                    email=payload.email,
                    role="VIEWER",
                    is_active=True,
                    password_hash=hash_password(payload.password),
                )
            )

    except SQLAlchemyError:
        print(
            "Gagal menyimpan viewer. "
            "Periksa koneksi database dan schema proyek."
        )
        return 1

    print(
        f"Viewer {payload.username} berhasil dibuat "
        "dan dapat langsung login."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nDibatalkan. Tidak ada akun baru yang disimpan.")
        raise SystemExit(1)