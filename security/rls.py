"""
Row-Level Security (RLS) implementation
Applies user-context based filters to queries
"""
from dataclasses import dataclass
from typing import List
from semantic_layer.schemas import SemanticQuery, Filter


@dataclass
class UserContext:
    """User security context"""
    user_id: str
    role: str  # 'SO', 'ASM', 'ZSM', 'NSM', 'sales_rep', 'manager', 'executive', 'admin'
    territories: List[str] = None  # Territory codes
    regions: List[str] = None  # Region/Zone codes
    states: List[str] = None  # State names
    data_access_level: str = "territory"  # territory, region, state, national
    sales_hierarchy_level: str = None  # 'SO', 'ASM', 'ZSM', 'NSM', or None
    so_codes: List[str] = None  # Sales Officer codes
    asm_codes: List[str] = None  # Area Sales Manager codes
    zsm_codes: List[str] = None  # Zonal Sales Manager codes
    nsm_codes: List[str] = None  # National Sales Manager codes

    def __post_init__(self):
        if self.territories is None:
            self.territories = []
        if self.regions is None:
            self.regions = []
        if self.states is None:
            self.states = []
        if self.so_codes is None:
            self.so_codes = []
        if self.asm_codes is None:
            self.asm_codes = []
        if self.zsm_codes is None:
            self.zsm_codes = []
        if self.nsm_codes is None:
            self.nsm_codes = []


class RowLevelSecurity:
    """Apply row-level security filters based on user context"""

    @staticmethod
    def apply_security(
        semantic_query: SemanticQuery,
        user: UserContext
    ) -> SemanticQuery:
        """
        Inject security filters into query based on user context.

        Args:
            semantic_query: Original query
            user: User security context

        Returns:
            SemanticQuery with security filters applied
        """
        # Admins and executives with national access see everything
        if user.data_access_level == "national" or user.role == "admin":
            return semantic_query

        # Clone query to avoid mutating original
        from copy import deepcopy
        secured_query = deepcopy(semantic_query)

        # PRIORITY 1: Sales Hierarchy Filtering (takes precedence over geography)
        if user.sales_hierarchy_level:
            if user.sales_hierarchy_level == "SO" and user.so_codes:
                # Sales Officer - most restrictive
                so_filter = Filter(
                    dimension="so_code",
                    operator="IN",
                    values=user.so_codes
                )
                secured_query.filters.append(so_filter)
                return secured_query

            elif user.sales_hierarchy_level == "ASM" and user.asm_codes:
                # Area Sales Manager
                asm_filter = Filter(
                    dimension="asm_code",
                    operator="IN",
                    values=user.asm_codes
                )
                secured_query.filters.append(asm_filter)
                return secured_query

            elif user.sales_hierarchy_level == "ZSM" and user.zsm_codes:
                # Zonal Sales Manager
                zsm_filter = Filter(
                    dimension="zsm_code",
                    operator="IN",
                    values=user.zsm_codes
                )
                secured_query.filters.append(zsm_filter)
                return secured_query

            elif user.sales_hierarchy_level == "NSM" and user.nsm_codes:
                # National Sales Manager - see specific NSM data
                nsm_filter = Filter(
                    dimension="nsm_code",
                    operator="IN",
                    values=user.nsm_codes
                )
                secured_query.filters.append(nsm_filter)
                return secured_query

        # PRIORITY 2: Geographic Filtering (if no sales hierarchy)
        if user.data_access_level == "state" and user.states:
            # State-level access
            state_filter = Filter(
                dimension="state_name",
                operator="IN",
                values=user.states
            )
            secured_query.filters.append(state_filter)

        elif user.data_access_level == "region" and user.regions:
            # Region/zone-level access
            region_filter = Filter(
                dimension="zone_name",
                operator="IN",
                values=user.regions
            )
            secured_query.filters.append(region_filter)

        elif user.data_access_level == "territory" and user.territories:
            # Territory-level access (most restrictive)
            # Map territories to geography filters
            # This is simplified - in production, you'd have territory mapping
            territory_filter = Filter(
                dimension="district_name",
                operator="IN",
                values=user.territories
            )
            secured_query.filters.append(territory_filter)

        return secured_query

    @staticmethod
    def get_user_context_from_role(user_id: str, role: str) -> UserContext:
        """
        Helper to create UserContext from role.
        In production, this would query a user database.

        Args:
            user_id: User ID
            role: User role

        Returns:
            UserContext with appropriate access levels
        """
        # Sales Hierarchy Roles
        if role == "NSM":
            return UserContext(
                user_id=user_id,
                role=role,
                data_access_level="national",
                sales_hierarchy_level="NSM",
                nsm_codes=["NSM01"]  # Example
            )
        elif role == "ZSM":
            return UserContext(
                user_id=user_id,
                role=role,
                data_access_level="region",
                sales_hierarchy_level="ZSM",
                zsm_codes=["ZSM01"]  # Example
            )
        elif role == "ASM":
            return UserContext(
                user_id=user_id,
                role=role,
                data_access_level="region",
                sales_hierarchy_level="ASM",
                asm_codes=["ZSM01_ASM1"]  # Example
            )
        elif role == "SO":
            return UserContext(
                user_id=user_id,
                role=role,
                data_access_level="territory",
                sales_hierarchy_level="SO",
                so_codes=["ZSM01_ASM1_SO01"]  # Example
            )
        # Legacy Geographic Roles
        elif role == "executive" or role == "admin":
            return UserContext(
                user_id=user_id,
                role=role,
                data_access_level="national"
            )
        elif role == "manager":
            # Managers typically have region-level access
            return UserContext(
                user_id=user_id,
                role=role,
                data_access_level="region",
                regions=["North", "South"]  # Example
            )
        elif role == "sales_rep":
            # Sales reps have territory-level access
            return UserContext(
                user_id=user_id,
                role=role,
                data_access_level="territory",
                territories=["NORTH_01", "NORTH_02"]  # Example
            )
        else:
            # Default: no access
            return UserContext(
                user_id=user_id,
                role=role,
                data_access_level="territory",
                territories=[]
            )
