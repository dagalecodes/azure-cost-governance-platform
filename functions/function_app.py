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

@app.timer_trigger(
    schedule="0 30 6 * * *",
    arg_name="anomalyTimer",
    run_on_startup=False,
    use_monitor=False
)
def AnomalyDetector(anomalyTimer: func.TimerRequest) -> None:

    logging.info(f"AnomalyDetector triggered at {datetime.datetime.now()}")

    try:
        credential = DefaultAzureCredential()

        # Pull cached cost data from Blob Storage
        blob_service = BlobServiceClient(
            account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
            credential=credential
        )

        container_client = blob_service.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client("latest-costs.json")

        data = json.loads(
            blob_client.download_blob().readall()
        )

        costs = data.get("costs", [])

        if not costs:
            logging.warning("No cost data found for anomaly detection")
            return

        # Group costs by date → daily totals
        daily_totals = {}
        for record in costs:
            date = record["date"]
            cost = record["cost"]
            daily_totals[date] = daily_totals.get(date, 0) + cost

        sorted_dates = sorted(daily_totals.keys())

        if len(sorted_dates) < 2:
            logging.info("Not enough data for anomaly detection")
            return

        # Today's cost
        today_key = sorted_dates[-1]
        today_cost = daily_totals[today_key]

        # 7-day rolling average (excluding today)
        last_7_days = sorted_dates[-8:-1]
        if not last_7_days:
            last_7_days = sorted_dates[:-1]

        avg_cost = sum(daily_totals[d] for d in last_7_days) / len(last_7_days)

        logging.info(f"Today: ${today_cost:.4f} | 7-day avg: ${avg_cost:.4f}")

        # Anomaly threshold → 20% above average
        THRESHOLD = 0.20

        if avg_cost > 0 and today_cost > avg_cost * (1 + THRESHOLD):
            spike_pct = ((today_cost - avg_cost) / avg_cost) * 100

            logging.warning(
                f"ANOMALY DETECTED: Today ${today_cost:.4f} "
                f"is {spike_pct:.1f}% above 7-day avg ${avg_cost:.4f}"
            )

            # Save anomaly to Blob Storage
            anomaly = {
                "detected": datetime.datetime.utcnow().isoformat() + "Z",
                "date": today_key,
                "todayCost": round(today_cost, 4),
                "sevenDayAvg": round(avg_cost, 4),
                "spikePercent": round(spike_pct, 2),
                "threshold": THRESHOLD * 100,
                "status": "ANOMALY"
            }

            anomaly_blob = container_client.get_blob_client("latest-anomaly.json")
            anomaly_blob.upload_blob(
                json.dumps(anomaly, indent=2),
                overwrite=True
            )

            logging.info("Anomaly saved to Blob Storage")

            # TODO: Trigger Logic App (Step 9)
            # We will wire this in the next step

        else:
            logging.info(f"Spending normal — no anomaly detected")

            # Save clean status
            normal = {
                "checked": datetime.datetime.utcnow().isoformat() + "Z",
                "date": today_key,
                "todayCost": round(today_cost, 4),
                "sevenDayAvg": round(avg_cost, 4),
                "status": "NORMAL"
            }

            anomaly_blob = container_client.get_blob_client("latest-anomaly.json")
            anomaly_blob.upload_blob(
                json.dumps(normal, indent=2),
                overwrite=True
            )

    except Exception as e:
        logging.error(f"AnomalyDetector failed: {str(e)}")
        raise