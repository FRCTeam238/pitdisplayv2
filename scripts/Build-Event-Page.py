import os
import time
import datetime as dt
from pathlib import Path

import tbaapiv3client
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

api_key = os.environ.get("TBA_API_KEY")
if not api_key:
    raise RuntimeError(
        "TBA_API_KEY is not set. Copy .env.example to .env and add your "
        "The Blue Alliance API key."
    )

configuration = tbaapiv3client.Configuration(
    host = "https://www.thebluealliance.com/api/v3",
    api_key = {
        'X-TBA-Auth-Key': api_key
    }
)

api_client = tbaapiv3client.ApiClient(configuration)

    
    

try:
    while True:
        api_instance = tbaapiv3client.TeamApi(api_client)
        team = api_instance.get_team(team_key = "frc238")
       # print(team)
        print(team.team_number)
        with open ('./docs/event.md', 'w') as file:
            file.write(team.name)

        time.sleep(25)
except KeyboardInterrupt:
    print("Goodbye Wordle!")





















