/**
 * Development environment configuration
 * Used when running `ng serve` (default)
 */
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8080/api',

  // Service ports (for reference/documentation)
  ports: {
    mockIdp: 9400,
    ticketingMcp: 9000,
    organizationsMcp: 9001,
    fastApi: 8080,
    angularUi: 4200
  }
};