"""
Tests for query API endpoints.

Tests:
- POST /api/queries - Create query and generate SQL
- GET /api/queries/{id} - Get query details
- GET /api/queries - List queries with pagination
- POST /api/queries/{id}/execute - Execute query
- GET /api/queries/{id}/results - Get paginated results
- GET /api/queries/{id}/export - Export results as CSV
- POST /api/queries/{id}/rerun - Re-run query
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.query import QueryAttempt, QueryResultsManifest
from backend.app.models.user import User


class TestCreateQuery:
    """Tests for POST /api/queries endpoint."""

    def test_create_query_success(
        self,
        authenticated_client: TestClient,
        test_user: User,
        sample_query_attempt: QueryAttempt,
    ):
        """Test successful query creation with SQL generation."""
        from backend.app.schemas.queries import QueryAttemptResponse
        from backend.app.schemas.common import QueryStatus
        from datetime import datetime
        from unittest.mock import AsyncMock, patch

        # Mock the service response with proper DTO
        mock_response = QueryAttemptResponse(
            id=sample_query_attempt.id,
            natural_language_query=sample_query_attempt.natural_language_query,
            generated_sql=sample_query_attempt.generated_sql,
            status=QueryStatus.NOT_EXECUTED,
            created_at=datetime.utcnow().isoformat() + "Z",
            generated_at=datetime.utcnow().isoformat() + "Z",
            generation_ms=1500,
            error_message=None,
        )

        with patch("backend.app.api.queries.query_service.create_query_attempt", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            response = authenticated_client.post(
                "/api/queries",
                json={"natural_language_query": "Show me all active users"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["natural_language_query"] == "Show me all active users"
            assert "generated_sql" in data
            assert data["status"] == "not_executed"

    def test_create_query_unauthenticated(self, client: TestClient):
        """Test query creation without authentication."""
        response = client.post(
            "/api/queries",
            json={"natural_language_query": "Show me all users"},
        )

        assert response.status_code == 401

    def test_create_query_empty_query(self, authenticated_client: TestClient):
        """Test query creation with empty natural language query."""
        response = authenticated_client.post(
            "/api/queries",
            json={"natural_language_query": "   "},  # Whitespace only
        )

        assert response.status_code == 422  # Validation error

    def test_create_query_too_long(self, authenticated_client: TestClient):
        """Test query creation with query exceeding max length."""
        long_query = "a" * 5001  # Max is 5000

        response = authenticated_client.post(
            "/api/queries",
            json={"natural_language_query": long_query},
        )

        assert response.status_code == 422

    def test_create_query_missing_field(self, authenticated_client: TestClient):
        """Test query creation with missing required field."""
        response = authenticated_client.post("/api/queries", json={})

        assert response.status_code == 422


class TestGetQuery:
    """Tests for GET /api/queries/{id} endpoint."""

    def test_get_query_success(
        self,
        authenticated_client: TestClient,
        sample_query_attempt: QueryAttempt,
    ):
        """Test successful query retrieval."""
        response = authenticated_client.get(f"/api/queries/{sample_query_attempt.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_query_attempt.id
        assert data["natural_language_query"] == sample_query_attempt.natural_language_query

    def test_get_query_not_found(self, authenticated_client: TestClient):
        """Test getting non-existent query."""
        response = authenticated_client.get("/api/queries/99999")

        assert response.status_code == 404

    def test_get_query_unauthorized(
        self,
        authenticated_client: TestClient,
        test_db: Session,
        test_admin: User,
    ):
        """Test getting another user's query (non-admin)."""
        # Create query for admin user
        admin_query = QueryAttempt(
            user_id=test_admin.id,
            natural_language_query="Admin's query",
            generated_sql="SELECT * FROM admin_table;",
            status="not_executed",
        )

        test_db.add(admin_query)
        test_db.commit()
        test_db.refresh(admin_query)

        # Try to access as regular user
        response = authenticated_client.get(f"/api/queries/{admin_query.id}")

        assert response.status_code == 403

    def test_get_query_admin_can_access_all(
        self,
        admin_client: TestClient,
        sample_query_attempt: QueryAttempt,
    ):
        """Test that admin can access any user's query."""
        response = admin_client.get(f"/api/queries/{sample_query_attempt.id}")

        assert response.status_code == 200


class TestListQueries:
    """Tests for GET /api/queries endpoint."""

    def test_list_queries_success(
        self,
        authenticated_client: TestClient,
        sample_query_attempt: QueryAttempt,
    ):
        """Test successful query listing."""
        response = authenticated_client.get("/api/queries")

        assert response.status_code == 200
        data = response.json()
        assert "queries" in data
        assert "pagination" in data
        assert len(data["queries"]) > 0

    def test_list_queries_pagination(
        self,
        authenticated_client: TestClient,
        test_db: Session,
        test_user: User,
    ):
        """Test query listing with pagination."""
        # Create 25 queries
        for i in range(25):
            query = QueryAttempt(
                user_id=test_user.id,
                natural_language_query=f"Query {i}",
                generated_sql=f"SELECT {i};",
                status="not_executed",
            )
            test_db.add(query)

        test_db.commit()

        # Get first page (20 items)
        response = authenticated_client.get("/api/queries?page=1&page_size=20")

        assert response.status_code == 200
        data = response.json()
        assert len(data["queries"]) == 20
        assert data["pagination"]["total_count"] == 25
        assert data["pagination"]["total_pages"] == 2

        # Get second page
        response = authenticated_client.get("/api/queries?page=2&page_size=20")

        assert response.status_code == 200
        data = response.json()
        assert len(data["queries"]) == 5

    def test_list_queries_status_filter(
        self,
        authenticated_client: TestClient,
        test_db: Session,
        test_user: User,
    ):
        """Test query listing with status filter."""
        # Create queries with different statuses
        success_query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Success query",
            generated_sql="SELECT 1;",
            status="success",
        )

        failed_query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Failed query",
            generated_sql=None,
            status="failed_generation",
            error_message="LLM error",
        )

        test_db.add_all([success_query, failed_query])
        test_db.commit()

        # Filter by success status
        response = authenticated_client.get("/api/queries?status_filter=success")

        assert response.status_code == 200
        data = response.json()
        assert all(q["status"] == "success" for q in data["queries"])

    def test_list_queries_invalid_page(self, authenticated_client: TestClient):
        """Test query listing with invalid page number."""
        response = authenticated_client.get("/api/queries?page=0")

        assert response.status_code == 400

    def test_list_queries_user_sees_only_own(
        self,
        authenticated_client: TestClient,
        test_db: Session,
        test_admin: User,
    ):
        """Test that regular users see only their own queries."""
        # Create query for admin
        admin_query = QueryAttempt(
            user_id=test_admin.id,
            natural_language_query="Admin query",
            generated_sql="SELECT 1;",
            status="not_executed",
        )

        test_db.add(admin_query)
        test_db.commit()

        # List as regular user
        response = authenticated_client.get("/api/queries")

        assert response.status_code == 200
        data = response.json()

        # Should not see admin's query
        query_ids = [q["id"] for q in data["queries"]]
        assert admin_query.id not in query_ids


class TestExecuteQuery:
    """Tests for POST /api/queries/{id}/execute endpoint."""

    def test_execute_query_success(
        self,
        authenticated_client: TestClient,
        sample_query_attempt: QueryAttempt,
        test_db: Session,
    ):
        """Test successful query execution."""
        from backend.app.services.postgres_execution_service import QueryResult
        from unittest.mock import AsyncMock, patch
        from datetime import datetime

        # Mock successful execution
        mock_result = QueryResult(
            columns=["id", "username"],
            rows=[[1, "alice"], [2, "bob"]],
            total_rows=2,
            execution_ms=150,
        )

        async def mock_execute_with_update(db, query):
            # Update the query object as the real service would
            query.executed_at = datetime.utcnow()
            query.execution_ms = 150
            query.status = "success"
            db.commit()
            return mock_result

        with patch("backend.app.api.queries.postgres_service.execute_query_attempt", new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = mock_execute_with_update

            response = authenticated_client.post(
                f"/api/queries/{sample_query_attempt.id}/execute"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "results" in data
            assert data["results"]["total_rows"] == 2

    def test_execute_query_not_found(self, authenticated_client: TestClient):
        """Test executing non-existent query."""
        response = authenticated_client.post("/api/queries/99999/execute")

        assert response.status_code == 404

    def test_execute_query_no_sql(
        self, authenticated_client: TestClient, failed_query: QueryAttempt
    ):
        """Test executing query with no generated SQL."""
        response = authenticated_client.post(f"/api/queries/{failed_query.id}/execute")

        assert response.status_code == 400
        assert "SQL generation failed" in response.json()["detail"]

    def test_execute_query_already_executed(
        self,
        authenticated_client: TestClient,
        executed_query_with_results: tuple[QueryAttempt, QueryResultsManifest],
    ):
        """Test re-executing already successful query."""
        query, _ = executed_query_with_results

        response = authenticated_client.post(f"/api/queries/{query.id}/execute")

        assert response.status_code == 400
        assert "already been executed" in response.json()["detail"]


class TestGetResults:
    """Tests for GET /api/queries/{id}/results endpoint."""

    def test_get_results_success(
        self,
        authenticated_client: TestClient,
        executed_query_with_results: tuple[QueryAttempt, QueryResultsManifest],
    ):
        """Test successful results retrieval."""
        query, manifest = executed_query_with_results

        response = authenticated_client.get(f"/api/queries/{query.id}/results?page=1")

        assert response.status_code == 200
        data = response.json()
        assert data["attempt_id"] == query.id
        assert data["total_rows"] == 3
        assert len(data["columns"]) == 3
        assert len(data["rows"]) == 3

    def test_get_results_no_results(
        self,
        authenticated_client: TestClient,
        sample_query_attempt: QueryAttempt,
    ):
        """Test getting results for query that hasn't been executed."""
        response = authenticated_client.get(
            f"/api/queries/{sample_query_attempt.id}/results"
        )

        assert response.status_code == 404
        assert "No results available" in response.json()["detail"]

    def test_get_results_invalid_page(
        self,
        authenticated_client: TestClient,
        executed_query_with_results: tuple[QueryAttempt, QueryResultsManifest],
    ):
        """Test getting results with invalid page number."""
        query, _ = executed_query_with_results

        response = authenticated_client.get(f"/api/queries/{query.id}/results?page=999")

        assert response.status_code == 400

    def test_get_results_pagination(
        self,
        authenticated_client: TestClient,
        test_db: Session,
        test_user: User,
    ):
        """Test results pagination with multiple pages."""
        # Create query
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Large result set",
            generated_sql="SELECT * FROM large_table;",
            status="success",
        )

        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        # Create manifest with 1000 rows (2 pages at 500 rows each)
        columns = ["id", "value"]
        rows = [[i, f"value_{i}"] for i in range(1000)]

        manifest = QueryResultsManifest(
            attempt_id=query.id,
            columns_json=json.dumps(columns),
            results_json=json.dumps(rows),
            total_rows=1000,
            page_size=500,
            page_count=2,
        )

        test_db.add(manifest)
        test_db.commit()

        # Get first page
        response = authenticated_client.get(f"/api/queries/{query.id}/results?page=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["rows"]) == 500
        assert data["current_page"] == 1
        assert data["page_count"] == 2

        # Get second page
        response = authenticated_client.get(f"/api/queries/{query.id}/results?page=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["rows"]) == 500
        assert data["current_page"] == 2


class TestExportResults:
    """Tests for GET /api/queries/{id}/export endpoint."""

    def test_export_results_success(
        self,
        authenticated_client: TestClient,
        executed_query_with_results: tuple[QueryAttempt, QueryResultsManifest],
    ):
        """Test successful CSV export."""
        query, _ = executed_query_with_results

        response = authenticated_client.get(f"/api/queries/{query.id}/export")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        # Check CSV content
        csv_content = response.text
        assert "id,username,email" in csv_content
        assert "alice" in csv_content

    def test_export_results_not_found(
        self,
        authenticated_client: TestClient,
        sample_query_attempt: QueryAttempt,
    ):
        """Test exporting results for query that hasn't been executed."""
        response = authenticated_client.get(
            f"/api/queries/{sample_query_attempt.id}/export"
        )

        assert response.status_code == 404

    def test_export_results_too_large(
        self,
        authenticated_client: TestClient,
        executed_query_with_results: tuple[QueryAttempt, QueryResultsManifest],
    ):
        """Test exporting results that exceed size limit."""
        from backend.app.services.export_service import ExportTooLargeError
        from unittest.mock import AsyncMock, patch

        query, _ = executed_query_with_results

        with patch("backend.app.api.queries.export_service.export_to_csv", new_callable=AsyncMock) as mock_export:
            # Mock export service to raise error
            mock_export.side_effect = ExportTooLargeError(
                "Result set too large: 15000 rows. Maximum is 10000 rows."
            )

            response = authenticated_client.get(f"/api/queries/{query.id}/export")

            assert response.status_code == 413


class TestRerunQuery:
    """Tests for POST /api/queries/{id}/rerun endpoint."""

    def test_rerun_query_success(
        self,
        authenticated_client: TestClient,
        sample_query_attempt: QueryAttempt,
        test_db: Session,
        test_user: User,
    ):
        """Test successful query re-run."""
        from unittest.mock import AsyncMock, patch
        from backend.app.schemas.queries import QueryAttemptResponse
        from backend.app.schemas.common import QueryStatus
        from datetime import datetime

        # Mock the service response
        mock_response = QueryAttemptResponse(
            id=sample_query_attempt.id + 1,  # New attempt ID
            natural_language_query=sample_query_attempt.natural_language_query,
            generated_sql=sample_query_attempt.generated_sql,
            status=QueryStatus.NOT_EXECUTED,
            created_at=datetime.utcnow().isoformat() + "Z",
            generated_at=datetime.utcnow().isoformat() + "Z",
            generation_ms=1500,
            error_message=None,
        )

        async def mock_create_with_db_record(db, user_id, request):
            # Create actual database record so the endpoint can query it
            new_query = QueryAttempt(
                id=sample_query_attempt.id + 1,
                user_id=user_id,
                natural_language_query=request.natural_language_query,
                generated_sql=sample_query_attempt.generated_sql,
                status="not_executed",
                created_at=datetime.utcnow(),
                generated_at=datetime.utcnow(),
                generation_ms=1500,
            )
            db.add(new_query)
            db.commit()
            db.refresh(new_query)
            return mock_response

        with patch("backend.app.api.queries.query_service.create_query_attempt", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = mock_create_with_db_record

            response = authenticated_client.post(
                f"/api/queries/{sample_query_attempt.id}/rerun"
            )

            assert response.status_code == 201
            data = response.json()
            assert data["original_attempt_id"] == sample_query_attempt.id
            assert data["natural_language_query"] == sample_query_attempt.natural_language_query

    def test_rerun_query_not_found(self, authenticated_client: TestClient):
        """Test re-running non-existent query."""
        response = authenticated_client.post("/api/queries/99999/rerun")

        assert response.status_code == 404

    def test_rerun_query_unauthorized(
        self,
        authenticated_client: TestClient,
        test_db: Session,
        test_admin: User,
    ):
        """Test re-running another user's query."""
        # Create query for admin user
        admin_query = QueryAttempt(
            user_id=test_admin.id,
            natural_language_query="Admin's query",
            generated_sql="SELECT * FROM admin_table;",
            status="not_executed",
        )

        test_db.add(admin_query)
        test_db.commit()
        test_db.refresh(admin_query)

        response = authenticated_client.post(f"/api/queries/{admin_query.id}/rerun")

        assert response.status_code == 403
