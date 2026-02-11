// Cube configuration options: https://cube.dev/docs/config
/** @type{ import('@cubejs-backend/server-core').CreateOptions } */
module.exports = {
  // Multi-tenancy: map client to separate app instance
  contextToAppId: ({ securityContext }) => {
    const clientId = securityContext.clientId || 'default';
    return `CUBEJS_APP_${clientId}`;
  },

  // Security context for row-level security
  queryRewrite: (query, { securityContext }) => {
    if (!securityContext) {
      throw new Error('No security context provided');
    }

    // Apply row-level security filters based on user role and territory
    const { role, territories, regions, states } = securityContext;

    // Admin and executives see all data
    if (role === 'admin' || role === 'executive') {
      return query;
    }

    // Apply territorial filters for sales reps and managers
    if (role === 'manager' && regions && regions.length > 0) {
      query.filters = query.filters || [];
      query.filters.push({
        member: 'Accounts.region',
        operator: 'equals',
        values: regions
      });
    } else if (role === 'sales_rep' && states && states.length > 0) {
      query.filters = query.filters || [];
      query.filters.push({
        member: 'Customers.state',
        operator: 'equals',
        values: states
      });
    }

    return query;
  },

  // Scheduled refresh contexts for pre-aggregations
  scheduledRefreshContexts: () => {
    return [
      { securityContext: { clientId: 'default', role: 'admin' } },
      { securityContext: { clientId: 'itc', role: 'admin' } },
      { securityContext: { clientId: 'nestle', role: 'admin' } },
      { securityContext: { clientId: 'unilever', role: 'admin' } }
    ];
  },

  // Extract security context from request
  checkAuth: (req, auth) => {
    // In production, validate JWT token or API key here
    // For now, accept the provided context
    if (!auth) {
      throw new Error('Authorization required');
    }
  },

  // Context to orchestrator
  contextToOrchestratorId: ({ securityContext }) => {
    return securityContext.clientId || 'default';
  }
};
