# SPÉCIFICATION API - SYSTÈME DE GESTION DOCUMENTAIRE DISTRIBUÉ
**Version:** 1.0.0
**Date:** 2026-06-13
**Base URL:** `https://api.example.com/v1`

## 1. AUTHENTIFICATION

### POST /auth/login
**Description:** Authentifie un utilisateur et retourne un token JWT

**Requête:**
```json
{
  "username": "alice",
  "password": "password123"
}