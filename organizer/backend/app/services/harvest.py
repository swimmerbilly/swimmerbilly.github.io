import httpx

from app.config import settings

HARVEST_API_BASE = "https://api.harvestapp.com/v2"


class HarvestError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class HarvestClient:
    def __init__(
        self,
        access_token: str | None = None,
        account_id: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.access_token = access_token or settings.harvest_access_token
        self.account_id = account_id or settings.harvest_account_id
        self.user_agent = user_agent or settings.harvest_user_agent

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.account_id)

    def _headers(self) -> dict[str, str]:
        if not self.is_configured:
            raise HarvestError("Harvest is not configured. Set HARVEST_ACCESS_TOKEN and HARVEST_ACCOUNT_ID.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Harvest-Account-Id": self.account_id,
            "User-Agent": self.user_agent,
        }

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                f"{HARVEST_API_BASE}{path}",
                headers=self._headers(),
                **kwargs,
            )

        if response.status_code >= 400:
            detail = response.text
            try:
                payload = response.json()
                detail = payload.get("message", detail)
            except ValueError:
                pass
            raise HarvestError(detail, status_code=response.status_code)

        if response.status_code == 204:
            return {}
        return response.json()

    async def get_me(self) -> dict:
        return await self._request("GET", "/users/me")

    async def list_projects(self, is_active: bool | None = None) -> list[dict]:
        projects: list[dict] = []
        page = 1

        while True:
            params: dict[str, str | int | bool] = {"page": page, "per_page": 2000}
            if is_active is not None:
                params["is_active"] = is_active

            payload = await self._request("GET", "/projects", params=params)
            projects.extend(payload.get("projects", []))

            next_page = payload.get("next_page")
            if not next_page:
                break
            page = next_page

        return projects

    async def get_project(self, project_id: int) -> dict:
        return await self._request("GET", f"/projects/{project_id}")
