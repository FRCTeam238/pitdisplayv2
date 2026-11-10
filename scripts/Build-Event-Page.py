import time
import datetime as dt
import tbaapiv3client

configuration = tbaapiv3client.Configuration(
    host = "https://www.thebluealliance.com/api/v3",
    api_key = {
        'X-TBA-Auth-Key':''
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





















