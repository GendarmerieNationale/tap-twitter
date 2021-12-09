"""REST client handling, including TwitterStream base class."""

import requests
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable

from memoization import cached

from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream
from singer_sdk.authenticators import BearerTokenAuthenticator


SCHEMAS_DIR: Path = Path(__file__).parent / Path("./schemas")
MAX_RESULTS: int = 100


class TwitterStream(RESTStream):
    """Twitter stream class."""

    url_base: str = "https://api.twitter.com/2"
    max_results: int = MAX_RESULTS

    # OR use a dynamic url_base:
    # @property
    # def url_base(self) -> str:
    #     """Return the API URL root, configurable via tap settings."""
    #     return self.config["api_url"]

    records_jsonpath: str = "$.data[*]"  # Or override `parse_response`.
    next_page_token_jsonpath: str = "$.meta.next_token"  # Or override `get_next_page_token`.

    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        """Return a new authenticator object."""
        return BearerTokenAuthenticator.create_for_stream(
            self,
            token=self.config.get("bearer_token")
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        # If not using an authenticator, you may also provide inline auth headers:
        # headers["Private-Token"] = self.config.get("auth_token")
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages."""
        if self.next_page_token_jsonpath:
            all_matches = extract_jsonpath(
                self.next_page_token_jsonpath, response.json()
            )
            first_match = next(iter(all_matches), None)
            next_page_token = first_match
        else:
            next_page_token = response.headers.get("X-Next-Page", None)

        return next_page_token

    def make_query(self):
        twitter_handle = self.config.get("account_handle")
        return f"from:{twitter_handle}"

    def get_additional_url_params(self) -> Dict:
        pass

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {"query": self.make_query(), "max_results": self.max_results}
        # twitter_handle = self.config.get("account_handle")
        # params["query"] = f"from:{twitter_handle}"
        if next_page_token:
            params["next_token"] = next_page_token
        if self.replication_key:
            params["sort"] = "asc"
            params["order_by"] = self.replication_key
        if self.get_additional_url_params():
            params.update(self.get_additional_url_params())
        return params

    # def prepare_request_payload(
    #     self, context: Optional[dict], next_page_token: Optional[Any]
    # ) -> Optional[dict]:
    #     """Prepare the data payload for the REST API request.
    #
    #     By default, no payload will be sent (return None).
    #     """
    #     # TODO: Delete this method if no payload is required. (Most REST APIs.)
    #     return None

    # def parse_response(self, response: requests.Response) -> Iterable[dict]:
    #     """Parse the response and return an iterator of result rows."""
    #     # TODO: Parse response body and return a set of records.
    #     yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    # def post_process(self, row: dict, context: Optional[dict]) -> dict:
    #     """As needed, append or transform raw data to match expected structure."""
    #     # TODO: Delete this method if not needed.
    #     return row