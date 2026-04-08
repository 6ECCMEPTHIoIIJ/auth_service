# ruff: noqa: B008

from auth_service.app.modules.auth.dtos.signin import SigninRequestBody, SigninResponse
from auth_service.app.modules.auth.dtos.sigup import SignupResponse
from auth_service.app.modules.auth.use_cases.signin.controller import SigninController
from auth_service.app.modules.auth.use_cases.signup.controller import SignupController
from fastapi import APIRouter, Depends, Request, Response, status

from .dtos import GetMeResponse, SignupRequestBody
from .use_cases.csrf import CsrfTokenController
from .use_cases.me import MeController

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=GetMeResponse, status_code=status.HTTP_200_OK)
async def get_me(
    request: Request,
    me_controller: MeController = Depends(MeController.provider),
) -> GetMeResponse:
    return me_controller._get(request)


@router.get("/csrf", status_code=status.HTTP_204_NO_CONTENT)
async def issue_csrf_token(
    response: Response,
    csrf_controller: CsrfTokenController = Depends(CsrfTokenController.provider),
) -> None:
    csrf_controller.issue(response)


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    request_body: SignupRequestBody,
    signup_controller: SignupController = Depends(SignupController.provider),
) -> SignupResponse:
    return await signup_controller.signup(request_body)


@router.post(
    "/signin",
    response_model=SigninResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signin(
    request_body: SigninRequestBody,
    request: Request,
    response: Response,
    signin_controller: SigninController = Depends(SigninController.provider),
) -> SigninResponse:
    return await signin_controller.signin(request_body, request, response)
