BASE_URL = "https://api.mouser.com/api/v1.0"

''' USER VARIABLES - CHANGE VALUES HERE '''
ENVIRONMENT_VARIABLE_API_KEY_NAME = "MOUSER_API_KEY"    # name of your environment variable (if you need another name for some reason on your system)

CSV_MOUSER_COLUMN_NAME = "MouserNr"                       # how you named your column
CSV_DELIMITER = ","                                     # the delimiter of your .csv-file
                                    
API_TIMEOUT_MAX_RETRIES = 10                            # max retries if api decides to return errors -> possibly due to my dataprocessing?
API_TIMEOUT_SLEEP_S = 2                                 # wait time between retries in seconds