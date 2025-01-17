from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import logging

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tokens.db'  # replace with your database URI
db = SQLAlchemy(app)

# Define the model
class TrackingTokenNames(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_name = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"<TrackingTokenNames {self.token_name}>"

    @staticmethod
    def add_token(name):
        try:
            with app.app_context():  # Ensure we're in the application context
                # Add a token to the database
                token = TrackingTokenNames(token_name=name)
                db.session.add(token)
                db.session.commit()
                return True
        except Exception as e:
            db.session.rollback()  # Rollback in case of other errors
            logging.exception(f"Error occurred: {str(e)}")
            return False

    @staticmethod
    def get_all_tokens():
        try:
            with app.app_context():  # Ensure we're in the application context
                # Get all token names from the database
                name_list = [token.token_name for token in TrackingTokenNames.query.all()]
                return name_list
        except Exception as e:
            logging.exception(f"Error occurred: {str(e)}")
            return []

    @staticmethod
    def delete_token(name):
        try:
            with app.app_context():  # Ensure we're in the application context
                # Delete a token from the database
                token = TrackingTokenNames.query.filter_by(token_name=name).first()
                if token:
                    db.session.delete(token)
                    db.session.commit()
                    return True
                return False
        except Exception as e:
            db.session.rollback()  # Rollback in case of other errors
            logging.exception(f"Error occurred: {str(e)}")
            return False


##################################################################################

# Define the model
class FakeTwitterAccounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fake_twitter = db.Column(db.String(300), unique=True, nullable=False)

    def __repr__(self):
        return f"<FakeTwitterAccount {self.fake_twitter}>"

    @staticmethod
    def add_account(fake_twitter):
        try:
            with app.app_context():  # Ensure we're in the application context
                # Check if the account already exists
                existing_account = FakeTwitterAccounts.query.filter_by(fake_twitter=fake_twitter).first()
                if existing_account:
                    logging.info(f"Account {fake_twitter} already exists.")
                    return False  # Account already exists

                # Add the new account to the database
                twitter = FakeTwitterAccounts(fake_twitter=fake_twitter)
                db.session.add(twitter)
                db.session.commit()
                return True
        except Exception as e:
            db.session.rollback()  # Rollback in case of other errors
            logging.exception(f"Error occurred: {str(e)}")
            return False

    @staticmethod
    def get_all_accounts():
        try:
            with app.app_context():  # Ensure we're in the application context
                # Get all fake twitter accounts from the database
                twitter_list = [twitter.fake_twitter.split('/')[-1] for twitter in FakeTwitterAccounts.query.all()]
                return twitter_list
        except Exception as e:
            logging.exception(f"Error occurred: {str(e)}")
            return []
        

    @staticmethod
    def is_Fake(twitter_link):
        try:
            with app.app_context():  # Ensure we're in the application context
                existing_account = FakeTwitterAccounts.query.filter_by(fake_twitter=twitter_link.lower()).first()
                if existing_account :
                    return True
                else:
                    return False
        except Exception as e:
            logging.exception(f"Error occurred \"check_Fake()\" in dtabase: {str(e)}")
            return False


    @staticmethod
    def delete_account(twitter_link):
        try:
            with app.app_context():  # Ensure we're in the application context
                # Delete a token from the database
                twitter = FakeTwitterAccounts.query.filter_by(fake_twitter=twitter_link.lower()).first()
                if twitter:
                    db.session.delete(twitter)
                    db.session.commit()
                    return True
                else:
                    logging.info(f"Account {twitter_link} not found.")
                    return False
        except Exception as e:
            db.session.rollback()  # Rollback in case of other errors
            logging.exception(f"Error occurred: {str(e)}")
            return False
        

        
####################################################################################

class MessageIdBasedOnTwitter(db.Model):
    # Primary key is the twitter handle, message_id is unique
    twitter = db.Column(db.String(300), primary_key=True)
    hash_id = db.Column(db.String(300), nullable=False)
    multiple_count = db.Column(db.Integer, nullable=False)  
    message_id = db.Column(db.Integer, nullable=False)  
    empty_msg_id = db.Column(db.Integer, nullable=False)  ## Empty messsage id ""\n⭕\n""
    def __repr__(self):
        return f"<Message {self.twitter} - {self.message_id}>" 

    def add_message_details(twitter,message_id,empty_msg_id, hash_id, multiple_count=0):
        try:
            with app.app_context(): 
                # Check if the message_id already exists for the given twitter handle
                existing_message = MessageIdBasedOnTwitter.query.filter_by(twitter=twitter.lower()).first()
                
                if existing_message:
                    logging.info(f"Message {twitter} already exists")
                    return False
                
                # Create and add new message
                new_message = MessageIdBasedOnTwitter(
                    twitter=twitter.lower(),
                    hash_id=hash_id,
                    message_id=message_id,
                    empty_msg_id=empty_msg_id,
                    multiple_count=multiple_count
                )
                db.session.add(new_message)
                db.session.commit()
                logging.info(f"Message id added for {twitter}.")
                return True
        except Exception as e:
            db.session.rollback()
            logging.exception(f"Error occurred: {str(e)}")
            return False

    def update_message_and_count_and_hasah_id(twitter,new_multiple_count=None, new_message_id=None,new_empty_msg_id=None,new_hash_id =None,):
        try:
            with app.app_context():
                # Find the message to update
                twitter_to_update = MessageIdBasedOnTwitter.query.filter_by(twitter=twitter.lower()).first()
                
                if twitter_to_update:
                    # Update fields only if they are provided
                    if new_multiple_count is not None:
                        twitter_to_update.multiple_count = new_multiple_count
                    if new_message_id:
                        twitter_to_update.message_id = new_message_id
                    if new_hash_id:
                        twitter_to_update.hash_id = new_hash_id
                    if new_empty_msg_id:
                        twitter_to_update.empty_msg_id = new_empty_msg_id


                    db.session.commit()
                    logging.info(f"Message with ID {new_message_id} and {new_hash_id} updated for {twitter}.")
                    return True
                else:
                    logging.info(f" This twitter not found -  {twitter}.")
                    return False
        except Exception as e:
            db.session.rollback()
            logging.exception(f"Error occurred: {str(e)}")
            return False


    def delete_message(twitter):
        try:
            with app.app_context(): 
                # Find the message to delete
                twitter_to_delete = MessageIdBasedOnTwitter.query.filter_by(twitter=twitter.lower()).first()
                
                if twitter_to_delete:
                    db.session.delete(twitter_to_delete)
                    db.session.commit()
                    logging.info(f" Deleted sucessfull - {twitter}")
                    return True
                else:
                    logging.info(f"Not found in database to delete this twitter{twitter}")
                    return False
        except Exception as e:
            db.session.rollback()
            logging.exception(f"Error occurred: {str(e)}")
            return False
        

    def check_twitter_handle_exists_from_twitter_link(twitter_handle):
        try:
            with app.app_context(): 
                # Query to check if the twitter handle exists in the database
                record = MessageIdBasedOnTwitter.query.filter_by(twitter=twitter_handle.lower()).first()
                
                # If record is found, return its data (message_id and multiple_count)
                if record:
                    return {
                        'hash_id': record.hash_id,
                        'message_id': record.message_id,
                        'empty_msg_id': record.empty_msg_id,
                        'multiple_count': record.multiple_count
                    }
                else:
                    # If the twitter handle does not exist, return None or a suitable message
                    return None
            
        except Exception as e:
            # Handle any exceptions (e.g., database errors)
            print(f"An error occurred while querying the database: {e}")
            # Optionally return an error message or None
            return None
        
        

    def check_twitter_handle_exists_from_hashcode(hash_id):
        try:
            with app.app_context(): 
                # Query to check if the twitter handle exists in the database
                record = MessageIdBasedOnTwitter.query.filter_by(hash_id=hash_id).first()
                
                # If record is found, return its data (message_id and multiple_count)
                if record:
                    return {
                        'twitter': record.twitter,
                        'message_id': record.message_id,
                        'empty_msg_id': record.empty_msg_id,
                        'multiple_count': record.multiple_count
                    }
                else:
                    # If the twitter handle does not exist, return None or a suitable message
                    return None
            
        except Exception as e:
            # Handle any exceptions (e.g., database errors)
            print(f"An error occurred while querying the database: {e}")
            # Optionally return an error message or None
            return None

class MemeCoins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    signature = db.Column(db.String(255), nullable=False)
    token_name = db.Column(db.String(120), nullable=False)
    token_ticker = db.Column(db.String(120), nullable=False)
    contract_address = db.Column(db.String(120), nullable=False)
    dev_address = db.Column(db.String(120), nullable=False)
    initial_buy = db.Column(db.Float, nullable=False)
    sol_amount = db.Column(db.Float, nullable=False)
    bonding_curve_key = db.Column(db.String(120), nullable=False)
    v_tokens_in_bonding_curve = db.Column(db.Float, nullable=False)
    v_sol_in_bonding_curve = db.Column(db.Float, nullable=False)
    market_cap_sol = db.Column(db.Float, nullable=False)
    metadata_link = db.Column(db.String(200), nullable=False)
    twitter_link = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"<MemeCoin {self.token_name} ({self.token_ticker})>"

    @staticmethod
    def add_meme_coin(token_name, token_ticker, contract_address, dev_address, metadata_link, twitter_link,
                      initial_buy=0, sol_amount=0.0, bonding_curve_key=None, v_tokens_in_bonding_curve=0,
                      v_sol_in_bonding_curve=0.0, market_cap_sol=0.0, signature=None):
        try:
            with app.app_context():
                # Create a new MemeCoins instance
                new_token = MemeCoins(
                    token_name=token_name,
                    token_ticker=token_ticker,
                    contract_address=contract_address,
                    dev_address=dev_address,
                    metadata_link=metadata_link,
                    twitter_link=twitter_link.lower(),  # Ensure lowercase Twitter link
                    initial_buy=initial_buy,
                    sol_amount=sol_amount,
                    bonding_curve_key=bonding_curve_key,
                    v_tokens_in_bonding_curve=v_tokens_in_bonding_curve,
                    v_sol_in_bonding_curve=v_sol_in_bonding_curve,
                    market_cap_sol=market_cap_sol,
                    signature=signature if signature else None  # Optionally include signature if available
                )

                # Add the new token to the session and commit
                db.session.add(new_token)
                db.session.commit()
                return True
        except IntegrityError:
            db.session.rollback()
            logging.exception("Error: Integrity constraint violation (e.g., duplicate token name or ticker)!")
            return False
        except Exception as e:
            db.session.rollback()
            logging.exception(f"Error occurred while adding token to database: {str(e)}")
            return False

        
    def get_tokens_by_name(token_name):
        try:
            with app.app_context():
            # Query the database for all tokens with the same token_name
                tokens = MemeCoins.query.filter_by(token_name=token_name).all()

                # If no tokens are found with that name, return a message
                if not tokens:
                    return []

                # If tokens are found, return them in a JSON response
                tokens_list = [{"created_at" : token.created_at,
                                "token_name": token.token_name,
                                "token_ticker": token.token_ticker,
                                "contract_address": token.contract_adddress,
                            "dev_address": token.dev_address,
                            "metadata_link": token.metadata_link,
                            "twitter_link": token.twitter_link} for token in tokens]
                
                tokens_list.reverse()
                return tokens_list

        except Exception as e:
            return jsonify({"message": f"Error occurred while fetching tokens: {str(e)}"}), 500



    def get_tokens_by_contract_address(contract_address):
        try:
            with app.app_context():
            # Query the database for all tokens with the same token_name
                meme_coin = MemeCoins.query.filter_by(contract_address=contract_address).first()

                # If no tokens are found with that name, return a message
                if not meme_coin:
                    return []
            
                return meme_coin

        except Exception as e:
            return jsonify({"message": f"Error occurred while fetching tokmeme coin: {str(e)}"}), 500

    def get_tokens_by_ticker(token_ticker):
        try:
            with app.app_context():
                # Query the database for all tokens with the same token_name
                tokens = MemeCoins.query.filter_by(token_ticker=token_ticker).all()

                # If no tokens are found with that name, return a message
                if not tokens:
                    return[]

                # If tokens are found, return them in a JSON response
                tokens_list = [{"created_at" : token.created_at,
                                "token_name": token.token_name, 
                                "token_ticker": token.token_ticker,
                                "contract_address": token.contract_adddress,
                                "dev_address": token.dev_address,
                                "metadata_link": token.metadata_link,
                                "twitter_link": token.twitter_link} for token in tokens]
                
                tokens_list.reverse()
                return tokens_list

        except Exception as e:
            return jsonify({"message": f"Error occurred while fetching tokens: {str(e)}"}), 500

    def get_tokens_have_same_twitter(twitter_link):
        try:
            with app.app_context():

               
                # Query the database for all tokens with the same token_name
                tokens = MemeCoins.query.filter_by(twitter_link=twitter_link.lower()).all()

                print("awa")
                # If no tokens are found with that name, return a message
                if not tokens:
                    return[]

                # If tokens are found, return them in a JSON response
                tokens_list = [{"created_at" : token.created_at,
                                "token_name": token.token_name, 
                                "token_ticker": token.token_ticker,
                                "contract_address": token.contract_adddress,
                                "dev_address": token.dev_address,
                                "metadata_link": token.metadata_link,
                                "twitter_link": token.twitter_link} for token in tokens]
                
                tokens_list.reverse()
                return tokens_list

        except Exception as e:
            print("Error get_tokens_have_same_twitter in database")
            return jsonify({"message": f"Error occurred while fetching tokens: {str(e)}"}), 500


    def get_tokens_have_same_twitter(twitter_link):
        try:
            with app.app_context():

                # Query the database for all tokens with the same twitter_link
                tokens = MemeCoins.query.filter_by(twitter_link=twitter_link.lower()).all()

                # If no tokens are found, return an empty list or a message
                if not tokens:
                    return []

                # If tokens are found, return them in a JSON response
                tokens_list = [
                    {
                        "created_at": token.created_at,
                        "token_name": token.token_name,
                        "token_ticker": token.token_ticker,
                        "contract_address": token.contract_address,  # Fixed typo here
                        "dev_address": token.dev_address,
                        "metadata_link": token.metadata_link,
                        "twitter_link": token.twitter_link
                    }
                    for token in tokens
                ]
                
                # Optionally reverse the order of tokens (based on `created_at` or other criteria)
                tokens_list.reverse()
                
                return tokens_list

        except Exception as e:
            # Log the error and return an informative error response
            print(f"Error occurred while fetching tokens: {str(e)}")
            return jsonify({"message": f"Error occurred while fetching tokens: {str(e)}"}), 500



    def delete_meme_coin(token_name):
        try:
            with app.app_context():
                # Fetch the token by its name
                token_to_delete = MemeCoins.query.filter_by(token_name=token_name).first()

                if not token_to_delete:
                    return jsonify({"message": "Token not found!"}), 404
                
                # Delete the token from the session
                db.session.delete(token_to_delete)
                db.session.commit()
                
                return jsonify({"message": f"Token '{token_name}' deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Error occurred while deleting token: {str(e)}"}), 500
        

    def check_token_availability(token_name, token_ticker, duplicate_count=1):
        try:
            with app.app_context():
                # Check how many tokens have the same token_ticker in the database
                existing_token_ticker_count = MemeCoins.query.filter_by(token_ticker=token_ticker).count()
                if existing_token_ticker_count >= duplicate_count:
                    return True, token_ticker, True  # Duplicate count met for ticker

                # Check how many tokens have the same token_name in the database
                existing_token_name_count = MemeCoins.query.filter_by(token_name=token_name).count()
                if existing_token_name_count >= duplicate_count:
                    return True, token_name, False  # Duplicate count met for name

                # If neither token name nor ticker meets the duplicate count, it's available
                return False, "Not Exist"

        except Exception as e:
            logging.exception(f"Error occurred while checking token availability: {str(e)}")
            return False, "Error - while checking token availability"

    def check_token_availability_from_twitter(twitter, duplicate_count=1):
        try:
            with app.app_context():
                # Check how many tokens have the same token_ticker in the database
                existing_toke_count = MemeCoins.query.filter_by(token_ticker=twitter).count()
                if existing_toke_count >= duplicate_count:
                    return True

                # If neither token name nor ticker meets the duplicate count, it's available
                return False

        except Exception as e:
            logging.exception(f"Error occurred while checking token availability: {str(e)}")
            return False



# Ensure tables are created
with app.app_context():
    db.create_all()
    print("Tables created successfully.")
