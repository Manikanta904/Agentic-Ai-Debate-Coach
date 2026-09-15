from datetime import datetime
from typing import List

from app.mongodb.debate_repository import debate_repository
from app.debate.schemas.report_schema import DebateReport


class ReportService:
    """
    Service class for retrieving debate analysis reports.
    """

    def get_all_reports(self) -> List[DebateReport]:
        """
        Retrieve all debate reports.
        """
        reports = debate_repository.get_all_reports()
        return [self._convert_document(report) for report in reports]

    def get_report_by_id(self, report_id: str) -> DebateReport | None:
        """
        Retrieve a report using its MongoDB ObjectId.
        """
        report = debate_repository.get_report_by_id(report_id)
        if report is None:
            return None
        return self._convert_document(report)

    def get_reports_by_session(self, session_id: int) -> List[DebateReport]:
        """
        Retrieve reports for a debate session.
        """
        reports = debate_repository.get_reports_by_session(session_id)
        return [self._convert_document(report) for report in reports]

    def get_reports_by_user(self, user_id: int) -> List[DebateReport]:
        """
        Retrieve reports for a user.
        """
        reports = debate_repository.get_reports_by_user(user_id)
        return [self._convert_document(report) for report in reports]

    def get_reports_by_user_ids(self, user_ids: List[int]) -> List[DebateReport]:
        """
        Retrieve reports for a list of user IDs.
        """
        reports = debate_repository.get_reports_by_user_ids(user_ids)
        return [self._convert_document(report) for report in reports]

    @staticmethod
    def _format_datetime(val) -> str | None:
        if val is None:
            return None
        if hasattr(val, "isoformat"):
            res = val.isoformat()
            if not res.endswith("Z") and "+" not in res and "-" not in res[10:]:
                res += "Z"
            return res
        res_str = str(val)
        if res_str and not res_str.endswith("Z") and "+" not in res_str and "-" not in res_str[10:]:
            res_str += "Z"
        return res_str

    @classmethod
    def _convert_document(cls, document: dict) -> DebateReport:
        """
        Convert a MongoDB document into a DebateReport schema safely.
        """
        created_at_str = cls._format_datetime(document.get("created_at"))
        updated_at_str = cls._format_datetime(document.get("updated_at"))

        return DebateReport(
            report_id=str(document["_id"]),
            session_id=document["session_id"],
            user_id=document.get("user_id"),
            topic_id=document.get("topic_id"),
            input_type=document.get("input_type") or "text",
            media_filename=document.get("media_filename"),
            transcript=document.get("transcript") or {},
            argument_analysis=document.get("argument_analysis") or {},
            logical_fallacy_analysis=document.get("logical_fallacy_analysis") or {},
            counterargument=document.get("counterargument") or {},
            ai_debate_opponent=document.get("ai_debate_opponent") or {},
            judge_evaluation=document.get("judge_evaluation") or document.get("judge_categories") or {},
            performance=document.get("performance") or {},
            coaching=document.get("coaching") or {},
            recommendations=document.get("recommendations") or {},
            learning_path=document.get("learning_path") or {},
            observability=document.get("observability") or {},
            created_at=created_at_str,
            updated_at=updated_at_str,
        )


report_service = ReportService()
