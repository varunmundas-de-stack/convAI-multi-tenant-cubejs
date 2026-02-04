"""
AST-based SQL generation system.
Replaces string concatenation with type-safe, tree-based SQL construction.
"""
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


# ============================================================================
# AST Node Base Classes
# ============================================================================

class ASTNode(ABC):
    """Base class for all AST nodes"""

    @abstractmethod
    def to_sql(self, dialect: str = "duckdb") -> str:
        """Generate SQL from this node"""
        pass

    def validate(self) -> List[str]:
        """Validate node structure, return list of errors"""
        return []


# ============================================================================
# Expression Nodes
# ============================================================================

@dataclass
class ColumnRef(ASTNode):
    """Column reference: table.column"""
    column: str
    table: Optional[str] = None
    alias: Optional[str] = None

    def to_sql(self, dialect: str = "duckdb") -> str:
        parts = []
        if self.table:
            parts.append(self.table)
        parts.append(self.column)

        sql = ".".join(parts)
        if self.alias:
            sql += f" AS {self.alias}"
        return sql


@dataclass
class Literal(ASTNode):
    """Literal value"""
    value: Any
    data_type: Optional[str] = None

    def to_sql(self, dialect: str = "duckdb") -> str:
        if isinstance(self.value, str):
            # Escape single quotes
            escaped = self.value.replace("'", "''")
            return f"'{escaped}'"
        elif self.value is None:
            return "NULL"
        elif isinstance(self.value, bool):
            return "TRUE" if self.value else "FALSE"
        else:
            return str(self.value)


@dataclass
class AggregateExpr(ASTNode):
    """Aggregate function: SUM, AVG, COUNT, etc."""
    function: str  # SUM, AVG, COUNT, MIN, MAX
    expression: Union[ColumnRef, str]
    distinct: bool = False
    alias: Optional[str] = None

    def to_sql(self, dialect: str = "duckdb") -> str:
        distinct_str = "DISTINCT " if self.distinct else ""

        if isinstance(self.expression, ColumnRef):
            expr_sql = self.expression.to_sql(dialect)
        else:
            expr_sql = self.expression

        sql = f"{self.function}({distinct_str}{expr_sql})"

        if self.alias:
            sql += f" AS {self.alias}"
        return sql


@dataclass
class BinaryExpr(ASTNode):
    """Binary expression: left operator right"""
    left: Union[ColumnRef, Literal, 'BinaryExpr']
    operator: str  # =, <, >, <=, >=, !=, IN, LIKE, AND, OR
    right: Union[ColumnRef, Literal, List[Literal], 'BinaryExpr']

    def to_sql(self, dialect: str = "duckdb") -> str:
        left_sql = self.left.to_sql(dialect) if isinstance(self.left, ASTNode) else str(self.left)

        if isinstance(self.right, list):
            # IN clause
            right_values = [v.to_sql(dialect) if isinstance(v, ASTNode) else str(v) for v in self.right]
            right_sql = f"({', '.join(right_values)})"
        elif isinstance(self.right, ASTNode):
            right_sql = self.right.to_sql(dialect)
        else:
            right_sql = str(self.right)

        return f"{left_sql} {self.operator} {right_sql}"


@dataclass
class CaseExpr(ASTNode):
    """CASE WHEN expression"""
    conditions: List[tuple]  # List of (condition, result) tuples
    else_result: Optional[Any] = None
    alias: Optional[str] = None

    def to_sql(self, dialect: str = "duckdb") -> str:
        sql = "CASE"

        for condition, result in self.conditions:
            cond_sql = condition.to_sql(dialect) if isinstance(condition, ASTNode) else condition
            result_sql = result.to_sql(dialect) if isinstance(result, ASTNode) else result
            sql += f" WHEN {cond_sql} THEN {result_sql}"

        if self.else_result:
            else_sql = self.else_result.to_sql(dialect) if isinstance(self.else_result, ASTNode) else self.else_result
            sql += f" ELSE {else_sql}"

        sql += " END"

        if self.alias:
            sql += f" AS {self.alias}"
        return sql


# ============================================================================
# Clause Nodes
# ============================================================================

@dataclass
class SelectClause(ASTNode):
    """SELECT clause"""
    expressions: List[Union[ColumnRef, AggregateExpr, Literal, str]]
    distinct: bool = False

    def to_sql(self, dialect: str = "duckdb") -> str:
        distinct_str = "DISTINCT " if self.distinct else ""

        expr_sqls = []
        for expr in self.expressions:
            if isinstance(expr, ASTNode):
                expr_sqls.append(expr.to_sql(dialect))
            else:
                expr_sqls.append(str(expr))

        return f"SELECT {distinct_str}{', '.join(expr_sqls)}"


@dataclass
class FromClause(ASTNode):
    """FROM clause"""
    table: str
    alias: Optional[str] = None

    def to_sql(self, dialect: str = "duckdb") -> str:
        sql = f"FROM {self.table}"
        if self.alias:
            sql += f" {self.alias}"
        return sql


@dataclass
class JoinClause(ASTNode):
    """JOIN clause"""
    join_type: str  # INNER, LEFT, RIGHT, FULL
    table: str
    alias: Optional[str] = None
    on_condition: Optional[BinaryExpr] = None

    def to_sql(self, dialect: str = "duckdb") -> str:
        sql = f"{self.join_type} JOIN {self.table}"

        if self.alias:
            sql += f" {self.alias}"

        if self.on_condition:
            sql += f" ON {self.on_condition.to_sql(dialect)}"

        return sql


@dataclass
class WhereClause(ASTNode):
    """WHERE clause"""
    condition: Union[BinaryExpr, List[BinaryExpr]]

    def to_sql(self, dialect: str = "duckdb") -> str:
        if isinstance(self.condition, list):
            # Multiple conditions - AND them together
            conditions = [c.to_sql(dialect) for c in self.condition]
            condition_sql = " AND ".join(conditions)
        else:
            condition_sql = self.condition.to_sql(dialect)

        return f"WHERE {condition_sql}"


@dataclass
class GroupByClause(ASTNode):
    """GROUP BY clause"""
    columns: List[Union[ColumnRef, str]]

    def to_sql(self, dialect: str = "duckdb") -> str:
        col_sqls = []
        for col in self.columns:
            if isinstance(col, ColumnRef):
                col_sqls.append(col.to_sql(dialect))
            else:
                col_sqls.append(str(col))

        return f"GROUP BY {', '.join(col_sqls)}"


@dataclass
class OrderByClause(ASTNode):
    """ORDER BY clause"""
    columns: List[tuple]  # List of (column, direction) tuples

    def to_sql(self, dialect: str = "duckdb") -> str:
        order_sqls = []
        for col, direction in self.columns:
            if isinstance(col, (ColumnRef, AggregateExpr)):
                col_sql = col.to_sql(dialect)
            else:
                col_sql = str(col)

            order_sqls.append(f"{col_sql} {direction}")

        return f"ORDER BY {', '.join(order_sqls)}"


@dataclass
class LimitClause(ASTNode):
    """LIMIT clause"""
    limit: int
    offset: Optional[int] = None

    def to_sql(self, dialect: str = "duckdb") -> str:
        sql = f"LIMIT {self.limit}"
        if self.offset:
            sql += f" OFFSET {self.offset}"
        return sql


# ============================================================================
# Query Node (Complete Query)
# ============================================================================

@dataclass
class Query(ASTNode):
    """Complete SQL query"""
    select: SelectClause
    from_clause: FromClause
    joins: List[JoinClause] = field(default_factory=list)
    where: Optional[WhereClause] = None
    group_by: Optional[GroupByClause] = None
    having: Optional[WhereClause] = None
    order_by: Optional[OrderByClause] = None
    limit: Optional[LimitClause] = None

    def to_sql(self, dialect: str = "duckdb") -> str:
        """Generate complete SQL query"""
        parts = []

        # SELECT
        parts.append(self.select.to_sql(dialect))

        # FROM
        parts.append(self.from_clause.to_sql(dialect))

        # JOINs
        for join in self.joins:
            parts.append(join.to_sql(dialect))

        # WHERE
        if self.where:
            parts.append(self.where.to_sql(dialect))

        # GROUP BY
        if self.group_by:
            parts.append(self.group_by.to_sql(dialect))

        # HAVING
        if self.having:
            parts.append(self.having.to_sql(dialect))

        # ORDER BY
        if self.order_by:
            parts.append(self.order_by.to_sql(dialect))

        # LIMIT
        if self.limit:
            parts.append(self.limit.to_sql(dialect))

        return "\n".join(parts)

    def validate(self) -> List[str]:
        """Validate complete query structure"""
        errors = []

        # Check for dangerous keywords (SQL injection prevention)
        sql = self.to_sql()
        dangerous_patterns = [
            "DROP ", "DELETE ", "TRUNCATE ", "ALTER ", "CREATE ",
            "GRANT ", "REVOKE ", "--", "/*", "*/"
        ]

        for pattern in dangerous_patterns:
            if pattern in sql.upper():
                # Check if it's in a string literal (safe) or raw SQL (dangerous)
                # For now, just warn
                errors.append(f"Warning: Found potentially dangerous keyword: {pattern}")

        # Validate SELECT has at least one expression
        if not self.select.expressions:
            errors.append("SELECT clause must have at least one expression")

        # Validate FROM is present
        if not self.from_clause:
            errors.append("FROM clause is required")

        # If GROUP BY exists, SELECT should only have grouped columns or aggregates
        # This is a simplified check
        if self.group_by and not self.select.expressions:
            errors.append("GROUP BY requires SELECT expressions")

        return errors


# ============================================================================
# Helper Functions
# ============================================================================

def column(name: str, table: Optional[str] = None, alias: Optional[str] = None) -> ColumnRef:
    """Helper to create column reference"""
    return ColumnRef(column=name, table=table, alias=alias)


def literal(value: Any) -> Literal:
    """Helper to create literal"""
    return Literal(value=value)


def aggregate(func: str, expr: Union[ColumnRef, str], alias: Optional[str] = None) -> AggregateExpr:
    """Helper to create aggregate"""
    return AggregateExpr(function=func, expression=expr, alias=alias)


def equals(left: Union[ColumnRef, str], right: Union[Literal, Any]) -> BinaryExpr:
    """Helper to create equals condition"""
    if not isinstance(left, ColumnRef):
        left = ColumnRef(column=str(left))
    if not isinstance(right, Literal):
        right = Literal(value=right)
    return BinaryExpr(left=left, operator="=", right=right)


def in_list(column_ref: Union[ColumnRef, str], values: List[Any]) -> BinaryExpr:
    """Helper to create IN condition"""
    if not isinstance(column_ref, ColumnRef):
        column_ref = ColumnRef(column=str(column_ref))

    literals = [Literal(value=v) for v in values]
    return BinaryExpr(left=column_ref, operator="IN", right=literals)
