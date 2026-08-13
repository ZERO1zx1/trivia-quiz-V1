"""Small, timeout-safe Supabase Auth, Storage, and Realtime adapter.

The publishable key is used for user-scoped operations. The secret key is
used only for narrowly scoped server administration and is never returned to
templates or browser code.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode

import requests
from flask import current_app
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SupabaseError(RuntimeError):
    """A safe external-service error that contains no credentials."""


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict[str, Any]


class SupabaseService:
    def __init__(self) -> None:
        self.url = current_app.config['SUPABASE_URL'].rstrip('/')
        self.publishable_key = current_app.config['SUPABASE_PUBLISHABLE_KEY']
        self.secret_key = current_app.config['SUPABASE_SECRET_KEY']
        self.timeout = current_app.config['SUPABASE_HTTP_TIMEOUT']
        retry = Retry(
            total=3,
            connect=3,
            read=2,
            backoff_factor=0.25,
            status_forcelist=(429, 502, 503, 504),
            allowed_methods=frozenset({'GET', 'PUT', 'DELETE'}),
            respect_retry_after_header=True,
        )
        self.http = requests.Session()
        self.http.mount('https://', HTTPAdapter(max_retries=retry))

    @staticmethod
    def enabled() -> bool:
        return bool(current_app.config.get('SUPABASE_AUTH_ENABLED'))

    def _headers(self, *, token: str | None = None,
                 admin: bool = False) -> dict[str, str]:
        key = self.secret_key if admin else self.publishable_key
        if not key:
            raise SupabaseError('Supabase is not configured')
        return {
            'apikey': key,
            'Authorization': f'Bearer {token or key}',
            'Content-Type': 'application/json',
        }

    def _request(self, method: str, path: str, *, token: str | None = None,
                 admin: bool = False, expected: tuple[int, ...] = (200,),
                 **kwargs: Any) -> dict[str, Any]:
        try:
            response = self.http.request(
                method, f'{self.url}{path}',
                headers=self._headers(token=token, admin=admin),
                timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise SupabaseError('Authentication service is unavailable') from exc
        if response.status_code not in expected:
            try:
                payload = response.json()
                message = payload.get('msg') or payload.get('message') \
                    or payload.get('error_description')
            except ValueError:
                message = None
            current_app.logger.warning(
                'Supabase request failed: %s %s status=%s',
                method, path.split('?')[0], response.status_code)
            raise SupabaseError(message or 'Supabase request failed')
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise SupabaseError('Supabase returned an invalid response') from exc

    @staticmethod
    def _tokens(payload: dict[str, Any]) -> AuthTokens:
        session = payload.get('session') or payload
        user = payload.get('user') or session.get('user') or {}
        try:
            return AuthTokens(
                access_token=session['access_token'],
                refresh_token=session['refresh_token'],
                expires_in=int(session.get('expires_in', 3600)),
                user=user,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SupabaseError('Authentication did not return a session') from exc

    def sign_up(self, email: str, password: str,
                metadata: dict[str, Any]) -> dict[str, Any]:
        return self._request('POST', '/auth/v1/signup', expected=(200, 201),
                             json={'email': email, 'password': password,
                                   'data': metadata})

    def sign_in(self, email: str, password: str) -> AuthTokens:
        payload = self._request(
            'POST', '/auth/v1/token?grant_type=password',
            json={'email': email, 'password': password})
        return self._tokens(payload)

    def create_legacy_user(self, email: str, password: str,
                           metadata: dict[str, Any],
                           email_confirm: bool) -> dict[str, Any]:
        return self._request(
            'POST', '/auth/v1/admin/users', admin=True, expected=(200, 201),
            json={'email': email, 'password': password,
                  'email_confirm': email_confirm,
                  'user_metadata': metadata})

    def delete_user(self, auth_user_id: str) -> None:
        self._request('DELETE', f'/auth/v1/admin/users/{auth_user_id}',
                      admin=True, expected=(200, 204))

    def refresh(self, refresh_token: str) -> AuthTokens:
        payload = self._request(
            'POST', '/auth/v1/token?grant_type=refresh_token',
            json={'refresh_token': refresh_token})
        return self._tokens(payload)

    @staticmethod
    def _pkce() -> tuple[str, str]:
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode('ascii')).digest()
        ).rstrip(b'=').decode('ascii')
        return verifier, challenge

    def recover(self, email: str, redirect_to: str) -> str:
        verifier, challenge = self._pkce()
        self._request('POST', '/auth/v1/recover', expected=(200,),
                      json={'email': email, 'redirect_to': redirect_to,
                            'code_challenge': challenge,
                            'code_challenge_method': 's256'})
        return verifier

    def update_password(self, access_token: str, password: str) -> None:
        self._request('PUT', '/auth/v1/user', token=access_token,
                      json={'password': password})

    def begin_oauth(self, provider: str, redirect_to: str) -> tuple[str, str]:
        verifier, challenge = self._pkce()
        query = urlencode({
            'provider': provider,
            'redirect_to': redirect_to,
            'code_challenge': challenge,
            'code_challenge_method': 's256',
        })
        return f'{self.url}/auth/v1/authorize?{query}', verifier

    def exchange_oauth_code(self, code: str, verifier: str) -> AuthTokens:
        payload = self._request(
            'POST', '/auth/v1/token?grant_type=pkce',
            json={'auth_code': code, 'code_verifier': verifier})
        return self._tokens(payload)

    def enroll_totp(self, access_token: str,
                    friendly_name: str) -> dict[str, Any]:
        return self._request(
            'POST', '/auth/v1/factors', token=access_token,
            expected=(200, 201),
            json={'factor_type': 'totp', 'friendly_name': friendly_name,
                  'issuer': 'TriviaVerse'})

    def challenge_totp(self, access_token: str,
                       factor_id: str) -> str:
        payload = self._request(
            'POST', f'/auth/v1/factors/{factor_id}/challenge',
            token=access_token, expected=(200, 201), json={})
        challenge_id = payload.get('id')
        if not challenge_id:
            raise SupabaseError('MFA challenge could not be created')
        return challenge_id

    def verify_totp(self, access_token: str, factor_id: str,
                    challenge_id: str, code: str) -> AuthTokens:
        payload = self._request(
            'POST', f'/auth/v1/factors/{factor_id}/verify',
            token=access_token,
            json={'challenge_id': challenge_id, 'code': code})
        return self._tokens(payload)

    def unenroll_factor(self, access_token: str, factor_id: str) -> None:
        self._request('DELETE', f'/auth/v1/factors/{factor_id}',
                      token=access_token, expected=(200, 204))

    def upload_image(self, bucket: str, object_path: str, data: bytes,
                     content_type: str, access_token: str) -> str:
        path = '/storage/v1/object/' + quote(bucket, safe='') + '/' + quote(
            object_path, safe='/')
        headers = self._headers(token=access_token)
        headers['Content-Type'] = content_type
        headers['x-upsert'] = 'false'
        try:
            response = self.http.post(
                f'{self.url}{path}', headers=headers, data=data,
                timeout=self.timeout)
        except requests.RequestException as exc:
            raise SupabaseError('Storage service is unavailable') from exc
        if response.status_code not in (200, 201):
            raise SupabaseError('Image upload failed')
        return (f'{self.url}/storage/v1/object/public/'
                f'{quote(bucket, safe="")}/{quote(object_path, safe="/")}')

    def broadcast(self, topic: str, event: str, payload: dict[str, Any],
                  *, private: bool = True) -> None:
        path = (f'/realtime/v1/api/broadcast/{quote(topic, safe="")}'
                f'/events/{quote(event, safe="")}')
        if private:
            path += '?private=true'
        self._request('POST', path, admin=True, expected=(200, 202),
                      json=payload)
