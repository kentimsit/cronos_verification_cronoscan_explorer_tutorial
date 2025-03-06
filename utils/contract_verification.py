import json
import requests


class ContractVerification:
    def __init__(self, cronoscan_api_key: str, cronos_explorer_api_key: str):
        self.cronoscan_api_key = cronoscan_api_key
        self.cronos_explorer_api_key = cronos_explorer_api_key

    def query_cronoscan(self, contract_address: str) -> dict:
        """
        Query the Cronoscan API for contract details
        """
        api_response = requests.request(
            method="GET",
            url=f"https://api.cronoscan.com/api?module=contract&action=getsourcecode&address={contract_address}&apikey={self.cronoscan_api_key}",
        )
        with open("./data/cronoscan_response.json", "w") as f:
            json.dump(api_response.json(), f)
        result = api_response.json().get("result", [])
        # Process and display the response
        result_0 = result[0]
        contract_name = result_0.get("ContractName", "")
        print("Contract name: ", contract_name)
        compiler_version = result_0.get("CompilerVersion", "")
        compiler_version = (
            compiler_version.split("+")[0].replace("v", "").replace(" ", "").strip()
        )
        print("Compiler version: ", compiler_version)
        optimization_used = result_0.get("OptimizationUsed", "")
        if optimization_used == "1":
            optimization_used = True
        else:
            optimization_used = False
        print("Optimization used: ", optimization_used)
        optimization_runs = result_0.get("Runs", "")
        try:
            optimization_runs = int(optimization_runs)
        except:
            optimization_runs = 0
        print("Optimization runs: ", optimization_runs)
        constructor_arguments = result_0.get("ConstructorArguments", "")
        source_code = result_0.get("SourceCode", "")
        source_code_scenario = "source_code_single_file"
        if source_code.startswith("{{"):
            source_code_scenario = "standard_json"
        elif source_code.startswith("{"):
            source_code_scenario = "source_code_multiple_files"

        print("Type of source code: ", source_code_scenario)
        # print("Full response from Cronoscan:")
        # print(json.dumps(result, indent=4))
        res = {
            "contract_address": contract_address,
            "contract_name": contract_name,
            "compiler_version": compiler_version,
            "optimization_used": optimization_used,
            "optimization_runs": optimization_runs,
            "constructor_arguments": constructor_arguments,
            "source_code": source_code,
            "source_code_scenario": source_code_scenario,
            "full_response": result,
        }
        file_path = "./data/contract_details.json"
        with open(file_path, "w") as f:
            json.dump(res, f)
        return res

    def verify_contract(self, contract_details: dict) -> dict:
        """
        Verify the contract using the Cronos Explorer API
        """
        contract_address = contract_details.get("contract_address")
        contract_name = contract_details.get("contract_name")
        compiler_version = contract_details.get("compiler_version")
        optimization_used = contract_details.get("optimization_used")
        optimization_runs = contract_details.get("optimization_runs")
        constructor_arguments = contract_details.get("constructor_arguments")
        source_code = contract_details.get("source_code")
        source_code_scenario = contract_details.get("source_code_scenario")
        # Prepare source code for verification
        file_path = "./data/source_code.json"
        if source_code_scenario == "standard_json":
            print("Requesting verification: standard JSON...")
            source_code = source_code[1:-1]
            with open(file_path, "w") as f:
                f.write(source_code)
        if source_code_scenario == "source_code_single_file":
            print("Requesting verification: source code single file...")
            file_path_sol = "./data/source_code.sol"
            with open(file_path_sol, "w") as f:
                f.write(source_code)
            with open(file_path_sol, "r") as f:
                source_code_updated = f.read()
            source_code_json = {
                "language": "Solidity",
                "sources": {contract_name + ".sol": {"content": source_code_updated}},
            }
            if optimization_used:
                settings = {"optimizer": {"enabled": True, "runs": optimization_runs}}
            else:
                settings = {"optimizer": {"enabled": False, "runs": optimization_runs}}
            source_code_json["settings"] = settings
            file_path = "./data/source_code.json"
            with open(file_path, "w") as f:
                json.dump(source_code_json, f)
        if source_code_scenario == "source_code_multiple_files":
            print("Requesting verification: source code multiple files...")
            with open(file_path, "w") as f:
                f.write(source_code)
            with open(file_path, "r") as f:
                source_code_updated = json.load(f)
            source_code_json = {
                "language": "Solidity",
                "sources": source_code_updated,
            }
            if optimization_used:
                settings = {"optimizer": {"enabled": True, "runs": optimization_runs}}
            else:
                settings = {"optimizer": {"enabled": False, "runs": optimization_runs}}
            source_code_json["settings"] = settings
            with open(file_path, "w") as f:
                json.dump(source_code_json, f)
        # Create contract verification request
        verification_request_response = requests.request(
            method="POST",
            url=f"https://explorer-api.cronos.org/mainnet/api/v1/contract/verifySourceCode?apikey={self.cronos_explorer_api_key}",
            files={"contract[]": open(file_path, "rb")},
            data={
                "contractAddress": contract_address,
                "name": contract_name,
                "compilerVersion": compiler_version,
                "constructorArguments": constructor_arguments,
                "compilerType": "solidity-standard-json-input",
            },
        )
        print(verification_request_response.text)
        # print(verification_request_response.json())
        verification_request_data = verification_request_response.json()
        verification_id = verification_request_data.get("result", {}).get(
            "contractVerificationId", ""
        )
        print("contractVerificationId: ", verification_id)
        return {
            "contract_address": contract_address,
            "verification_id": verification_id,
            "full_response": verification_request_data,
        }

    def get_verification_status(self, verification_id: str) -> dict:
        """
        Get the verification status of the contract
        """
        # Check verification status
        verification_response = requests.request(
            method="GET",
            url=f"https://explorer-api.cronos.org/mainnet/api/v1/contract/checkVerifyStatus?guid={verification_id}&apikey={self.cronos_explorer_api_key}",
        )
        print(verification_response.json())
        return verification_response.json()
