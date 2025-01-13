from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

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
            print(f"Error occurred: {str(e)}")
            return False

    @staticmethod
    def get_all_tokens():
        try:
            with app.app_context():  # Ensure we're in the application context
                # Get all token names from the database
                name_list = [token.token_name for token in TrackingTokenNames.query.all()]
                return name_list
        except Exception as e:
            print(f"Error occurred: {str(e)}")
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
            print(f"Error occurred: {str(e)}")
            return False
        


class MemeCoins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
     
     # Automatically set current timestamp in UTC when the row is inserted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    token_name = db.Column(db.String(120),nullable=False)
    token_ticker = db.Column(db.String(120), nullable=False)
    contract_adddress = db.Column(db.String(120), nullable=False)
    dev_address = db.Column(db.String(120), nullable=False)
    metadata_link = db.Column(db.String(120), nullable=False)
    twitter_link = db.Column(db.String(150), nullable=False)




    def add_meme_coin(token_name, token_ticker, contract_address, dev_address, metadata_link,twitter_link):
        try:
            with app.app_context():
            # Create a new MemeCoinsDetails instance
                new_token = MemeCoins(
                    token_name=token_name,
                    token_ticker=token_ticker,
                    contract_adddress=contract_address,
                    dev_address=dev_address,
                    metadata_link=metadata_link,
                    twitter_link=twitter_link.lower()
                )

            # Add the new token to the session and commit
            
                db.session.add(new_token)
                db.session.commit()
                return True
        except IntegrityError:
            db.session.rollback()
            print("Error: Integrity constraint violation (e.g., duplicate token name or ticker)!")
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred while adding token to database: {str(e)}")
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
                tokens_list = [{"token_name": token.token_name, 
                                "token_ticker": token.token_ticker,
                                "contract_address": token.contract_adddress,
                            "dev_address": token.dev_address,
                            "metadata_link": token.metadata_link,
                            "twitter_link": token.twitter_link} for token in tokens]
                
                tokens_list.reverse()
                return tokens_list

        except Exception as e:
            return jsonify({"message": f"Error occurred while fetching tokens: {str(e)}"}), 500

    def get_tokens_by_ticker(token_ticker):
        try:
            with app.app_context():
                # Query the database for all tokens with the same token_name
                tokens = MemeCoins.query.filter_by(token_ticker=token_ticker).all()

                # If no tokens are found with that name, return a message
                if not tokens:
                    return[]

                # If tokens are found, return them in a JSON response
                tokens_list = [{"token_name": token.token_name, 
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
                tokens = MemeCoins.query.filter_by(twitter_link=twitter_link).all()

                # If no tokens are found with that name, return a message
                if not tokens:
                    return[]

                # If tokens are found, return them in a JSON response
                tokens_list = [{"token_name": token.token_name, 
                                "token_ticker": token.token_ticker,
                                "contract_address": token.contract_adddress,
                                "dev_address": token.dev_address,
                                "metadata_link": token.metadata_link,
                                "twitter_link": token.twitter_link} for token in tokens]
                
                tokens_list.reverse()
                return tokens_list

        except Exception as e:
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
            print(f"Error occurred while checking token availability: {str(e)}")
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
            print(f"Error occurred while checking token availability: {str(e)}")
            return False



# Ensure tables are created
with app.app_context():
    db.create_all()
    print("Tables created successfully.")
