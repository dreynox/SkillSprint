from dependency_injector import containers, providers
from database import SessionLocal

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "routes.auth_routes",
            "routes.chatbot_routes",
            "routes.compiler_routes",
            "routes.contest_routes",
            "routes.hackathon_routes",
            "routes.health_routes",
            "routes.message_routes",
            "routes.quiz_routes",
            "routes.user_routes"
        ]
    )
    
    db_session = providers.Resource(get_db_session)
