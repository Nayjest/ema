from ema.linear_api import LinearApi, LinearConfig, Team
from dotenv import load_dotenv

def test_teams():
    load_dotenv('.env.test')
    api = LinearApi(LinearConfig())
    teams = api.teams()
    assert isinstance(teams[0], Team)
    assert teams[0].id
    assert teams[0].name
    assert teams[0].key

def test_team():
    load_dotenv('.env.test')
    api = LinearApi(LinearConfig())
    teams = api.teams()
    team = teams[0]
    assert team == api.find_team(team.name)
    assert team == api.find_team(team.id)
    assert team == api.find_team(team.key)
