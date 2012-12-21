import re
import os.path
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, Numeric
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import (class_mapper, mapper, relationship, 
                            scoped_session, sessionmaker, configure_mappers)
from sqlalchemy.engine.url import URL

from magic import one_to_many, many_to_one, many_to_many

# Setup MySQL database connection reading the username/password from
# your ~/.my.cnf file. You can comment this out and create a simpler
# DB_URL if you're using something other than MySQL, eg:
# postgresql://user:pass@localhost/payments
DB_URL = URL(drivername='mysql', host='localhost', database='payments', 
             query={'read_default_file': 
                    os.path.join(os.path.expanduser('~'), '.my.cnf')})

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

    def __repr__(self):
        """Create a pretty representation of the Entity with column values"""
        vals = {}
        for column in self.__class__.__table__.columns:
            vals[column.name] = getattr(self, column.name)
        return "<{name} {vals}>".format(name=self.__class__.__name__,
                                        vals=vals)

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
    amount = Column(Numeric(19, 2), nullable=False)
    timestamp = Column(sa.DateTime, nullable=False)
    payment_method = many_to_one("PaymentMethod", "payment_method_id", reverse="transactions")
    note = Column(String(50), nullable=True)

def destroy_database():
    "Drop all the database tables"
    engine = sa.create_engine(DB_URL)
    meta = sa.MetaData(engine)
    meta.reflect()
    meta.drop_all()

def create_test_data():
    "Create some test data"
    # Create a user and their payment method:
    mary = User(username="mary")
    cc1 = PaymentMethod(credit_card='123-456-7890', user=mary)
    Entity.session.add(mary)
    Entity.session.add(cc1)
    Entity.session.commit()
    
    # Buy some things:
    purchase1 = PaymentTransaction(
        amount = '78.01',
        payment_method = cc1,
        timestamp = datetime.now(),
        note = 'Groceries')
    Entity.session.add(purchase1)
    purchase2 = PaymentTransaction(
        amount = '108.95',
        payment_method = cc1,
        timestamp = datetime.now(),
        note = 'Electronics')
    Entity.session.add(purchase2)
    Entity.session.commit()

def test_data_report():
    "Query the users and transactions and print them out."
    for user in Entity.session.query(User):
        print("#" * 80)
        print("Transactions for user: {user.username}".format(user=user))
        for payment_method in user.payment_methods:
            for payment in payment_method.transactions:
                print('{payment.note}\t\t{payment.amount}\t\t{payment.timestamp}'.format(payment=payment))
        print("#" * 80)
                

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Setup Database')
    parser.add_argument('--create', dest='create', action='store_true',
                        help='Create/Update the schema in the database'
                        ' from the definied Entity classes.')
    parser.add_argument('--create-test-data', dest='create_test_data', 
                        action='store_true', help='Create some test data')
    parser.add_argument('--report', dest='report', 
                        action='store_true', help='Print test data report')
    parser.add_argument('--destroy', dest='destroy', action='store_true',
                        help='Destroy all the tables in the database')
    args = parser.parse_args()

    if (args.create) :
        if (args.destroy):
            destroy_database()
        Entity.setup_database(DB_URL, create=True)
    elif (args.destroy) :
        destroy_database()
    elif (args.create_test_data):
        create_test_data()
    elif (args.report):
        test_data_report()
    else :
        parser.print_help()
        sys.exit(1)
