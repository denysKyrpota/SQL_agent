"""
Tests for QueryService - main query workflow and SQL generation coordination.

Tests:
- Query attempt creation
- Two-stage SQL generation workflow
- Success and failure scenarios
- Error handling and status updates
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from backend.app.models.query import QueryAttempt
from backend.app.models.user import User
from backend.app.schemas.queries import CreateQueryRequest
from backend.app.schemas.common import QueryStatus
from backend.app.services.query_service import QueryService, SQLGenerationError
from backend.app.services.llm_service import LLMServiceUnavailableError
from backend.app.services.knowledge_base_service import KBExample


class TestCreateQueryAttempt:
    """Tests for complete query attempt creation workflow."""

    @pytest.mark.asyncio
    async def test_create_query_attempt_success(
        self,
        test_db: Session,
        test_user: User,
        mock_llm_response: dict,
        mock_schema_data: dict,
        mock_kb_examples: list[dict]
    ):
        """Test successful query creation with SQL generation."""
        # Create mocked services
        mock_llm = AsyncMock()
        mock_llm.select_relevant_tables = AsyncMock(return_value=["users", "sessions"])
        mock_llm.generate_sql = AsyncMock(
            return_value="SELECT u.id, u.username FROM users u WHERE u.active = true;"
        )

        mock_schema = MagicMock()
        mock_schema.get_table_names = MagicMock(return_value=["users", "sessions", "products"])
        mock_schema.filter_schema_by_tables = MagicMock(return_value=mock_schema_data["tables"])
        mock_schema.format_schema_for_llm = MagicMock(return_value="Schema text...")

        mock_kb = AsyncMock()
        kb_examples = [
            KBExample(
                filename="active_users.sql",
                title="Active Users",
                description="Get active users",
                sql="SELECT * FROM users WHERE active = true;"
            )
        ]
        # find_similar_examples returns tuple[list[KBExample], float]
        mock_kb.find_similar_examples = AsyncMock(return_value=(kb_examples, 0.75))

        # Create service with mocks
        service = QueryService(
            llm_service=mock_llm,
            schema_service=mock_schema,
            kb_service=mock_kb
        )

        # Create query request
        request = CreateQueryRequest(
            natural_language_query="Show me all active users"
        )

        # Execute
        response = await service.create_query_attempt(
            db=test_db,
            user_id=test_user.id,
            request=request
        )

        # Assertions
        assert response.id is not None
        assert response.natural_language_query == "Show me all active users"
        assert response.generated_sql is not None
        assert "SELECT" in response.generated_sql
        assert response.status == QueryStatus.NOT_EXECUTED
        assert response.generation_ms is not None
        assert response.generation_ms >= 0  # Can be 0 for very fast mocked operations
        assert response.error_message is None

        # Verify mocks were called
        mock_llm.select_relevant_tables.assert_called_once()
        mock_llm.generate_sql.assert_called_once()
        mock_schema.get_table_names.assert_called_once()
        mock_kb.find_similar_examples.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_query_attempt_llm_failure(
        self,
        test_db: Session,
        test_user: User
    ):
        """Test query creation when LLM service fails."""
        # Create mocked services
        mock_llm = AsyncMock()
        mock_llm.select_relevant_tables = AsyncMock(
            side_effect=LLMServiceUnavailableError("OpenAI API unavailable")
        )

        mock_schema = MagicMock()
        mock_schema.get_table_names = MagicMock(return_value=["users"])

        mock_kb = AsyncMock()

        service = QueryService(
            llm_service=mock_llm,
            schema_service=mock_schema,
            kb_service=mock_kb
        )

        request = CreateQueryRequest(
            natural_language_query="Show me all users"
        )

        # Should raise LLMServiceUnavailableError
        with pytest.raises(LLMServiceUnavailableError):
            await service.create_query_attempt(
                db=test_db,
                user_id=test_user.id,
                request=request
            )

    @pytest.mark.asyncio
    async def test_create_query_attempt_sql_generation_error(
        self,
        test_db: Session,
        test_user: User
    ):
        """Test query creation when SQL generation fails."""
        # Create mocked services
        mock_llm = AsyncMock()
        mock_llm.select_relevant_tables = AsyncMock(return_value=["users"])
        mock_llm.generate_sql = AsyncMock(
            side_effect=ValueError("Invalid response from LLM")
        )

        mock_schema = MagicMock()
        mock_schema.get_table_names = MagicMock(return_value=["users"])
        mock_schema.filter_schema_by_tables = MagicMock(return_value={})
        mock_schema.format_schema_for_llm = MagicMock(return_value="Schema...")

        mock_kb = AsyncMock()
        # find_similar_examples returns tuple[list[KBExample], float]
        mock_kb.find_similar_examples = AsyncMock(return_value=([], 0.0))

        service = QueryService(
            llm_service=mock_llm,
            schema_service=mock_schema,
            kb_service=mock_kb
        )

        request = CreateQueryRequest(
            natural_language_query="Show me all users"
        )

        # Execute
        response = await service.create_query_attempt(
            db=test_db,
            user_id=test_user.id,
            request=request
        )

        # Should create attempt but mark as failed
        assert response.id is not None
        assert response.generated_sql is None
        assert response.status == QueryStatus.FAILED_GENERATION
        assert response.error_message is not None
        assert "Invalid response" in response.error_message


class TestGenerateSQL:
    """Tests for two-stage SQL generation process."""

    @pytest.mark.asyncio
    async def test_generate_sql_full_workflow(self):
        """Test complete two-stage SQL generation."""
        # Mock services
        mock_llm = AsyncMock()
        mock_llm.select_relevant_tables = AsyncMock(
            return_value=["activity_activity", "auth_user"]
        )
        mock_llm.generate_sql = AsyncMock(
            return_value="SELECT a.id, u.username FROM activity_activity a JOIN auth_user u ON a.user_id = u.id;"
        )

        mock_schema = MagicMock()
        mock_schema.get_table_names = MagicMock(
            return_value=["activity_activity", "auth_user", "other_table"]
        )
        mock_schema.filter_schema_by_tables = MagicMock(return_value={})
        mock_schema.format_schema_for_llm = MagicMock(return_value="Filtered schema...")

        kb_example = KBExample(
            filename="activities.sql",
            title="Activities",
            description="Query activities",
            sql="SELECT * FROM activity_activity;"
        )
        mock_kb = AsyncMock()
        # find_similar_examples returns tuple[list[KBExample], float]
        mock_kb.find_similar_examples = AsyncMock(return_value=([kb_example], 0.8))

        service = QueryService(
            llm_service=mock_llm,
            schema_service=mock_schema,
            kb_service=mock_kb
        )

        # Execute
        sql = await service._generate_sql(
            natural_language_query="Show me activities with user names",
            user_id=1
        )

        # Verify result
        assert sql is not None
        assert "SELECT" in sql
        assert "activity_activity" in sql or "auth_user" in sql

        # Verify Stage 1: Table selection
        mock_schema.get_table_names.assert_called_once()
        mock_llm.select_relevant_tables.assert_called_once_with(
            table_names=["activity_activity", "auth_user", "other_table"],
            question="Show me activities with user names",
            max_tables=10
        )

        # Verify Stage 2: Schema filtering
        mock_schema.filter_schema_by_tables.assert_called_once_with(
            ["activity_activity", "auth_user"]
        )

        # Verify Stage 3: KB examples
        mock_kb.find_similar_examples.assert_called_once()
        call_kwargs = mock_kb.find_similar_examples.call_args.kwargs
        assert call_kwargs["question"] == "Show me activities with user names"
        assert call_kwargs["top_k"] == 3

        # Verify Stage 4: SQL generation
        mock_llm.generate_sql.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_sql_no_relevant_tables(self):
        """Test SQL generation when no relevant tables found."""
        mock_llm = AsyncMock()
        mock_llm.select_relevant_tables = AsyncMock(return_value=[])

        mock_schema = MagicMock()
        mock_schema.get_table_names = MagicMock(return_value=["users"])

        mock_kb = AsyncMock()

        service = QueryService(
            llm_service=mock_llm,
            schema_service=mock_schema,
            kb_service=mock_kb
        )

        # Even with empty tables, should still try to generate SQL
        mock_llm.generate_sql = AsyncMock(return_value="SELECT 1;")
        mock_schema.filter_schema_by_tables = MagicMock(return_value={})
        mock_schema.format_schema_for_llm = MagicMock(return_value="")
        # find_similar_examples returns tuple[list[KBExample], float]
        mock_kb.find_similar_examples = AsyncMock(return_value=([], 0.0))

        sql = await service._generate_sql(
            natural_language_query="Show me something",
            user_id=1
        )

        assert sql is not None


class TestUpdateAttempt:
    """Tests for query attempt update methods."""

    def test_update_attempt_success(self, test_db: Session, test_user: User):
        """Test updating query attempt with successful SQL generation."""
        # Create initial attempt
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Test query",
            generated_sql=None,
            status=QueryStatus.NOT_EXECUTED.value
        )
        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        service = QueryService()

        # Update with success
        updated = service._update_attempt_success(
            db=test_db,
            attempt_id=query.id,
            generated_sql="SELECT * FROM users;",
            generation_ms=1500
        )

        assert updated.generated_sql == "SELECT * FROM users;"
        assert updated.status == QueryStatus.NOT_EXECUTED.value
        assert updated.generation_ms == 1500
        assert updated.generated_at is not None
        assert updated.error_message is None

    def test_update_attempt_failure(self, test_db: Session, test_user: User):
        """Test updating query attempt with generation failure."""
        # Create initial attempt
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Test query",
            generated_sql=None,
            status=QueryStatus.NOT_EXECUTED.value
        )
        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        service = QueryService()

        # Update with failure
        updated = service._update_attempt_failure(
            db=test_db,
            attempt_id=query.id,
            error_message="LLM service unavailable",
            generation_ms=2000
        )

        assert updated.generated_sql is None
        assert updated.status == QueryStatus.FAILED_GENERATION.value
        assert updated.generation_ms == 2000
        assert updated.generated_at is None
        assert updated.error_message == "LLM service unavailable"

    def test_update_attempt_not_found(self, test_db: Session):
        """Test updating non-existent query attempt."""
        service = QueryService()

        with pytest.raises(ValueError, match="not found"):
            service._update_attempt_success(
                db=test_db,
                attempt_id=99999,
                generated_sql="SELECT 1;",
                generation_ms=100
            )


class TestCreateInitialAttempt:
    """Tests for initial query attempt record creation."""

    def test_create_initial_attempt(self, test_db: Session, test_user: User):
        """Test creating initial query attempt record."""
        service = QueryService()

        from datetime import datetime
        created_at = datetime.utcnow().isoformat() + "Z"

        attempt = service._create_initial_attempt(
            db=test_db,
            user_id=test_user.id,
            natural_language_query="Show me all users",
            created_at=created_at
        )

        assert attempt.id is not None
        assert attempt.user_id == test_user.id
        assert attempt.natural_language_query == "Show me all users"
        assert attempt.generated_sql is None
        assert attempt.status == QueryStatus.NOT_EXECUTED.value
        assert attempt.generated_at is None
        assert attempt.generation_ms is None
        assert attempt.error_message is None

    def test_create_initial_attempt_persisted(self, test_db: Session, test_user: User):
        """Test that initial attempt is persisted to database."""
        service = QueryService()

        from datetime import datetime
        created_at = datetime.utcnow().isoformat() + "Z"

        attempt = service._create_initial_attempt(
            db=test_db,
            user_id=test_user.id,
            natural_language_query="Test query",
            created_at=created_at
        )

        # Verify it's in the database
        db_attempt = test_db.query(QueryAttempt).filter(
            QueryAttempt.id == attempt.id
        ).first()

        assert db_attempt is not None
        assert db_attempt.natural_language_query == "Test query"


class TestServiceInitialization:
    """Tests for QueryService initialization."""

    def test_init_with_default_services(self):
        """Test service initialization with default dependencies."""
        service = QueryService()

        assert service.llm is not None
        assert service.schema is not None
        assert service.kb is not None

    def test_init_with_custom_services(self):
        """Test service initialization with custom dependencies."""
        mock_llm = AsyncMock()
        mock_schema = MagicMock()
        mock_kb = AsyncMock()

        service = QueryService(
            llm_service=mock_llm,
            schema_service=mock_schema,
            kb_service=mock_kb
        )

        assert service.llm == mock_llm
        assert service.schema == mock_schema
        assert service.kb == mock_kb
