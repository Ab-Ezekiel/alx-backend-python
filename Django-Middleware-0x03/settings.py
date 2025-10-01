from messaging_app.settings import *  # noqa: F401,F403

MIDDLEWARE += [
    'chats.middleware.RolepermissionMiddleware',
    'chats.middleware.OffensiveLanguageMiddleware', 
    'chats.middleware.RequestLoggingMiddleware',
    'chats.middleware.RestrictAccessByTimeMiddleware',
]
