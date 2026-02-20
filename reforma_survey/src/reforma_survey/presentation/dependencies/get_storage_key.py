from uuid import UUID


def get_template_asset_key(owner_id: UUID, template_id: UUID, filename: str) -> str:
    return f"templates/user-{owner_id}/template-{template_id}/{filename}"


def get_survey_image_key(survey_id: UUID, question_id: UUID, filename: str) -> str:
    return f"surveys/survey-{survey_id}/question-{question_id}/{filename}"


def get_report_file_key(report_id: UUID, file_format: str) -> str:
    return f"reports/report-{report_id}/report.{file_format}"
