import asyncio
import asyncpg

async def test_db_connection():
    try:
        conn = await asyncpg.connect('postgresql://user_mmjwbpycud:rw9KIOXNheM3YYZEwvsR@devinapps-backend-prod.cluster-clussqewa0rh.us-west-2.rds.amazonaws.com/db_pmovtfhicd?sslmode=require')
        print('Successfully connected to the database')

        # Test creating a table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name TEXT
            )
        ''')
        print('Successfully created test table')

        # Test inserting data
        await conn.execute("INSERT INTO test_table (name) VALUES ($1)", "Test Name")
        print('Successfully inserted data into test table')

        # Test querying data
        row = await conn.fetchrow("SELECT * FROM test_table WHERE name = $1", "Test Name")
        if row:
            print(f'Successfully queried data: {row}')
        else:
            print('No data found in test table')

        # Clean up
        await conn.execute("DROP TABLE test_table")
        print('Successfully dropped test table')

        await conn.close()
    except Exception as e:
        print(f'Error during database operations: {e}')

if __name__ == "__main__":
    asyncio.run(test_db_connection())
