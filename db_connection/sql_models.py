from sqlalchemy import Integer, Column

from db_connection.db_connector import Base, engine

class Example(Base):
    id: Column = Column(Integer, primary_key=True)

    def my_method(self):
        return true


Base.metadata.create_all(engine)