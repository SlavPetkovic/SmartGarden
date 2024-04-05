# Import Dependencies
from sqlalchemy import create_engine, Column, Integer, Numeric, DateTime
# Updated import statement for declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

# Adjusted to use the new import path for declarative_base
Base = declarative_base()

class Sensors(Base):
    __tablename__ = 'SensorsData'
    id = Column(Integer, primary_key=True, autoincrement=True)
    TimeStamp = Column(DateTime, default=func.now())
    Temperature = Column(Numeric)
    Gas = Column(Numeric)
    Humidity = Column(Numeric)
    Pressure = Column(Numeric)
    Altitude = Column(Numeric)
    Luminosity = Column(Numeric)

# Create engine
engine = create_engine('sqlite:///data/Neutrino.db', echo=True)

# Create all tables in the engine
Base.metadata.create_all(engine)

# Create session
Session = sessionmaker(bind=engine)

# Using context manager to handle session
with Session() as session:
    # Creating dummy data set for test
    test_data = Sensors(
        Temperature=75,
        Gas=100,
        Humidity=50,
        Pressure=1000,
        Altitude=1000,
        Luminosity=1000
    )

    # Add test_data to the session
    session.add(test_data)

    # Commit the record to the database
    session.commit()
