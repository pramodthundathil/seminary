#!/bin/bash
# Exit on any error
set -e

# Navigate to project directory
cd /var/www/seminary

# Activate virtual environment
source seminaryenv/bin/activate

# Fetch all tables in public schema
echo "Fetching tables..."
TABLES=$(sudo -u postgres psql -d seminary -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public';")

echo "Disabling all triggers and foreign key constraints (as postgres superuser)..."
for table in $TABLES; do
    # Trim whitespace
    table=$(echo $table | xargs)
    if [ -n "$table" ]; then
        sudo -u postgres psql -d seminary -c "ALTER TABLE \"$table\" DISABLE TRIGGER ALL;"
    fi
done

echo "Loading complete_data.json fixture..."
python manage.py loaddata complete_data.json --verbosity 2 || {
    echo "Error loading fixture. Re-enabling constraints..."
    for table in $TABLES; do
        table=$(echo $table | xargs)
        if [ -n "$table" ]; then
            sudo -u postgres psql -d seminary -c "ALTER TABLE \"$table\" ENABLE TRIGGER ALL;"
        fi
    done
    exit 1
}

echo "Re-enabling all triggers and foreign key constraints (as postgres superuser)..."
for table in $TABLES; do
    table=$(echo $table | xargs)
    if [ -n "$table" ]; then
        sudo -u postgres psql -d seminary -c "ALTER TABLE \"$table\" ENABLE TRIGGER ALL;"
    fi
done

echo "Database fixture loaded and constraints successfully re-enabled!"
