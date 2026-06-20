import io
import json
import pytest
from flask import current_app
from werkzeug.datastructures import FileStorage

from tuned.models.enums import AssetOwnerType, FileExtensionType, GenderEnum
from tuned.models.user import User
from tuned.utils.auth import hash_password
from tuned.utils.dependencies import get_services


def make_dummy_file(filename, content=b"dummy file contents"):
    return FileStorage(
        stream=io.BytesIO(content),
        filename=filename,
        content_type="text/plain"
    )


def test_media_upload_and_permissions(app, db, sample_user, admin_user):
    services = get_services()
    
    # 1. Upload a file
    dummy_file = make_dummy_file("test_document.txt")
    asset_dto = services.media.upload_file(
        file=dummy_file,
        owner_type=AssetOwnerType.USER,
        owner_id=str(sample_user.id),
        is_public=False
    )
    
    assert asset_dto.original_filename == "test_document.txt"
    assert asset_dto.is_public is False
    assert asset_dto.storage_path.startswith("profile_pics/")
    
    # 2. Owner can download
    assert services.media.verify_download_permission(str(asset_dto.id), sample_user) is True
    
    # 3. Non-owner cannot download
    other_user = User(
        username="otheruser",
        email="other@example.com",
        first_name="Other",
        last_name="User",
        gender=GenderEnum.FEMALE,
        email_verified=True
    )
    other_user.password_hash = hash_password("Password123!")
    db.session.add(other_user)
    db.session.commit()
    
    assert services.media.verify_download_permission(str(asset_dto.id), other_user) is False
    
    # 4. Admin can download
    assert services.media.verify_download_permission(str(asset_dto.id), admin_user) is True


def test_media_download_api(client, db, app, sample_user, admin_user):
    # Log in as sample_user
    login_data = {
        'identifier': sample_user.email,
        'password': 'TestPass123!'
    }
    login_resp = client.post('/api/auth/login', json=login_data)
    assert login_resp.status_code == 200
    
    services = get_services()
    
    # Upload restricted file
    dummy_file = make_dummy_file("secret.txt", b"very secret info")
    asset_dto = services.media.upload_file(
        file=dummy_file,
        owner_type=AssetOwnerType.USER,
        owner_id=str(sample_user.id),
        is_public=False
    )
    
    # Download single file
    resp = client.get(f'/api/media/download/{asset_dto.id}')
    assert resp.status_code == 200
    assert resp.headers.get('X-Accel-Redirect') == f"/protected_media/{asset_dto.storage_path}"
    assert "attachment" in resp.headers.get('Content-Disposition')
    
    # Download bulk files
    bulk_data = {
        'asset_ids': [str(asset_dto.id)]
    }
    resp = client.post('/api/media/download/bulk', json=bulk_data)
    assert resp.status_code == 200
    assert resp.headers.get('X-Accel-Redirect').startswith("/protected_media/temp/")
    assert resp.headers.get('Content-Type') == "application/zip"
