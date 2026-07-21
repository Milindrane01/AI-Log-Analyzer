"""Pydantic schemas: the API's wire formats (request/response bodies).

Schemas are the public contract; ORM models (models/) are private storage.
They are kept separate so the database can change without breaking clients.
"""
