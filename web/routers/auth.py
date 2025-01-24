from fastapi import APIRouter, Depends, status, Query
from starlette.responses import RedirectResponse
from typing import Optional, Annotated
from ..dependencies import RegisteredUserCompact, verify_token
from database.ORM import ORM
from database.models import RegisteredUser
from database.scoreService import ScoreService
from database.util import parse_score_filters

router = APIRouter()
orm = ORM()
score_service = ScoreService(orm.sessionmaker())

@router.post("/logout")
async def logout(token: Annotated[RegisteredUserCompact, Depends(verify_token)]):
    if not token:
        return {"message": "user not logged in"}
    response = RedirectResponse('/', status_code=302)
    response.delete_cookie('session_token', '/')
    return response

@router.get('/users/{user_id}', tags=['auth'])
def get_user(user_id: int):
    """
    Fetches a user from the database from their user_id
    """
    return {"user": orm.session.get(RegisteredUser, user_id)}

@router.get('/scores', tags=['auth'])
def get_score(beatmap_id: int, user_id: int, mode: str = 'osu', filters: Optional[str] = None, metric: str = 'pp'):
    filters = parse_score_filters(mode, filters)
    """
    Fetches a user's scores on a beatmap
    """

    return {"score": score_service.get_user_scores(beatmap_id, user_id, mode, filters, metric)}

@router.post("/initial_fetch_self/", status_code=status.HTTP_202_ACCEPTED)
def initial_fetch(token: Annotated[RegisteredUserCompact, Depends(verify_token)], catch_converts: Annotated[ bool , Query(description='Fetch ctb converts?')] = False):
    from ..webapi import tq
    print('token v')
    print(token)

    data = ('initial_fetch', {'user_id': token['user_id'], 'catch_converts': catch_converts})
    tq.enqueue(data)
    items = {"user_id": token['user_id'],
             "catch_converts": catch_converts,
             "queue": tq.q.queue}
    return items