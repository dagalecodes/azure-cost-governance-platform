import azure.functions as func
import datetime
import json
import logging
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

SUBSCRIPTION_ID = "69d8cd24-2eb5-4f77-a92d-49d33a2f9f1e"
STORAGE_ACCOUNT = "stcostdashboard6431"
CONTAINER_NAME  = "cost-data"

@app.timer_trigger(
    schedule="0 0 6 * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False
)
def CostDataFetcher(myTimer: func.TimerRequest) -> None:

    logging.info(f"CostDataFetcher triggered at {datetime.datetime.now()}")

    try:
        # Step 1 — Authenticate using Managed Identity (zero credentials)
        credential = DefaultAzureCredential()
        logging.info("Authentication successful")

        # Step 2 — Pull cost data from Cost Management API
        client = CostManagementClient(credential)

        today = datetime.date.today()
        first_of_month = today.replace(day=1)

        scope = f"/subscriptions/{SUBSCRIPTION_ID}"

        query = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": first_of_month.strftime("%Y-%m-%dT00:00:00Z"),
                "to": today.strftime("%Y-%m-%dT23:59:59Z")
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {
                        "name": "Cost",
                        "function": "Sum"
                    }
                },
                "grouping": [
                    {
                        "type": "Dimension",
                        "name": "ServiceName"
                    }
                ]
            }
        }

        result = client.query.usage(scope=scope, parameters=query)
        logging.info("Cost data retrieved successfully")

        # Step 3 — Process and structure the data
        cost_data = {
            "lastRefreshed": datetime.datetime.utcnow().isoformat() + "Z",
            "subscriptionId": SUBSCRIPTION_ID,
            "period": {
                "from": first_of_month.strftime("%Y-%m-%d"),
                "to": today.strftime("%Y-%m-%d")
            },
            "costs": []
        }

        if result.rows:
            for row in result.rows:
                cost_data["costs"].append({
                    "cost": round(float(row[0]), 4),
                    "date": str(row[1]),
                    "service": str(row[2]),
                    "currency": str(row[3]) if len(row) > 3 else "USD"
                })

        # Step 4 — Cache to Blob Storage
        blob_service = BlobServiceClient(
            account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
            credential=credential
        )

        container_client = blob_service.get_container_client(CONTAINER_NAME)

        try:
            container_client.create_container()
            logging.info(f"Container {CONTAINER_NAME} created")
        except Exception:
            logging.info(f"Container {CONTAINER_NAME} already exists")

        blob_client = container_client.get_blob_client("latest-costs.json")
        blob_client.upload_blob(
            json.dumps(cost_data, indent=2),
            overwrite=True
        )

        logging.info(f"Cost data cached successfully → {len(cost_data['costs'])} records")

    except Exception as e:
        logging.error(f"CostDataFetcher failed: {str(e)}")
        raise