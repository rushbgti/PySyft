# future
from __future__ import annotations

# stdlib
from datetime import datetime
import json
import os
from signal import SIGTERM
import subprocess  # nosec
import sys
import time
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

# third party
from oblv import OblvClient
import requests

# relative
from ..core.node.common.exceptions import OblvEnclaveError
from ..core.node.common.exceptions import OblvUnAuthorizedError
from ..util import bcolors
from .constants import DOMAIN_CONNECTION_PORT
from .constants import LOCAL_MODE
from .oblv_proxy import check_oblv_proxy_installation_status


class DeploymentClient:

    deployment_id: str
    user_key_name: str
    client: List[Any] = []  # List of domain client objects
    oblv_client: OblvClient = None
    __conn_string: str
    __logs: Any
    __process: Any

    def __init__(
        self,
        domain_clients: List[Any],
        deployment_id: Optional[str] = None,
        oblv_client: Optional[OblvClient] = None,
        user_key_name: Optional[str] = None,
    ):
        self.deployment_id = deployment_id
        self.user_key_name = user_key_name
        self.oblv_client = oblv_client
        self.client = domain_clients
        self.__conn_string = ""
        self.__process = None
        self.__logs = None

    def make_request_to_enclave(
        self,
        request_method: Callable,
        connection_string: str,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ):
        header = {}
        if LOCAL_MODE:
            header["x-oblv-user-name"] = "enclave_test"
            header["x-oblv-user-role"] = "user"
        else:
            depl = self.oblv_client.deployment_info(self.deployment_id)
            if depl.is_deleted:
                raise Exception(
                    "User cannot connect to this deployment, as it is no longer available."
                )
        return request_method(
            connection_string,
            headers=header,
            params=params,
            files=files,
            data=data,
            json=json,
        )

    def set_conn_string(self, url: str):
        self.__conn_string = url

    def initiate_connection(self, connection_port: int = DOMAIN_CONNECTION_PORT):
        if LOCAL_MODE:
            self.__conn_string = f"http://127.0.0.1:{connection_port}"
            return
        check_oblv_proxy_installation_status()
        self.close_connection()  # To close any existing connections
        public_file_name = os.path.join(
            os.path.expanduser("~"),
            ".ssh",
            self.user_key_name,
            self.user_key_name + "_public.der",
        )
        private_file_name = os.path.join(
            os.path.expanduser("~"),
            ".ssh",
            self.user_key_name,
            self.user_key_name + "_private.der",
        )
        log_file_name = os.path.join(
            os.path.expanduser("~"),
            ".oblv_syft_logs",
            "proxy_logs_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + ".log",
        )
        # Creating directory if not exist
        os.makedirs(os.path.dirname(log_file_name), exist_ok=True)
        log_file = open(log_file_name, "wb")
        depl = self.oblv_client.deployment_info(self.deployment_id)
        if depl.is_deleted:
            raise Exception(
                "User cannot connect to this deployment, as it is no longer available."
            )
        try:
            if depl.is_dev_env:
                process = subprocess.Popen(  # nosec
                    [
                        "oblv",
                        "connect",
                        "--private-key",
                        private_file_name,
                        "--public-key",
                        public_file_name,
                        "--url",
                        depl.instance.service_url,
                        "--pcr0",
                        depl.pcr_codes[0],
                        "--pcr1",
                        depl.pcr_codes[1],
                        "--pcr2",
                        depl.pcr_codes[2],
                        "--port",
                        "443",
                        "--lport",
                        str(connection_port),
                        "--disable-pcr-check",
                    ],
                    stdout=log_file,
                    stderr=log_file,
                )
            else:
                process = subprocess.Popen(  # nosec
                    [
                        "oblv",
                        "connect",
                        "--private-key",
                        private_file_name,
                        "--public-key",
                        public_file_name,
                        "--url",
                        depl.instance.service_url,
                        "--pcr0",
                        depl.pcr_codes[0],
                        "--pcr1",
                        depl.pcr_codes[1],
                        "--pcr2",
                        depl.pcr_codes[2],
                        "--port",
                        "443",
                        "--lport",
                        str(connection_port),
                    ],
                    stdout=log_file,
                    stderr=log_file,
                )
            log_file_read = open(log_file_name, "r")
            while True:
                log_line = log_file_read.readline()
                if "Error:  Invalid PCR Values" in log_line:
                    raise Exception("PCR Validation Failed")
                if "Only one usage of each socket address" in log_line:
                    raise Exception(
                        "Another oblv proxy instance running. Either close that connection"
                        + "or change the *connection_port*"
                    )
                elif "error" in log_line.lower():
                    raise Exception(log_line)
                elif "listening on" in log_line:
                    break
        except Exception as e:
            print("Could not connect to Proxy")
            raise e
        else:
            print(
                f"Successfully connected to proxy on port {connection_port}. The logs can be found at {log_file_name}"
            )
        self.__conn_string = f"http://127.0.0.1:{connection_port}"
        self.__logs = log_file_name
        self.__process = process
        return

    def get_uploaded_datasets(self) -> Dict:
        if len(self.client) == 0:
            raise Exception(
                "No Domain Clients added. Set the propert *client* with the list of your domain logins"
            )
        if self.__conn_string is None:
            raise Exception(
                "proxy not running. Use the method connect_oblv_proxy to start the proxy."
            )
        elif self.__conn_string == "":
            raise Exception(
                "Either proxy not running or not initiated using syft."
                + " Run the method initiate_connection to initiate the proxy connection"
            )

        req = self.make_request_to_enclave(
            requests.get, connection_string=self.__conn_string + "/tensor/dataset/list"
        )
        if req.status_code == 401:
            raise OblvUnAuthorizedError()
        elif req.status_code == 400:
            raise OblvEnclaveError(req.json()["detail"])
        elif req.status_code == 422:
            print(req.text)
            # ToDo - Update here
            return "Failed"
        elif req.status_code != 200:
            raise OblvEnclaveError(
                f"Request to publish dataset failed with status {req.status_code}"
            )
        return req.json()  # This is the publish_request_id

    def publish_action(self, action: str, arguments, *args, **kwargs):
        if self.__conn_string is None:
            raise Exception(
                "proxy not running. Use the method connect_oblv_proxy to start the proxy."
            )
        elif self.__conn_string == "":
            raise Exception(
                "Either proxy not running or not initiated using syft. Run the method initiate_connection"
                + "to initiate the proxy connection"
            )
        file = None
        if len(arguments) == 2 and arguments[1]["type"] == "tensor":
            file = arguments[1]["value"]
            arguments[1]["value"] = "file"
        body = {
            "inputs": json.dumps(arguments),
            "args": json.dumps(args),
            "kwargs": json.dumps(kwargs),
        }

        req = self.make_request_to_enclave(
            requests.post,
            connection_string=self.__conn_string + f"/tensor/action?op={action}",
            data=body,
            files={"file": file},
        )

        if req.status_code == 401:
            raise OblvUnAuthorizedError()
        elif req.status_code == 400:
            raise OblvEnclaveError(req.json()["detail"])
        elif req.status_code == 422:
            print(req.text)
            # ToDo - Update here
            return "Failed"
        elif req.status_code != 200:
            raise OblvEnclaveError(
                "Request to publish dataset failed with status {}".format(
                    req.status_code
                )
            )
        else:
            # Status code 200
            # TODO - Remove this after oblv proxy is resolved
            data = req.json()
            if isinstance(data, dict) and data.get("detail") is not None:
                raise OblvEnclaveError(data["detail"])
            return data
        # #return req.json()

    def request_publish(self, dataset_id, sigma=0.5):
        if len(self.client) == 0:
            raise Exception(
                "No Domain Clients added. Set the propert *client* with the list of your domain logins"
            )
        if self.__conn_string is None:
            raise Exception(
                "proxy not running. Use the method connect_oblv_proxy to start the proxy."
            )
        elif self.__conn_string == "":
            raise Exception(
                "Either proxy not running or not initiated using syft. Run the method initiate_connection"
                + "to initiate the proxy connection"
            )

        req = self.make_request_to_enclave(
            requests.post,
            connection_string=self.__conn_string + "/tensor/publish/request",
            json={"dataset_id": dataset_id, "sigma": sigma},
        )
        if req.status_code == 401:
            raise OblvUnAuthorizedError()
        elif req.status_code == 400:
            raise OblvEnclaveError(req.json()["detail"])
        elif req.status_code == 422:
            print(req.text)
            # ToDo - Update here
            return "Failed"
        elif req.status_code != 200:
            raise OblvEnclaveError(
                "Request to publish dataset failed with status {}".format(
                    req.status_code
                )
            )
        else:
            # Status code 200
            # TODO - Remove this after oblv proxy is resolved

            data = req.json()
            if type(data) == dict and data.get("detail") is not None:
                raise OblvEnclaveError(data["detail"])
            # Here data is publish_request_id
            for domain_client in self.client:
                domain_client.oblv.publish_budget(
                    deployment_id=self.deployment_id,
                    publish_request_id=data,
                    client=self.oblv_client,
                )
            return data

    def check_publish_request_status(self, publish_request_id):
        if self.__conn_string is None:
            raise Exception(
                "proxy not running. Use the method connect_oblv_proxy to start the proxy."
            )
        elif self.__conn_string == "":
            raise Exception(
                "Either proxy not running or not initiated using syft. Run the method initiate_connection"
                + "to initiate the proxy connection"
            )

        req = self.make_request_to_enclave(
            requests.get,
            connection_string=self.__conn_string
            + "/tensor/publish/result_ready?publish_request_id="
            + publish_request_id,
        )

        if req.status_code == 401:
            raise OblvUnAuthorizedError()
        elif req.status_code == 400:
            raise OblvEnclaveError(req.json()["detail"])
        elif req.status_code == 422:
            print(req.text)
            # ToDo - Update here
            return "Failed"
        elif req.status_code != 200:
            raise OblvEnclaveError(
                "Request to publish dataset failed with status {}".format(
                    req.status_code
                )
            )
        else:
            result = req.json()
            if type(result) == str:
                print("Not yet Ready")
            elif type(result) != dict:
                for o in self.client:
                    o.oblv.publish_request_budget_deduction(
                        deployment_id=self.deployment_id,
                        publish_request_id=publish_request_id,
                        client=self.oblv_client,
                        budget_to_deduct=result,
                    )
                print("Result is ready")  # This is the publish_request_id
            else:
                # TODO - Remove this after oblv proxy is resolved
                if result.get("detail") is not None:
                    raise OblvEnclaveError(result["detail"])

    def fetch_result(self, publish_request_id):
        if self.__conn_string is None:
            raise Exception(
                "proxy not running. Use the method connect_oblv_proxy to start the proxy."
            )
        elif self.__conn_string == "":
            raise Exception(
                "Either proxy not running or not initiated using syft. Run the method initiate_connection"
                + "to initiate the proxy connection"
            )

        req = self.make_request_to_enclave(
            requests.get,
            connection_string=self.__conn_string
            + "/tensor/publish/result?request_id="
            + publish_request_id,
        )
        if req.status_code == 401:
            raise OblvUnAuthorizedError()
        elif req.status_code == 400:
            raise OblvEnclaveError(req.json()["detail"])
        elif req.status_code == 422:
            print(req.text)
            # ToDo - Update here
            return "Failed"
        elif req.status_code != 200:
            raise OblvEnclaveError(
                "Request to publish dataset failed with status {}".format(
                    req.status_code
                )
            )
        return req.json()

    def close_connection(self):
        if self.check_proxy_running():
            os.kill(self.__process.pid, SIGTERM)
        else:
            return "No Proxy Connection Running"

    def check_proxy_running(self):
        if self.__process is not None:
            if self.__process.poll() is not None:
                return False
            else:
                return True
        return False

    def fetch_current_proxy_logs(self, follow=False, tail=False):
        """_summary_

        Args:
            follow (bool, optional): To follow the logs as they grow. Defaults to False.
            tail (bool, optional): Only show the new generated logs.
                To be used only when follow is True. Defaults to False.
        """
        if self.__logs is None:
            print(
                bcolors.RED
                + bcolors.BOLD
                + "Exception"
                + bcolors.BLACK
                + bcolors.ENDC
                + ": Logs not initiated",
                file=sys.stderr,
            )
        log_file = open(self.__logs, "r")
        if not follow:
            print(log_file.read())
        else:
            if tail:
                log_file.seek(0, 2)
            while True:
                line = log_file.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                print(line)


# Todo - Method to check if proxy is running
# Todo
