import re
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import (class_mapper, mapper, relationship, 
                            scoped_session, sessionmaker, configure_mappers)

from magic import one_to_many, many_to_one, many_to_many

DB_URL = "mysql://localhost/payments"


# Create a Base class that all Entity classes will inherit
class Base(object):
    
    @declared_attr
    def __tablename__(cls):
        # convert from CamelCase to words_with_underscores:
        name = cls.__name__
        return (
            name[0].lower() +
            re.sub(r'([A-Z])',
                   lambda m:"_" + m.group(0).lower(), name[1:])
            )

    #provide an 'id' column to all tables:
    id = Column(Integer, primary_key=True)

    @classmethod
    def setup_database(cls, url, create=False, echo=False):
        """'Setup everything' method for the ultra lazy."""

        configure_mappers()
        e = sa.create_engine(url, echo=echo)
        if create:
            cls.metadata.create_all(e)
        cls.session = scoped_session(sessionmaker(e))

Entity = declarative_base(cls=Base)
Entity.setup_database(DB_URL)

class User(Entity):
    username = Column(String(50), nullable=False)
    payment_methods = one_to_many("PaymentMethod", "user_id", reverse="user")
    
class PaymentMethod(Entity):
    credit_card = Column(String(50), nullable=False)
    user = many_to_one("User", "user_id", reverse="payment_methods")
    transactions = one_to_many("PaymentTransaction", "payment_method_id", reverse="payment_method")

class PaymentTransaction(Entity):
    amount = Column(Float(10,2), nullable=False)
    timestamp = Column(sa.DateTime, nullable=False)
    payment_method = many_to_one("PaymentMethod", "payment_method_id", reverse="transactions")

def destroy_database():
    engine = sa.create_engine(DB_URL)
    meta = sa.MetaData(engine)
    meta.reflect()
    meta.drop_all()

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Setup Database')
    parser.add_argument('--create', dest='create', action='store_true',
                        help='Create/Update the schema in the database'
                        ' from the definied Entity classes.')
    parser.add_argument('--destroy', dest='destroy', action='store_true',
                        help='Destroy all the tables in the database')
    args = parser.parse_args()
    if (args.create) :
        if (args.destroy):
            destroy_database()
        Entity.setup_database(DB_URL, create=True)
    elif (args.destroy) :
        destroy_database()
    else :
        parser.print_help()
        sys.exit(1)
