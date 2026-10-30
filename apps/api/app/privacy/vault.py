"""Local Secret Vault for PrivacyLens.

Secrets stored here are used strictly for direct local browser DOM injection.
Secret values NEVER enter model context, egress payloads, audit logs, or telemetry.
"""
from typing import Dict, Optional

class SecretVault:
    def __init__(self):
        # alias -> secret value
        self._secrets: Dict[str, str] = {}
        # Pre-seed with synthetic testing credentials for the 5 scenarios
        self._init_defaults()

    def _init_defaults(self):
        """Pre-seeds synthetic credentials (non-real, safe test data)."""
        self._secrets = {
            # Checkout scenario
            "checkout_card": "4532750012345673",
            "checkout_expiry": "12/28",
            "checkout_cvv": "987",
            "checkout_name": "Sagar Sharma",
            "checkout_address": "42 Cyber Security Marg, Bengaluru, Karnataka 560001",
            
            # Auth scenario
            "auth_email": "alice.developer@securecorp.local",
            "auth_password": "SuperSecretTestPassword!2026",
            "auth_otp": "782914",
            
            # Developer settings scenario
            "dev_api_token": "sk-pl-prod-live-982341908234918239081234",
            "dev_server_ip": "10.0.14.88",
        }

    def register_secret(self, alias: str, value: str):
        """Registers or updates a secret under a given alias."""
        self._secrets[alias] = value

    def get_secret(self, alias: str) -> Optional[str]:
        """Resolves secret value for direct DOM typing."""
        return self._secrets.get(alias)

    def has_secret(self, alias: str) -> bool:
        return alias in self._secrets

    def list_aliases(self) -> list[str]:
        """Safe export: lists aliases only, never the secret values."""
        return list(self._secrets.keys())

    def clear(self):
        self._secrets.clear()
        self._init_defaults()

vault = SecretVault()
