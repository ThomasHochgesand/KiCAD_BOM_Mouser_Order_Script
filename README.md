# KICAD Order Script for mouser

This is a quick pythonscript to order parts from a KICAD BOM.

## PREREQUISITES

### Mouser API key
This script uses **YOUR** mouser api key. You need to login to mouser and generate that one. To ensure safety and prevent leaking your API key by mistake, this script will make use of environment variables on your system.

Add your api key to your environment variables with the name "MOUSER_API_KEY". This name can also be changed in the main.py file if you require another name.

### Move main.py and BOM-File in same directory
Pretty self explainory, huh? The script looks in the local directory for any bom files and will start doing it's work then.

# HOW TO USE
1. Clone the repository
2. Install requirements
3. Pay attention to PREREQUISITES section (<- IMPORTANT)
4. Run main.py

# STEP BY STEP For venv
1. Clone the repo
2. create virtual environment
3. activate virtual environment
4. export your mouser key env. variable like:
```bash
export MOUSER_API_KEY=****-****-****-****
```
5. change CSV_MOUSER_COLUMN_NAME accordingly
6. move the Bom .csv file into this project
7. Run main.py