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
        Retrieves all turfs assigned to an org with their geometries from tracts_2023

        :param org_id: int
        :return: List of dicts with nested geometries
        """
        if org_id == 0: # guest mode
            query = """
            WITH turf_data AS (
                SELECT * FROM main_turf WHERE organization_id IS NULL
            )
            SELECT
                td.id,
                td.tracts,
                td.description,
                td.organization_id,
                -- Dissolve all matched tract geometries into one geometry
                ST_AsGeoJSON(ST_MakeValid(ST_Union(t.geometry)))::json AS geometry,
                ST_XMin(ST_Envelope(ST_Union(t.geometry))) AS min_lon,
                ST_YMin(ST_Envelope(ST_Union(t.geometry))) AS min_lat,
                ST_XMax(ST_Envelope(ST_Union(t.geometry))) AS max_lon,
                ST_YMax(ST_Envelope(ST_Union(t.geometry))) AS max_lat
            FROM turf_data td
            LEFT JOIN LATERAL unnest(td.tracts) AS tract_id ON true
            LEFT JOIN tracts_2023 t ON t."GEOID" = tract_id
            GROUP BY td.id, td.tracts, td.description, td.organization_id;
            """
            results = self.query(query)
        else:
            query = """
            WITH turf_data AS (
                SELECT * FROM main_turf WHERE organization_id = :org_id
            )
            SELECT
                td.id,
                td.tracts,
                td.description,
                td.organization_id,
                ST_AsGeoJSON(ST_MakeValid(ST_Union(t.geometry)))::json AS geometry,
                ST_XMin(ST_Envelope(ST_Union(t.geometry))) AS min_lon,
                ST_YMin(ST_Envelope(ST_Union(t.geometry))) AS min_lat,
                ST_XMax(ST_Envelope(ST_Union(t.geometry))) AS max_lon,
                ST_YMax(ST_Envelope(ST_Union(t.geometry))) AS max_lat
            FROM turf_data td
            LEFT JOIN LATERAL unnest(td.tracts) AS tract_id ON true
            LEFT JOIN tracts_2023 t ON t."GEOID" = tract_id
            GROUP BY td.id, td.tracts, td.description, td.organization_id;
            """
            results = self.query(text(query), params={'org_id': org_id})
        
        # Convert to list of dicts and parse JSON fields
        records = results.to_dict(orient='records')
        for record in records:
            # Parse description if it's a string
            if isinstance(record.get('description'), str):
                record['description'] = json.loads(record['description'])
            # geometries is already parsed as JSON by PostgreSQL
        
        return records

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
        
    def get_suggested_tract_groupings(self, tracts):
        """
        Returns suggested tract groupings queries.
        
        :param tracts: list of tract GEOIDs
        :return: list of dicts with grouping suggestions
        """
        if not tracts:
            return []
        
        # Query to find neighboring tracts (tracts that share a boundary)
        placeholders = ','.join(['%s'] * len(tracts))
        
        neighboring_query = f"""
            WITH input_tracts AS (
                SELECT t1."GEOID", t1.geometry
                FROM tracts_2023 t1
                WHERE t1."GEOID" IN ({placeholders})
            ),
            neighboring_tracts AS (
                SELECT DISTINCT
                    t2."GEOID" AS neighbor_geoid
                FROM input_tracts it
                JOIN tracts_2023 t2
                    ON ST_Touches(it.geometry, t2.geometry)
                WHERE t2."GEOID" NOT IN ({placeholders})
            )
            SELECT neighbor_geoid
            FROM neighboring_tracts
            ORDER BY neighbor_geoid;
        """
        
        results = self.query(neighboring_query, tuple(tracts) + tuple(tracts))
        neighbor_geoids = [r['neighbor_geoid'] for r in results.to_dict(orient='records')]
        suggestions = [
            {
                'id': 1,
                'type': 'neighboring_tracts',
                'description': 'Tracts that share a boundary with your selected tracts',
                'tracts': neighbor_geoids
            },
            {
                'id': 2,
                'type': 'neighboring_tracts_copy',
                'description': 'Tracts that share a boundary with your selected tracts',
                'tracts': neighbor_geoids[:10]
            }
        ]
        
        return suggestions
        
    def get_demographics(self, tracts):
        """
        Retrieves demographics for a list of tracts from pdb2023tr table

        :param tracts: list of tract GEOIDs
        :return: Dict with demographics by tract and aggregated totals
        """
        if not tracts:
            return {
                "aggregated": {},
                "by_tract": []
            }
        
        # Define demographic columns to fetch
        demographic_columns = [
            '"GIDTR"',
            '"State_name"',
            '"County_name"',
            '"Tract"',
            '"Tot_Population_CEN_2020"',
            '"Hispanic_CEN_2020"',
            '"NH_Blk_alone_CEN_2020"',
            '"NH_Asian_alone_CEN_2020"',
            '"NH_AIAN_alone_CEN_2020"',
            '"Born_foreign_ACS_17_21"',
            '"Tot_Population_ACS_17_21"',
            '"Prs_Blw_Pov_Lev_ACS_17_21"',
            '"Pov_Univ_ACS_17_21"',
            '"Rel_Child_Under_6_ACS_17_21"',
            '"Rel_Family_HHD_ACS_17_21"',
            '"Crowd_Occp_U_ACS_17_21"',
            '"Tot_Occp_Units_ACS_17_21"',
            '"MLT_U2_9_STRC_ACS_17_21"',
            '"Tot_Housing_Units_ACS_17_21"',
            '"MLT_U10p_ACS_17_21"',
            '"ENG_VW_ACS_17_21"',
            '"Pop_5yrs_Over_ACS_17_21"',
            '"ENG_VW_SPAN_ACS_17_21"',
            '"ENG_VW_INDO_EURO_ACS_17_21"',
            '"ENG_VW_API_ACS_17_21"'
        ]
        
        # Build the query
        placeholders = ','.join(['%s'] * len(tracts))
        query = f"""
        SELECT {', '.join(demographic_columns)}
        FROM pdb2023tr
        WHERE "GIDTR" IN ({placeholders})
        """
        
        results = self.query(query, tuple(tracts))
        demographics_list = results.to_dict(orient='records')
        
        # Calculate aggregated statistics
        total_pop_cen_2020 = sum(d.get('Tot_Population_CEN_2020', 0) or 0 for d in demographics_list)
        total_hispanic = sum(d.get('Hispanic_CEN_2020', 0) or 0 for d in demographics_list)
        total_black = sum(d.get('NH_Blk_alone_CEN_2020', 0) or 0 for d in demographics_list)
        total_asian = sum(d.get('NH_Asian_alone_CEN_2020', 0) or 0 for d in demographics_list)
        total_aian = sum(d.get('NH_AIAN_alone_CEN_2020', 0) or 0 for d in demographics_list)
        
        # ACS data
        total_pop_acs = sum(d.get('Tot_Population_ACS_17_21', 0) or 0 for d in demographics_list)
        total_foreign_born = sum(d.get('Born_foreign_ACS_17_21', 0) or 0 for d in demographics_list)
        total_below_poverty = sum(d.get('Prs_Blw_Pov_Lev_ACS_17_21', 0) or 0 for d in demographics_list)
        total_pov_universe = sum(d.get('Pov_Univ_ACS_17_21', 0) or 0 for d in demographics_list)
        
        # Housing
        total_family_hhd = sum(d.get('Rel_Family_HHD_ACS_17_21', 0) or 0 for d in demographics_list)
        total_child_under_6 = sum(d.get('Rel_Child_Under_6_ACS_17_21', 0) or 0 for d in demographics_list)
        total_crowded = sum(d.get('Crowd_Occp_U_ACS_17_21', 0) or 0 for d in demographics_list)
        total_occupied = sum(d.get('Tot_Occp_Units_ACS_17_21', 0) or 0 for d in demographics_list)
        total_mlt_2_9 = sum(d.get('MLT_U2_9_STRC_ACS_17_21', 0) or 0 for d in demographics_list)
        total_housing_units = sum(d.get('Tot_Housing_Units_ACS_17_21', 0) or 0 for d in demographics_list)
        total_mlt_10p = sum(d.get('MLT_U10p_ACS_17_21', 0) or 0 for d in demographics_list)
        
        # Language
        total_limited_english = sum(d.get('ENG_VW_ACS_17_21', 0) or 0 for d in demographics_list)
        total_pop_5_over = sum(d.get('Pop_5yrs_Over_ACS_17_21', 0) or 0 for d in demographics_list)
        total_spanish = sum(d.get('ENG_VW_SPAN_ACS_17_21', 0) or 0 for d in demographics_list)
        total_indoeuro = sum(d.get('ENG_VW_INDO_EURO_ACS_17_21', 0) or 0 for d in demographics_list)
        total_api = sum(d.get('ENG_VW_API_ACS_17_21', 0) or 0 for d in demographics_list)
        
        # Calculate percentages for aggregated data
        aggregated = {
            'tot_population_cen_2020': int(total_pop_cen_2020),
            'pct_hispanic_cen_2020': round(total_hispanic / total_pop_cen_2020 * 100, 2) if total_pop_cen_2020 > 0 else 0,
            'pct_nh_blk_alone_cen_2020': round(total_black / total_pop_cen_2020 * 100, 2) if total_pop_cen_2020 > 0 else 0,
            'pct_nh_asian_alone_cen_2020': round(total_asian / total_pop_cen_2020 * 100, 2) if total_pop_cen_2020 > 0 else 0,
            'pct_nh_aian_alone_cen_2020': round(total_aian / total_pop_cen_2020 * 100, 2) if total_pop_cen_2020 > 0 else 0,
            'pct_born_foreign_acs_17_21': round(total_foreign_born / total_pop_acs * 100, 2) if total_pop_acs > 0 else 0,
            'pct_prs_blw_pov_lev_acs_17_21': round(total_below_poverty / total_pov_universe * 100, 2) if total_pov_universe > 0 else 0,
            'pct_rel_family_hhd_cen_2020': round(total_child_under_6 / total_family_hhd * 100, 2) if total_family_hhd > 0 else 0,
            'pct_crowd_occp_u_acs_17_21': round(total_crowded / total_occupied * 100, 2) if total_occupied > 0 else 0,
            'pct_mlt_u2_9_strc_acs_17_21': round(total_mlt_2_9 / total_housing_units * 100, 2) if total_housing_units > 0 else 0,
            'pct_mlt_u10p_acs_17_21': round(total_mlt_10p / total_housing_units * 100, 2) if total_housing_units > 0 else 0,
            'pct_eng_vw_acs_17_21': round(total_limited_english / total_pop_5_over * 100, 2) if total_pop_5_over > 0 else 0,
            'pct_eng_vw_span_acs_17_21': round(total_spanish / total_pop_5_over * 100, 2) if total_pop_5_over > 0 else 0,
            'pct_eng_vw_indoeuro_acs_17_21': round(total_indoeuro / total_pop_5_over * 100, 2) if total_pop_5_over > 0 else 0,
            'pct_eng_vw_api_acs_17_21': round(total_api / total_pop_5_over * 100, 2) if total_pop_5_over > 0 else 0,
        }
        
        return {
            "aggregated": aggregated,
            "by_tract": [] # by_tract - no longer needed
        }