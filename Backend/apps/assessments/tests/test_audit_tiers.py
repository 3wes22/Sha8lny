from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_audit_tier1_runs_and_reports_only_stage1():
    # Tier-1 audit must restrict its coverage report to stage-1 single_choice
    # (no stage-2 floor noise). The command calls sys.exit(); both pass/fail
    # exit codes are acceptable here — we only assert on the report content.
    out = StringIO()
    try:
        call_command("scenario_corpus_audit", "--tier", "1", "--skip-duplicates", stdout=out)
    except SystemExit:
        pass
    text = out.getvalue()
    assert "stage 1 single_choice" in text
    assert "stage 2 single_choice" not in text
    assert "stage 2 multi_select" not in text
    assert "stage 2 open_ended" not in text


@pytest.mark.django_db
def test_audit_tier2_reports_stage2_not_stage1():
    out = StringIO()
    try:
        call_command("scenario_corpus_audit", "--tier", "2", "--skip-duplicates", stdout=out)
    except SystemExit:
        pass
    text = out.getvalue()
    assert "stage 2 single_choice" in text
    assert "stage 1 single_choice" not in text
