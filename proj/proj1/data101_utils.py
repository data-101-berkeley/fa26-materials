try:
    import psycopg
except ModuleNotFoundError as err:
    import psycopg2 as psycopg # if psycopg>=3 is not found on datahub

import sql

import dill as pickle

from pathlib import Path
from subprocess import run, PIPE

RESULTS_DIR = "results"
N_TUPLES = 10
# EXPORT_PDF_TYPE = "latex" # use this until libssl1.0-dev is installed

class GradingUtil(object):

    def __init__(self, projname):
        self.projname = projname

        self.pg_conn = None
        self.pg_cur = None

    def prepare_autograder(self, db_name=None):
        Path(RESULTS_DIR).mkdir(parents=False, exist_ok=True)

        if db_name:
            # use default user
            print("Opening additional database connection for grading.")
            self.pg_conn = psycopg.connect(
                database=db_name, host="localhost", port="5432")
            self.pg_cur = self.pg_conn.cursor()

    ### QUERY EXECUTION METHODS ###
    
    def run_sql(self, query, explain=False, explain_analyze=False):
        """Executes SQL statement(s) as a query string.

        Args:
            query (str) - SQL statement(s) to execute. Semicolon can only be omitted
                if you are executing a single statement.
            explain (bool) - True if you want to prepend EXPLAIN to the query
            explain_analyze (bool) - True if you want to prepend EXPLAIN ANAYLZE to the query

        Returns:
            If there was only 1 SQL statement, the return type will be either pandas.DataFrame (if the
            query resulted in a table with rows) or None otherwise.
                
            If there were multiple SQL statements, the return type will be a list
            where each element in the list is the output table of each statement as a pandas.DataFrame
            or None if the output had no rows.

            NOTE: An output of None can happen if SELECT ... WHERE ... filters out all rows
            or if you're creating a table/view/materialized view, for example.

        Raises:
            ValueError if:
                query is empty,
                explain and explain_analyze are both True, or
                query contains more than 1 SQL statement
            ConnectionError if postgres connection is not open
        """
        if query.strip() == '':
            raise ValueError("Empty query string")

        if explain and explain_analyze:
            raise ValueError("explain and explain_analyze parameters cannot both be set to True")
        
        if self.pg_conn is None or self.pg_cur is None:
            raise ConnectionError("Postgres connection and cursor not set. Must call prepare_autograder method first before calling query method")

        if explain:
            query = "EXPLAIN " + query
        elif explain_analyze:
            query = "EXPLAIN ANALYZE " + query

        results = []

        # execute all SQL statements and fetch first result
        # (otherwise if we call nextset() first, it will move cursor past first result)
        try:
            rows = self.pg_cur.execute(query).fetchall()
            output = pd.DataFrame.from_records(rows)
            results.append(output)
        except psycopg.ProgrammingError as e:
                # If a SQL statement like CREATE TABLE or CREATE VIEW is run,
                # calling .fetchall() will result in an error.
                if str(e) == "the last operation didn't produce a result":
                    results.append(None)
                else:
                    raise e

        # if the query string has multiple SQL statements, there can be multiple output tables.
        # get all of them and return them as a list
        while self.pg_cur.nextset():
            try:
                rows = self.pg_cur.fetchall()
                output = pd.DataFrame.from_records(rows)
                results.append(output)                
            except psycopg.ProgrammingError as e:
                # If a SQL statement like CREATE TABLE or CREATE VIEW is run,
                # calling .fetchall() will result in an error.
                if str(e) == "the last operation didn't produce a result":
                    results.append(None)
                else:
                    raise e

        if len(results) == 1:
            return results[0]
        return results 
        
    def run_file(self, path_to_sql_file, explain=False, explain_analyze=False, use_queries_dir=True):
        """Runs the SQL statement(s) in the given SQL file.
        If the .sql file extension is not provided, it is automatically added.

        Args:
            path_to_sql_file (str) - path to SQL file you want to execute
            explain (bool) - See the docstring of GradingUtil.execute
            explain_analyze (bool) - See the docstring of GradingUtil.execute
            use_queries_dir (bool) - True if you want to prepend `self.queries_dir` to the file path. Default True.

        Returns:
            See the docstring of GradingUtil.execute
        """
        if path_to_sql_file[-4:] != ".sql":
            path_to_sql_file += ".sql"

        with open(f"{self.queries_dir}/{path_to_sql_file}", "r") as f:
            results = self.run_sql(f.read())
        
        return results

    def prepare_submission_and_cleanup(self):
        if self.pg_conn:
            print("Closing grading database connection.")
            self.pg_conn.close()
            self.pg_conn = None

        command = ["zip",
                   "-r", f"{RESULTS_DIR}.zip",
                   RESULTS_DIR]
        results = run(command, stdout=PIPE, stderr=PIPE)
        if results.stderr:
            raise RuntimeError(results.stderr)

    def test_query_executes(self, query):
        # https://eli.thegreenplace.net/2008/08/21/robust-exception-handling/
        try:
            return self.pg_cur.execute(query)
            #self.pg_cur.fetchmany(N_TUPLES)
        except:
            self.pg_conn.rollback()
            raise

    # cache results because sql magic not supported in otter grader
    @staticmethod
    def save_results(pkl_fname, *args):
        pkl_fname = f"{RESULTS_DIR}/{pkl_fname}.pkl"
        with open(pkl_fname, 'wb') as f:
            for arg in args:
                if type(arg) == sql.run.resultset.ResultSet:
                    arg = arg.DataFrame() # convert jupysql to dataframe
                pickle.dump(arg, f)
        with open(pkl_fname, 'rb') as f:
            ret_vals = [pickle.load(f) for _ in args]
        return ret_vals

    # https://stackoverflow.com/questions/18675863/load-data-from-python-pickle-file-in-a-loop
    @staticmethod
    def load_results(pkl_fname):
        def pickleLoader(pklFile):
            try:
                while True:
                    yield pickle.load(pklFile)
            except EOFError:
                pass

        pkl_fname = f"{RESULTS_DIR}/{pkl_fname}.pkl"
        with open(pkl_fname, 'rb') as f:
            return [event for event in pickleLoader(f)]
