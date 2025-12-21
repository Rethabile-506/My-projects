# importing database connection function to talk to our database
from database import get_db_connection
# importing password hashing tools to keep passwords secure
from werkzeug.security import generate_password_hash, check_password_hash

# user model class that represents a person who uses our platform
class User:
    # setting up a new user object with all their basic info
    def __init__(self, user_id=None, fullname=None, username=None, email=None, 
                 password_hash=None, role='customer'):
        # unique id number for this user in database
        self.user_id = user_id
        # person's real full name
        self.fullname = fullname
        # username they choose to login with
        self.username = username
        # their email address for contact
        self.email = email
        # encrypted password for security
        self.password_hash = password_hash
        # what type of user they are (customer, admin, etc)
        self.role = role

    # finding a user by looking up their unique id number
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        # connecting to database to search for user
        conn = get_db_connection()
        cursor = conn.cursor()
        # asking database to find user with this specific id
        cursor.execute("SELECT * FROM Users WHERE UserId = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        # if we found someone, return their info as a dictionary
        if row:
            return {
                'UserId': row.UserId,
                'FullName': row.FullName,
                'Username': row.Username,
                'Email': row.Email,
                'Role': row.Role
            }
        # if no user found, return nothing
        return None

    # searching for a user by their chosen username
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        # connecting to database to look up user
        conn = get_db_connection()
        cursor = conn.cursor()
        # searching for someone with this exact username
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        # if found, return all their details including password hash
        if row:
            return {
                'UserId': row.UserId,
                'FullName': row.FullName,
                'Username': row.Username,
                'Email': row.Email,
                'PasswordHash': row.PasswordHash,
                'Role': row.Role
            }
        # return nothing if username doesn't exist
        return None

    # checking if username and password combination is correct for login
    @staticmethod
    def authenticate(username, password):
        """Authenticate user"""
        # first find the user by their username
        user = User.get_by_username(username)
        # if user exists and password matches the stored hash, login successful
        if user and check_password_hash(user['PasswordHash'], password):
            return user
        # if username doesn't exist or password wrong, deny access
        return None

    # saving this user's information to the database
    def save(self):
        """Save user to database"""
        # connecting to database to store user info
        conn = get_db_connection()
        cursor = conn.cursor()
        # if user already has an id, we update their existing record
        if self.user_id:
            # updating existing user's information
            cursor.execute("""
                UPDATE Users 
                SET FullName=?, Username=?, Email=?, Role=?
                WHERE UserId=?
            """, (self.fullname, self.username, self.email, self.role, self.user_id))
        else:
            # creating a brand new user record in database
            cursor.execute("""
                INSERT INTO Users (FullName, Username, Email, PasswordHash, Role)
                VALUES (?, ?, ?, ?, ?)
            """, (self.fullname, self.username, self.email, self.password_hash, self.role))
        # making sure changes are permanently saved
        conn.commit()
        conn.close()

    # getting a list of all users in the system
    @staticmethod
    def get_all():
        """Get all users"""
        # connecting to database to fetch everyone
        conn = get_db_connection()
        cursor = conn.cursor()
        # asking database for all user records
        cursor.execute("SELECT * FROM Users")
        users = []
        # going through each person found and adding them to our list
        for row in cursor.fetchall():
            users.append({
                'UserId': row.UserId,
                'FullName': row.FullName,
                'Username': row.Username,
                'Email': row.Email,
                'Role': row.Role
            })
        conn.close()
        # returning the complete list of all users
        return users