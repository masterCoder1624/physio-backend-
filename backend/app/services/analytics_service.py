from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.mongo_models import PatientDocument, PaymentDocument
from app.repositories.base_repository import BaseRepository


def _start_of_month(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=value.tzinfo)


def _offset_months(value: datetime, offset: int) -> datetime:
    year = value.year + ((value.month - 1 + offset) // 12)
    month = ((value.month - 1 + offset) % 12) + 1
    return value.replace(year=year, month=month)


class AnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.patient_repo = BaseRepository(PatientDocument, db, collection_name="patients")
        self.payment_repo = BaseRepository(PaymentDocument, db, collection_name="payments")

    async def get_physio_summary(
        self,
        physio_id: str,
        months: int = 6,
        new_patients_days: int = 30,
    ) -> Dict[str, object]:
        now = datetime.now(timezone.utc)
        patient_docs = await self.patient_repo.collection.find(
            {"physiotherapist_id": physio_id},
            {"id": 1, "primary_condition": 1, "created_at": 1},
        ).to_list(length=None)

        patient_ids = [str(doc.get("id")) for doc in patient_docs if doc.get("id")]
        total_patients = len(patient_ids)
        condition_distribution: Dict[str, int] = {}
        for doc in patient_docs:
            condition = (doc.get("primary_condition") or "General Physiotherapy").strip()
            condition_distribution[condition] = condition_distribution.get(condition, 0) + 1

        period_start = now - timedelta(days=new_patients_days)
        new_patients = sum(
            1
            for doc in patient_docs
            if doc.get("created_at") is not None
            and (
                doc["created_at"].replace(tzinfo=timezone.utc)
                if doc["created_at"].tzinfo is None
                else doc["created_at"]
            )
            >= period_start
        )

        paid_payments = []
        if patient_ids:
            paid_payments = await self.payment_repo.collection.find(
                {"patient_id": {"$in": patient_ids}, "status": "paid"}
            ).to_list(length=None)

        total_revenue = sum(float(payment.get("amount") or 0.0) for payment in paid_payments)
        paid_sessions = len(paid_payments)

        revenue_by_month = await self._build_monthly_trend(
            patient_ids, months, now, source="payments",
        )
        patients_by_month = await self._build_monthly_trend(
            physio_id, months, now, source="patients",
        )

        return {
            "total_patients": total_patients,
            "total_revenue": round(total_revenue, 2),
            "paid_sessions": paid_sessions,
            "new_patients": new_patients,
            "condition_distribution": condition_distribution,
            "revenue_by_month": revenue_by_month,
            "patients_by_month": patients_by_month,
        }

    async def _build_monthly_trend(
        self,
        target: object,
        months: int,
        now: datetime,
        source: str,
    ) -> List[Dict[str, object]]:
        items: List[Dict[str, object]] = []
        current_month = _start_of_month(now)

        for offset in range(months - 1, -1, -1):
            month_start = _offset_months(current_month, -offset)
            month_end = _offset_months(month_start, 1)
            label = month_start.strftime("%b %Y")

            if source == "payments":
                count = await self.payment_repo.collection.count_documents(
                    {
                        "patient_id": {"$in": target if isinstance(target, list) else []},
                        "status": "paid",
                        "created_at": {"$gte": month_start, "$lt": month_end},
                    }
                )
                cursor = self.payment_repo.collection.find(
                    {
                        "patient_id": {"$in": target if isinstance(target, list) else []},
                        "status": "paid",
                        "created_at": {"$gte": month_start, "$lt": month_end},
                    },
                    {"amount": 1},
                )
                docs = await cursor.to_list(length=None)
                amount = sum(float(doc.get("amount") or 0.0) for doc in docs)
                items.append({"month": label, "amount": round(amount, 2), "count": count})
            else:
                count = await self.patient_repo.collection.count_documents(
                    {
                        "physiotherapist_id": target,
                        "created_at": {"$gte": month_start, "$lt": month_end},
                    }
                )
                items.append({"month": label, "amount": float(count), "count": count})

        return items
