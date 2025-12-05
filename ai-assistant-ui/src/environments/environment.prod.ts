/**
 * Production environment configuration
 * Used when building for production (`ng build`)
 */
export const environment = {
  production: true,
  apiUrl: '/api',  // Use relative path in production (assume same domain)

  // Service ports (for reference/documentation)
  ports: {
    mockIdp: 9400,
    ticketingMcp: 9000,
    organizationsMcp: 9001,
    fastApi: 8080,
    angularUi: 4200
  }
};