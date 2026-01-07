from sqlalchemy import create_engine, text
import os, json
import pandas as pd

user = os.environ.get("DISTR_DB_USER")
password = os.environ.get("DISTR_DB_PASS")
host = os.environ.get("DISTR_DB_HOST")
database = os.environ.get("DISTR_DB_NAME")

db_connection_url = f'postgresql://{user}:{password}@{host}:5432/{database}'

class Database():
    """
    Example: 

    db = Database()
    results = db.query("SELECT * FROM table_name WHERE column_name = %s;", (user_input,))
    """
    def __init__(self):
        self.con = create_engine(db_connection_url)

    def query(self, query_text, params = None):
        """Execute a SQL query and return the results as a DataFrame.

        Args:
            query_text (str): The SQL query to execute.
            params (tuple or dict, optional): Parameters to pass to the query.

        Returns:
            pd.DataFrame: Result of the query.

        Examples:
            db.query("SELECT * FROM table_name")
            db.query("SELECT * FROM table_name WHERE column_name = %s;", (user_input,))
        """
        if params:
            return pd.read_sql(query_text, self.con, params=params)
        else:
            return pd.read_sql(query_text, self.con)

    def has_permissions_to_access_org(self, org_id, user_id):
        """Checks if the user has permission to access the org. Returns the org_id or False."""
        if user_id and org_id:
            results = self.query(
                "SELECT * FROM main_membership WHERE organization_id = %s AND is_org_admin IS TRUE AND member_id = %s;",
                (int(org_id), int(user_id))
            )
            return org_id if len(results) > 0 else False
        return 0  # User is a guest
    
    def get_records(self, org_id):
        """
        Retrieves all turfs assigned to an org

        :param org_id: int
        :return: Dict
        """
        if org_id == 0: # guest mode
            return self.query("SELECT * FROM main_turf WHERE organization_id IS NULL").to_dict(orient='records')

        query = """
        SELECT *
        FROM main_turf
        WHERE organization_id = :org_id;
        """
        return self.query(text(query), params={'org_id': org_id}).to_dict(orient='records')

    def add_record(self, tracts, description, org_id):
        """
        Adds a new record to the database.

        :param tracts: list of tracts
        :param description: dict containing 'name' and 'details'
        :param org_id: int
        :return: the new record as a dictionary
        """
        with self.con.connect() as connection:
            insert_query = """
            INSERT INTO main_turf (tracts, description, organization_id)
            VALUES (:tracts, :description, :org_id)
            RETURNING id;
            """
            result = connection.execute(
                text(insert_query),
                {
                    'tracts': tracts,
                    'description': json.dumps(description),
                    'org_id': org_id or None
                }
            )
            connection.commit()
            new_id = result.fetchone()[0]
            return {"id": new_id, "tracts": tracts, "description": description}

    def edit_record(self, record_id, tracts, description):
        """
        Edits an existing record.

        :param record_id: int representing the ID of the record to edit
        :param tracts: list of new tracts
        :param description: dict containing new 'name' and 'details'
        :return: the updated record or None if not found
        """
        with self.con.connect() as connection:
            update_query = """
            UPDATE main_turf
            SET tracts = :tracts, description = :description
            WHERE id = :record_id
            RETURNING *;
            """
            result = connection.execute(
                text(update_query),
                {
                    'tracts': tracts,
                    'description': json.dumps(description),
                    'record_id': record_id
                }
            )
            connection.commit()
            updated_record = result.fetchone()
            if updated_record:
                return updated_record._asdict()
            else:
                return None

    def delete_record(self, record_id):
        """
        Deletes a record.

        :param record_id: int
        :param org_id: int
        :return: True if deleted, False if not found
        """
        with self.con.connect() as connection:
            delete_query = """
            DELETE FROM main_turf
            WHERE id = :record_id
            """
            result = connection.execute(
                text(delete_query),
                {
                    'record_id': record_id
                }
            )
            connection.commit()
            return result.rowcount > 0  # Returns True if a row was deleted